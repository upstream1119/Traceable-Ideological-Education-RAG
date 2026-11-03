"""智证思政本地规则/template启动器；复用已有环境，不安装依赖或覆盖私有配置。"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
SERVICE = "zhizheng-sizheng"


def port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        try:
            listener.bind(("127.0.0.1", port))
        except OSError as exc:
            raise RuntimeError(f"127.0.0.1:{port}已被占用或不可绑定；请换端口，不要关闭未知进程。") from exc


def read_health(url):
    # 本地检查不走系统HTTP代理。
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=2) as response:
        data = json.load(response)
    if data.get("status") != "ok" or data.get("service") != SERVICE:
        raise ValueError("健康响应不是本项目API")
    return data


def wait_healthy(url, process, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"服务进程提前退出，退出码{process.returncode}；请查看本轮日志。")
        try:
            return read_health(url)
        except (OSError, ValueError, urllib.error.URLError):
            time.sleep(.2)
    raise RuntimeError(f"健康检查超时：{url}；请查看本轮日志。")


def stop_owned(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        # 仅停止本启动器刚创建且仍存活的PID及其子进程，不枚举/终止其他服务。
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW, check=False)
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def check_environment(api_port, web_port):
    if api_port == web_port or any(not 1 <= p <= 65535 for p in (api_port, web_port)):
        raise RuntimeError("前后端端口必须不同，且处于1—65535。")
    missing = [name for name in ("fastapi", "uvicorn", "pydantic", "numpy", "faiss", "openai")
               if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError("当前Python环境缺少：" + "、".join(missing) + "；请切换已有环境，安装须另行批准。")
    node = shutil.which("node")
    if not node or not (WEB / "node_modules/vite/bin/vite.js").is_file():
        raise RuntimeError("未找到Node或web现有Vite依赖；不会自动安装，请检查环境。")
    required = [ROOT / f"data/processed/text_chunks_sizheng_v{i}.jsonl" for i in range(1, 6)]
    required += [ROOT / "data/graph/force_graph.json", ROOT / "data/processed/routed_timeline_manifest.json",
                 WEB / "public/images/xiaohongjun.png"]
    if any(not p.is_file() for p in required):
        raise RuntimeError("运行数据或形象文件不完整；请核对当前代码与资产版本。")
    port_available(api_port); port_available(web_port)
    return node


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-port", type=int, default=5179)
    parser.add_argument("--online", action="store_true", help="每次提交优先通过通义千问生成回答")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--duration-seconds", type=float, default=0,
                        help="验收时定时退出；默认0表示运行至Ctrl+C")
    args = parser.parse_args()
    mode = "local/llm" if args.online else "local/template"
    children, streams = [], []
    run_dir = None
    try:
        if not 0 <= args.duration_seconds <= 86400:
            raise RuntimeError("运行时长须为0—86400秒，0表示持续运行。")
        node = check_environment(args.api_port, args.web_port)
        api_url, web_url = f"http://127.0.0.1:{args.api_port}", f"http://127.0.0.1:{args.web_port}"
        if args.check_only:
            print(json.dumps({"ok": True, "python": sys.executable, "node": node,
                              "api_url": api_url, "web_url": web_url, "mode": mode}, ensure_ascii=False))
            return 0
        run_dir = ROOT / "outputs/local_runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir.mkdir(parents=True, exist_ok=False)
        env = dict(os.environ)
        env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1",
                    "DACHUANG_RETRIEVE_MODE": "local", "DACHUANG_GENERATOR_MODE": "llm" if args.online else "template",
                    "DACHUANG_LLM_PROVIDER": "qwen" if args.online else "stub",
                    "DACHUANG_VECTOR_BACKEND": "", "DACHUANG_AUDIT_ENABLED": "0",
                    "VITE_RETRIEVE_MODE": "api", "VITE_API_BASE_URL": "/api",
                    "DACHUANG_API_PROXY_TARGET": api_url})
        for script in ("sync-display-assets.mjs", "verify-display-assets.mjs"):
            with (run_dir / (script + ".log")).open("x", encoding="utf-8") as output:
                result = subprocess.run([node, str(WEB / "scripts" / script)], cwd=WEB, env=env,
                                        stdout=output, stderr=subprocess.STDOUT, check=False)
            if result.returncode:
                raise RuntimeError("展示资产同步或校验失败，请查看日志；未启动服务。")
        commands = [
            ([sys.executable, "-B", "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", str(args.api_port)], ROOT, "backend.log"),
            ([node, str(WEB / "node_modules/vite/bin/vite.js"), "--host", "127.0.0.1", "--port", str(args.web_port), "--strictPort"], WEB, "frontend.log"),
        ]
        runtime = {"profile": mode, "python": sys.executable, "node": node,
                   "api_url": api_url, "web_url": web_url,
                   "configuration": {key: env[key] for key in (
                       "DACHUANG_RETRIEVE_MODE", "DACHUANG_GENERATOR_MODE", "DACHUANG_VECTOR_BACKEND",
                       "DACHUANG_AUDIT_ENABLED", "VITE_RETRIEVE_MODE", "VITE_API_BASE_URL", "DACHUANG_API_PROXY_TARGET")},
                   "private_env_files_modified": False}
        for command, cwd, log_name in commands:
            stream = (run_dir / log_name).open("x", encoding="utf-8")
            streams.append(stream)
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            children.append(process)
        runtime["owned_pids"] = [p.pid for p in children]
        with (run_dir / "runtime.json").open("x", encoding="utf-8") as stream:
            json.dump(runtime, stream, ensure_ascii=False, indent=2)
        wait_healthy(api_url + "/health", children[0])
        wait_healthy(web_url + "/api/health", children[1])
        print(json.dumps({"ready": True, "web_url": web_url, "health": api_url + "/health",
                          "proxy_health": web_url + "/api/health", "logs": str(run_dir),
                          "mode": mode, "stop": "Ctrl+C"}, ensure_ascii=False), flush=True)
        deadline = time.monotonic() + args.duration_seconds if args.duration_seconds else None
        while deadline is None or time.monotonic() < deadline:
            if any(p.poll() is not None for p in children):
                raise RuntimeError("服务意外退出，正在清理本启动器的其他进程；请查看日志。")
            time.sleep(.2)
        return 0
    except KeyboardInterrupt:
        print("正在停止本次启动的服务。", flush=True)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc), "logs": str(run_dir) if run_dir else None},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        for process in reversed(children):
            stop_owned(process)
        for stream in streams:
            stream.close()


if __name__ == "__main__":
    raise SystemExit(main())
