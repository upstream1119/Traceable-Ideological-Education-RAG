"""四学段在线验收；默认仅离线预检，--execute 才允许调用Qwen。"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GRADES = ("primary", "junior_high", "senior_high", "university")


def build_cases():
    spec = json.loads((ROOT / "tests/v1_acceptance_cases.json").read_text(encoding="utf-8"))
    indexed = {case["id"]: case for case in spec["cases"]}
    cases = []
    for source_id in ("v1qa_004", "v1qa_003"):
        for grade in GRADES:
            cases.append({"id": f"{source_id}_{grade}", "query": indexed[source_id]["query"],
                          "target_grade": grade, "review_focus": "事实、引用及四学段表达差异"})
    for source_id, grade in (("v1qa_022", "senior_high"), ("v1qa_001", "senior_high")):
        cases.append({"id": source_id, "query": indexed[source_id]["query"],
                      "target_grade": grade, "review_focus": (
                          "招生全部事实及v4_008/PDF303" if source_id == "v1qa_022"
                          else "166→167/PDF130；背景证据不足仍需复核，不要求强行approved")})
    return cases


@contextmanager
def runtime_mode():
    # 密钥和模型名继续由Provider读取，绝不批量导入或输出私有env。
    settings = {"DACHUANG_RETRIEVE_MODE": "local", "DACHUANG_GENERATOR_MODE": "llm",
                "DACHUANG_LLM_PROVIDER": "qwen", "DACHUANG_VECTOR_BACKEND": "",
                "DACHUANG_AUDIT_ENABLED": "1"}
    previous = {key: os.environ.get(key) for key in settings}
    os.environ.update(settings)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def save_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def run(output, execute=False, max_calls=20, case_ids=None):
    from src.api.main import RetrieveRequest, retrieve
    from src.generator import evidence_generator, llm_provider
    from src.utils import runtime_audit

    cases = build_cases()
    if case_ids is not None:
        if not case_ids or len(case_ids) != len(set(case_ids)) or set(case_ids) - {c["id"] for c in cases}:
            raise ValueError("复测题目ID为空、重复或不属于本轮题集")
        cases = [case for case in cases if case["id"] in case_ids]
    model = (os.getenv("DACHUANG_QWEN_MODEL", "").strip()
             or llm_provider._read_local_env_value("DACHUANG_QWEN_MODEL")
             or llm_provider.DEFAULT_QWEN_MODEL)
    has_key = bool(os.getenv("DASHSCOPE_API_KEY", "").strip()
                   or llm_provider._read_local_env_value("DASHSCOPE_API_KEY"))
    if execute and not has_key:
        raise ValueError("缺少DASHSCOPE_API_KEY；尚未发出请求")
    head = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    source_digest = hashlib.sha256()
    for path in sorted([*ROOT.glob("src/**/*.py"), Path(__file__)]):
        source_digest.update(path.relative_to(ROOT).as_posix().encode())
        source_digest.update(b"\0")
        source_digest.update(path.read_bytes())
    plan = {"mode": "live_qwen" if execute else "offline_preflight", "git_head": head,
            "working_sources_sha256": source_digest.hexdigest(),
            "model": model, "api_key_configured": has_key,
            "provider": "qwen", "retrieval": "local_rule_and_graph_no_embedding",
            "case_count": len(cases), "planned_max_calls": 2 * len(cases),
            "approved_call_limit_argument": max_calls if execute else None,
            "max_output_tokens_per_call": 1200, "timeout_seconds_per_call": 18,
            "automatic_retries": 0, "seed": None,
            "seed_note": "在线生成temperature=0.2；未指定seed，不声称确定性复现",
            "money_cap": "未提供金额硬限额；调用次数限制不等于金额限制",
            "corpus_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted((ROOT / "data/processed").glob("text_chunks_sizheng_v*.jsonl"))},
            "cases": cases, "human_content_acceptance": "pending"}
    save_json(output / "plan.json", plan)
    calls = []
    results = []
    factory = llm_provider.get_llm_provider
    current_case = None
    fatal_statuses = {"provider_auth_error", "provider_access_denied", "provider_rate_limit",
                      "provider_model_unavailable", "provider_invalid_request",
                      "provider_connection_error", "provider_timeout", "provider_http_error", "provider_error"}

    def counted_provider(name):
        provider = factory(name)
        original = provider.generate

        def generate(prompt):
            if execute and len(calls) >= max_calls:
                raise RuntimeError("已达到本轮模型调用上限，停止后续调用")
            started = time.perf_counter()
            call = {"case_id": current_case, "index": len(calls) + 1,
                    "external_request_attempted": execute, "prompt": prompt,
                    "system_prompt": provider.system_prompt, "status": "started"}
            calls.append(call)
            # 先落盘开始记录；网络异常或进程中断也保留已尝试调用的记录。
            with (output / "calls.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(call, ensure_ascii=False) + "\n")
            response = (original(prompt) if execute else llm_provider.LLMGenerationResult(
                text="", provider_name="qwen", status="offline_preflight_no_external_call"))
            call.update(status=response.status, raw_text=response.text,
                        elapsed_seconds=round(time.perf_counter() - started, 3))
            save_json(output / f"call-{call['index']:02d}.json", call)
            return response

        provider.generate = generate
        return provider

    with runtime_mode(), patch.object(evidence_generator, "get_llm_provider", counted_provider), \
            patch.object(runtime_audit, "AUDIT_ROOT", output / "audit"):
        for case in cases:
            current_case = case["id"]
            started = time.perf_counter()
            response = retrieve(RetrieveRequest(query=case["query"], target_grade=case["target_grade"]))
            result = {"case": case, "response": response,
                      "elapsed_seconds": round(time.perf_counter() - started, 3),
                      "human_content_review": "pending", "original_pdf_review": "pending"}
            save_json(output / (case["id"] + ".json"), result)
            results.append(result)
            case_calls = [call for call in calls if call["case_id"] == current_case]
            if execute and any(call["status"] in fatal_statuses for call in case_calls):
                break
    summary = {"mode": plan["mode"], "completed_cases": len(results),
               "planned_cases": len(cases), "external_request_attempts": len(calls) if execute else 0,
               "offline_prompt_captures": 0 if execute else len(calls),
               "online_generated_without_fallback": sum(
                   r["response"].get("used_fallback") is False for r in results) if execute else 0,
               "human_content_acceptance": "pending", "original_pdf_acceptance": "pending",
               "stopped_early": len(results) < len(cases)}
    save_json(output / "summary.json", summary)
    lines = ["# 四学段验收待审表", "", "默认预检结果是证据摘要，不是在线模型效果。approved不等于内容已验收。", "",
             "|题目|学段|Provider状态|回退|门控|人工内容/原PDF|", "|---|---|---|---|---|---|"]
    for result in results:
        case, response = result["case"], result["response"]
        lines.append(f"|{case['id']}|{case['target_grade']}|{response.get('provider_status')}|"
                     f"{response.get('used_fallback')}|{response['final_decision']['status']}|待审/待审|")
    (output / "review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="仅在已获付费调用批准后使用")
    parser.add_argument("--max-calls", type=int, default=20, help="在线模式的调用上限，1至20")
    parser.add_argument("--case-ids", nargs="+", choices=[c["id"] for c in build_cases()],
                        help="仅运行指定题目，复测不重复整批付费调用")
    args = parser.parse_args()
    if not 1 <= args.max_calls <= 20:
        parser.error("--max-calls必须在1至20之间")
    output = ROOT / "outputs/live_grade_acceptance" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    try:
        summary = run(output, args.execute, args.max_calls, args.case_ids)
    except Exception as exc:
        # 不回显SDK异常正文，避免认证或请求信息外泄。
        save_json(output / "interrupted.json", {"error_type": type(exc).__name__, "partial_results_preserved": True})
        print(f"运行停止：{type(exc).__name__}；已保存材料：{output}")
        return 1
    print(json.dumps({"output": str(output), **summary}, ensure_ascii=False))
    return int(summary["stopped_early"])


if __name__ == "__main__":
    raise SystemExit(main())
