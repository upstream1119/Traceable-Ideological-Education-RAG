import argparse
import csv
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.retriever.hybrid_retriever import retrieve


LOCAL_ENV_PATH = REPO_ROOT / ".env.local"
DEFAULT_QUERY_PATH = REPO_ROOT / "tests" / "demo_queries_sizheng_history.json"
DEFAULT_INDEX_DIR = (
    REPO_ROOT
    / "outputs"
    / "vector_experiments"
    / "2026-06-faiss-smoke"
    / "20260623_213511"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT
    / "outputs"
    / "retrieve_experiments"
    / "2026-06-backend-comparison"
)
BACKENDS = ("lightweight", "faiss")


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
    queries = [item for item in items if item.get("is_suitable_for_demo", True)]
    if limit <= 0:
        return queries
    return queries[:limit]


@contextmanager
def _patched_env(values: dict[str, str | None]):
    original = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _normalize(value: str) -> str:
    return "".join(str(value or "").split())


def _hit_matches_expected_id(hit: dict | None, expected_ids: list[str]) -> bool:
    return bool(hit and hit.get("id") in set(expected_ids))


def _hits_contain_expected_id(hits: list[dict], expected_ids: list[str]) -> bool:
    expected = set(expected_ids)
    return any(hit.get("id") in expected for hit in hits)


def _hits_contain_expected_section(
    hits: list[dict],
    expected_sections: list[str],
) -> bool:
    normalized_expected = [
        _normalize(section) for section in expected_sections if section
    ]
    if not normalized_expected:
        return False

    for hit in hits:
        citation = hit.get("citation") or {}
        actual = _normalize(citation.get("section", ""))
        if not actual:
            continue
        if any(expected in actual or actual in expected for expected in normalized_expected):
            return True
    return False


def _compact_hit(hit: dict) -> dict:
    citation = hit.get("citation") or {}
    return {
        "id": hit.get("id"),
        "title": hit.get("title"),
        "page": citation.get("page"),
        "section": citation.get("section"),
        "hybrid_score": hit.get("hybrid_score"),
        "vector_score": hit.get("vector_score"),
        "graph_score": hit.get("graph_score"),
    }


def _summarize_result(case: dict, backend: str, result: dict) -> dict:
    hits = result.get("hybrid_hits") or []
    top1 = hits[0] if hits else None
    expected_ids = case.get("expected_chunk_ids") or []
    expected_sections = case.get("expected_citation_sections") or []
    citation = (top1 or {}).get("citation") or {}
    final_decision = result.get("final_decision") or {}

    return {
        "case_id": case.get("id"),
        "query": case.get("query"),
        "backend": backend,
        "top1_id": (top1 or {}).get("id"),
        "top1_title": (top1 or {}).get("title"),
        "top1_page": citation.get("page"),
        "top1_score": (top1 or {}).get("hybrid_score"),
        "top1_expected_id_match": _hit_matches_expected_id(top1, expected_ids),
        "any_expected_id_in_topk": _hits_contain_expected_id(hits, expected_ids),
        "any_expected_section_in_topk": _hits_contain_expected_section(
            hits,
            expected_sections,
        ),
        "hybrid_hit_count": len(hits),
        "citation_count": len(result.get("citations_used") or []),
        "source_check_status": (result.get("source_check") or {}).get("status"),
        "policy_check_status": (result.get("policy_check") or {}).get("status"),
        "final_decision_status": final_decision.get("status"),
        "can_output": final_decision.get("can_output"),
        "review_required": final_decision.get("review_required"),
        "answer_len": len(result.get("answer") or ""),
        "topk": [_compact_hit(hit) for hit in hits],
    }


def _run_backend(case: dict, backend: str, index_dir: Path | None) -> dict:
    env = {
        "DACHUANG_RETRIEVE_MODE": "mock",
        "DACHUANG_LOCAL_MOCK_ACK": "1",
        "DACHUANG_GENERATOR_MODE": "template",
    }
    if backend == "faiss":
        env["DACHUANG_VECTOR_BACKEND"] = "faiss"
        env["DACHUANG_FAISS_INDEX_DIR"] = str(index_dir)
    else:
        env["DACHUANG_VECTOR_BACKEND"] = None
        env["DACHUANG_FAISS_INDEX_DIR"] = None

    with _patched_env(env):
        return retrieve(case["query"])


def _aggregate_backend(rows: list[dict], backend: str) -> dict:
    backend_rows = [row for row in rows if row["backend"] == backend]
    total = len(backend_rows)
    if total == 0:
        return {
            "backend": backend,
            "case_count": 0,
            "top1_id_rate": 0.0,
            "topk_id_rate": 0.0,
            "topk_section_rate": 0.0,
            "avg_citation_count": 0.0,
        }
    return {
        "backend": backend,
        "case_count": total,
        "top1_id_rate": sum(row["top1_expected_id_match"] for row in backend_rows)
        / total,
        "topk_id_rate": sum(row["any_expected_id_in_topk"] for row in backend_rows)
        / total,
        "topk_section_rate": sum(
            row["any_expected_section_in_topk"] for row in backend_rows
        )
        / total,
        "avg_citation_count": sum(row["citation_count"] for row in backend_rows)
        / total,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "case_id",
        "query",
        "backend",
        "top1_id",
        "top1_title",
        "top1_page",
        "top1_score",
        "top1_expected_id_match",
        "any_expected_id_in_topk",
        "any_expected_section_in_topk",
        "hybrid_hit_count",
        "citation_count",
        "source_check_status",
        "policy_check_status",
        "final_decision_status",
        "can_output",
        "review_required",
        "answer_len",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _format_rate(value: float) -> str:
    return f"{value:.4f}"


def _write_summary(path: Path, rows: list[dict], index_dir: Path, output_dir: Path) -> None:
    aggregates = [_aggregate_backend(rows, backend) for backend in BACKENDS]

    lines = [
        "# retrieve 后端对比结果",
        "",
        f"- 运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 检索模式：mock",
        "- 生成模式：template",
        f"- FAISS 索引目录：`{index_dir}`",
        f"- 输出目录：`{output_dir}`",
        "",
        "## 汇总指标",
        "",
        "| backend | 题数 | Top1 ID 命中率 | TopK ID 命中率 | TopK 章节命中率 | 平均 citation 数 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in aggregates:
        lines.append(
            "| {backend} | {case_count} | {top1_id_rate} | {topk_id_rate} | "
            "{topk_section_rate} | {avg_citation_count:.2f} |".format(
                backend=item["backend"],
                case_count=item["case_count"],
                top1_id_rate=_format_rate(item["top1_id_rate"]),
                topk_id_rate=_format_rate(item["topk_id_rate"]),
                topk_section_rate=_format_rate(item["topk_section_rate"]),
                avg_citation_count=item["avg_citation_count"],
            )
        )

    lines.extend(
        [
            "",
            "## 逐题结果",
            "",
            "| 题号 | backend | Top1 | 页码 | Top1 ID 命中 | TopK ID 命中 | TopK 章节命中 | source | policy | decision |",
            "|---|---|---|---:|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| {case_id} | {backend} | {top1_id} / {top1_title} | {top1_page} | "
            "{top1_expected_id_match} | {any_expected_id_in_topk} | "
            "{any_expected_section_in_topk} | {source_check_status} | "
            "{policy_check_status} | {final_decision_status} |".format(
                case_id=row["case_id"],
                backend=row["backend"],
                top1_id=row.get("top1_id") or "",
                top1_title=row.get("top1_title") or "",
                top1_page="" if row.get("top1_page") is None else row.get("top1_page"),
                top1_expected_id_match=row["top1_expected_id_match"],
                any_expected_id_in_topk=row["any_expected_id_in_topk"],
                any_expected_section_in_topk=row["any_expected_section_in_topk"],
                source_check_status=row.get("source_check_status") or "",
                policy_check_status=row.get("policy_check_status") or "",
                final_decision_status=row.get("final_decision_status") or "",
            )
        )

    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 本实验只比较 `/retrieve` 的轻量检索后端与可选 FAISS 后端，不代表论文级正式实验结论。",
            "- `expected_chunk_ids` 仍包含早期 demo chunk ID；FAISS 索引用的是 v1/v2 新 chunk ID，因此应重点参考 `TopK 章节命中率`。",
            "- 脚本强制使用 `DACHUANG_GENERATOR_MODE=template`，不会调用文本生成模型。",
            "- FAISS 组会调用 query embedding，但不会重建索引。",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_outputs(rows: list[dict], output_dir: Path, index_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "backend_comparison_results.jsonl", rows)
    _write_csv(output_dir / "backend_comparison_table.csv", rows)
    _write_summary(
        output_dir / "backend_comparison_summary.md",
        rows,
        index_dir,
        output_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare lightweight retrieve backend with optional FAISS backend."
    )
    parser.add_argument("--query-path", type=Path, default=DEFAULT_QUERY_PATH)
    parser.add_argument("--faiss-index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    _load_local_env()
    cases = _load_queries(args.query_path, args.limit)
    if not cases:
        raise ValueError("no query cases found")
    if not (args.faiss_index_dir / "index.faiss").exists():
        raise FileNotFoundError(f"missing index.faiss: {args.faiss_index_dir}")
    if not (args.faiss_index_dir / "metadata.json").exists():
        raise FileNotFoundError(f"missing metadata.json: {args.faiss_index_dir}")

    rows = []
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['query']}", flush=True)
        for backend in BACKENDS:
            print(f"  - backend={backend}", flush=True)
            result = _run_backend(case, backend, args.faiss_index_dir)
            rows.append(_summarize_result(case, backend, result))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_root / timestamp
    _write_outputs(rows, output_dir, args.faiss_index_dir)
    print(f"OUTPUT_DIR={output_dir}")
    print(f"SUMMARY={output_dir / 'backend_comparison_summary.md'}")


if __name__ == "__main__":
    main()
