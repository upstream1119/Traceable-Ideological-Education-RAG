import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOCAL_ENV_PATH = REPO_ROOT / ".env.local"
DEFAULT_QUERY_PATH = REPO_ROOT / "tests" / "demo_queries_sizheng_history.json"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "api_experiments"
DEFAULT_PROVIDERS = ("zhipu", "deepseek", "qwen")
TOO_SHORT_ANSWER_LENGTH = 50


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


def _load_queries(path: Path, limit: int) -> list[dict]:
    items = json.loads(path.read_text(encoding="utf-8"))
    queries = [
        {
            "id": item.get("id") or f"query_{index:03d}",
            "query": item["query"],
        }
        for index, item in enumerate(items, start=1)
    ]
    if limit <= 0:
        return queries
    return queries[:limit]


def _set_provider_env(provider: str) -> None:
    os.environ["DACHUANG_LLM_PROVIDER"] = provider
    if provider == "zhipu":
        os.environ.setdefault("DACHUANG_LLM_MODEL", "glm-4.5-air")
    elif provider == "deepseek":
        os.environ.setdefault("DACHUANG_DEEPSEEK_MODEL", "deepseek-v4-flash")
    elif provider == "qwen":
        os.environ.setdefault("DACHUANG_QWEN_MODEL", "qwen-plus")


def _build_direct_prompt(query: str) -> str:
    return (
        "请回答下面这个关于《中国共产党思想政治教育史》的问题。\n"
        "要求：直接给出自然语言回答；如果无法确认出处，请明确说明"
        "“出处无法确认”；不要编造具体页码。\n\n"
        f"问题：{query}"
    )


def _compact_direct_result(provider: str, query_item: dict, provider_result) -> dict:
    text = provider_result.text or ""
    return {
        "run_type": "direct_baseline",
        "provider": provider,
        "query_id": query_item.get("id"),
        "query": query_item["query"],
        "provider_status": provider_result.status,
        "used_fallback": None,
        "answer": text,
        "answer_length": len(text),
        "citation_count": 0,
        "source_status": "not_applicable_no_retrieval",
        "policy_status": "not_checked",
        "final_decision": "not_applicable",
        "citations_used": [],
    }


def _run_direct_baseline(provider: str, query_item: dict) -> dict:
    from src.generator.llm_provider import get_llm_provider

    _set_provider_env(provider)
    provider_result = get_llm_provider(provider).generate(
        _build_direct_prompt(query_item["query"])
    )
    return _compact_direct_result(provider, query_item, provider_result)


def _compact_kg_rag_result(provider: str, query_item: dict, response: dict) -> dict:
    citations_used = response.get("citations_used") or []
    source_check = response.get("source_check") or {}
    policy_check = response.get("policy_check") or {}
    final_decision = response.get("final_decision") or {}
    answer = response.get("answer") or ""
    return {
        "run_type": "kg_rag",
        "provider": provider,
        "query_id": query_item.get("id"),
        "query": query_item["query"],
        "provider_status": response.get("provider_status"),
        "used_fallback": response.get("used_fallback"),
        "answer": answer,
        "answer_length": len(answer),
        "citation_count": len(citations_used),
        "source_status": source_check.get("status"),
        "policy_status": policy_check.get("status"),
        "final_decision": final_decision.get("status"),
        "citations_used": citations_used,
    }


def _run_kg_rag(provider: str, query_item: dict) -> dict:
    from src.retriever.hybrid_retriever import retrieve

    _set_provider_env(provider)
    response = retrieve(query_item["query"])
    return _compact_kg_rag_result(provider, query_item, response)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _summarize_group(rows: list[dict], provider: str, run_type: str) -> dict:
    group = [
        row
        for row in rows
        if row["provider"] == provider and row["run_type"] == run_type
    ]
    return {
        "provider": provider,
        "run_type": run_type,
        "count": len(group),
        "success": sum(row.get("provider_status") == "success" for row in group),
        "no_fallback": sum(row.get("used_fallback") is False for row in group),
        "source_pass": sum(row.get("source_status") == "pass" for row in group),
        "policy_pass": sum(row.get("policy_status") == "pass" for row in group),
        "approved": sum(row.get("final_decision") == "approved" for row in group),
        "needs_review": sum(
            row.get("final_decision") == "needs_review" for row in group
        ),
        "answer_too_short": sum(
            row.get("answer_length", 0) < TOO_SHORT_ANSWER_LENGTH
            for row in group
        ),
        "citation_counts": [row.get("citation_count", 0) for row in group],
        "answer_lengths": [row.get("answer_length", 0) for row in group],
    }


def _write_summary(path: Path, rows: list[dict], providers: list[str]) -> None:
    lines = [
        "# 10题小规模 Provider Baseline 对比结果",
        "",
        f"- 运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 检索模式：mock",
        "- 生成模式：llm",
        f"- Provider：{', '.join(providers)}",
        "- 说明：本轮是小规模探索性对比，不代表正式实验结论。",
        "",
        "## 1. 汇总表",
        "",
        "| provider | run_type | count | success | no fallback | source pass | policy pass | approved | needs review | too short | citation数 | 回答长度 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for provider in providers:
        for run_type in ("direct_baseline", "kg_rag"):
            summary = _summarize_group(rows, provider, run_type)
            lines.append(
                "| {provider} | {run_type} | {count} | {success} | "
                "{no_fallback} | {source_pass} | {policy_pass} | {approved} | "
                "{needs_review} | {answer_too_short} | {citation_counts} | "
                "{answer_lengths} |".format(
                    provider=summary["provider"],
                    run_type=summary["run_type"],
                    count=summary["count"],
                    success=summary["success"],
                    no_fallback=summary["no_fallback"],
                    source_pass=summary["source_pass"],
                    policy_pass=summary["policy_pass"],
                    approved=summary["approved"],
                    needs_review=summary["needs_review"],
                    answer_too_short=summary["answer_too_short"],
                    citation_counts=" / ".join(
                        str(item) for item in summary["citation_counts"]
                    ),
                    answer_lengths=" / ".join(
                        str(item) for item in summary["answer_lengths"]
                    ),
                )
            )

    lines.extend(
        [
            "",
            "## 2. 解释边界",
            "",
            "- `direct_baseline` 不提供检索证据，因此 `source_status` 记为 `not_applicable_no_retrieval`。",
            "- `kg_rag` 走现有 `/retrieve` 等价链路，会记录 citation、溯源检查、政治红线初筛和最终决策。",
            "- 本轮只记录机器输出与链路状态，尚未包含人工质量评价。",
            "",
            "## 3. 下一步",
            "",
            "1. 人工抽查 direct_baseline 与 kg_rag 的回答差异。",
            "2. 增加人工评价字段：事实准确性、citation 支撑、语境漂移、政治表述稳妥性。",
            "3. 等 100-200 条 chunks 稳定后，再进入正式消融实验。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_outputs(output_dir: Path, rows: list[dict], providers: list[str]) -> tuple[Path, Path]:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / f"baseline_results_{run_id}.jsonl"
    summary_path = output_dir / f"baseline_summary_{run_id}.md"
    _write_jsonl(results_path, rows)
    _write_summary(summary_path, rows, providers)
    return results_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--providers", default=",".join(DEFAULT_PROVIDERS))
    args = parser.parse_args()

    _load_local_env()
    os.environ.setdefault("DACHUANG_RETRIEVE_MODE", "mock")
    os.environ.setdefault("DACHUANG_LOCAL_MOCK_ACK", "1")
    os.environ.setdefault("DACHUANG_GENERATOR_MODE", "llm")

    queries = _load_queries(DEFAULT_QUERY_PATH, args.limit)
    providers = [item.strip() for item in args.providers.split(",") if item.strip()]

    rows = []
    for provider in providers:
        for query_item in queries:
            print(
                f"[{provider}] direct_baseline {query_item['id']} "
                f"{query_item['query']}",
                flush=True,
            )
            rows.append(_run_direct_baseline(provider, query_item))
            print(
                f"[{provider}] kg_rag {query_item['id']} {query_item['query']}",
                flush=True,
            )
            rows.append(_run_kg_rag(provider, query_item))

    output_dir = DEFAULT_OUTPUT_ROOT / "2026-06-baseline"
    results_path, summary_path = _write_outputs(output_dir, rows, providers)
    print(f"RESULTS={results_path}")
    print(f"SUMMARY={summary_path}")


if __name__ == "__main__":
    main()
