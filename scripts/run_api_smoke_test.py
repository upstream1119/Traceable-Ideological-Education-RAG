import json
import os
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOCAL_ENV_PATH = REPO_ROOT / ".env.local"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "api_experiments"

SMOKE_QUERIES = [
    "马克思主义最初在中国如何传入？",
    "张闻天起草的宣传鼓动工作提纲强调了什么？",
    "长征中红军如何通过政治动员鼓舞士气？",
]


def _load_local_env() -> None:
    if not LOCAL_ENV_PATH.exists():
        return

    for line in LOCAL_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.lstrip("\ufeff").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _prepare_runtime_env() -> None:
    _load_local_env()
    os.environ.setdefault("DACHUANG_RETRIEVE_MODE", "mock")
    os.environ.setdefault("DACHUANG_LOCAL_MOCK_ACK", "1")
    os.environ.setdefault("DACHUANG_GENERATOR_MODE", "llm")
    os.environ.setdefault("DACHUANG_LLM_PROVIDER", "zhipu")
    os.environ.setdefault("DACHUANG_LLM_MODEL", "glm-4.5-air")


def _active_model_name() -> str:
    provider = os.getenv("DACHUANG_LLM_PROVIDER", "").strip().lower()
    if provider in {"deepseek", "deepseek-chat", "deepseek-v4-flash"}:
        return os.getenv("DACHUANG_DEEPSEEK_MODEL", "deepseek-v4-flash")
    if provider in {"qwen", "dashscope", "bailian", "qwen-plus"}:
        return os.getenv("DACHUANG_QWEN_MODEL", "qwen-plus")
    return os.getenv("DACHUANG_LLM_MODEL", "")


def _compact_result(index: int, query: str, response: dict) -> dict:
    citations_used = response.get("citations_used") or []
    source_check = response.get("source_check") or {}
    policy_check = response.get("policy_check") or {}
    final_decision = response.get("final_decision") or {}

    return {
        "index": index,
        "query": query,
        "provider_status": response.get("provider_status"),
        "generator_mode": response.get("generator_mode"),
        "generator_provider": response.get("generator_provider"),
        "used_fallback": response.get("used_fallback"),
        "answer": response.get("answer"),
        "answer_length": len(response.get("answer") or ""),
        "citation_count": len(citations_used),
        "citations_used": citations_used,
        "source_check": source_check,
        "policy_check": policy_check,
        "final_decision": final_decision,
        "query_entities": response.get("query_entities") or [],
        "hybrid_hit_ids": [
            hit.get("id")
            for hit in response.get("hybrid_hits", [])
        ],
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_summary(path: Path, rows: list[dict]) -> None:
    lines = [
        "# API 冒烟测试结果",
        "",
        f"- 运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 检索模式：mock",
        f"- 生成模式：{os.getenv('DACHUANG_GENERATOR_MODE', '')}",
        f"- LLM Provider：{os.getenv('DACHUANG_LLM_PROVIDER', '')}",
        f"- LLM Model：{_active_model_name()}",
        "",
        "| 序号 | 问题 | provider_status | fallback | citation数 | source_check | policy_check | final_decision | answer_len |",
        "|---:|---|---|---|---:|---|---|---|---:|",
    ]

    for row in rows:
        lines.append(
            "| {index} | {query} | {provider_status} | {used_fallback} | "
            "{citation_count} | {source_status} | {policy_status} | "
            "{decision_status} | {answer_length} |".format(
                index=row["index"],
                query=row["query"],
                provider_status=row.get("provider_status"),
                used_fallback=row.get("used_fallback"),
                citation_count=row.get("citation_count"),
                source_status=(row.get("source_check") or {}).get("status"),
                policy_status=(row.get("policy_check") or {}).get("status"),
                decision_status=(row.get("final_decision") or {}).get("status"),
                answer_length=row.get("answer_length"),
            )
        )

    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 本测试只用于确认 API 调用链路是否可用，不代表正式实验结论。",
            "- 若 `used_fallback=True`，说明模型回答未被采用或调用失败，系统回退到模板证据摘要。",
            "- 后续正式实验需要扩展问题数量，并加入 DeepSeek / Qwen / KG-RAG 消融对比。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    _prepare_runtime_env()

    from src.retriever.hybrid_retriever import retrieve

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = Path(
        os.getenv("DACHUANG_API_EXPERIMENT_DIR", str(DEFAULT_OUTPUT_ROOT))
    )
    output_dir = output_root / "2026-06-smoke"
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for index, query in enumerate(SMOKE_QUERIES, start=1):
        print(f"[{index}/{len(SMOKE_QUERIES)}] {query}", flush=True)
        response = retrieve(query)
        rows.append(_compact_result(index, query, response))

    results_path = output_dir / f"smoke_results_{run_id}.jsonl"
    summary_path = output_dir / f"smoke_summary_{run_id}.md"
    _write_jsonl(results_path, rows)
    _write_summary(summary_path, rows)

    print(f"RESULTS={results_path}")
    print(f"SUMMARY={summary_path}")


if __name__ == "__main__":
    main()
