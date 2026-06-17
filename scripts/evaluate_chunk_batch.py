import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.validate_jsonl import validate_record


PASS_STATUS = "pass"
WARNING_STATUS = "warning"
FAIL_STATUS = "fail"


def load_jsonl_records(path: Path) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    parse_errors: list[str] = []

    if not path.exists():
        return records, [f"ERROR file not found: {path}"]

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            raw = line.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                parse_errors.append(f"ERROR line {line_no}: invalid JSON -> {exc.msg}")
                continue
            if not isinstance(data, dict):
                parse_errors.append(f"ERROR line {line_no}: each JSONL line must be an object")
                continue
            records.append(data)

    return records, parse_errors


def load_query_cases(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"query file must contain a JSON list: {path}")
    return [item for item in data if isinstance(item, dict)]


def build_search_content(record: dict) -> str:
    citation = record.get("citation", {})
    if not isinstance(citation, dict):
        citation = {}

    fields: list[str] = [
        str(record.get("id", "")),
        str(record.get("source", "")),
        str(record.get("title", "")),
        str(record.get("text", "")),
        str(record.get("topic", "")),
        str(citation.get("doc", "")),
        str(citation.get("section", "")),
    ]

    for list_field in ("entities", "tags"):
        value = record.get(list_field, [])
        if isinstance(value, list):
            fields.append(" ".join(str(item) for item in value))

    return " ".join(field for field in fields if field)


def _keyword_hits(keywords: list[str], content: str) -> list[str]:
    return [keyword for keyword in keywords if keyword and keyword in content]


def _query_terms(query: str) -> list[str]:
    terms: list[str] = []
    for token in query.replace("？", " ").replace("?", " ").split():
        cleaned = token.strip()
        if len(cleaned) >= 2:
            terms.append(cleaned)
    return terms


def score_record_for_query(record: dict, case: dict) -> tuple[int, dict[str, list[str]]]:
    content = build_search_content(record)
    expected_entities = case.get("expected_entities", [])
    expected_keywords = case.get("expected_citation_keywords", [])
    expected_chunk_ids = case.get("expected_chunk_ids", [])
    query_terms = _query_terms(str(case.get("query", "")))

    entity_hits = _keyword_hits(expected_entities if isinstance(expected_entities, list) else [], content)
    keyword_hits = _keyword_hits(expected_keywords if isinstance(expected_keywords, list) else [], content)
    query_hits = _keyword_hits(query_terms, content)

    chunk_id = str(record.get("id", ""))
    expected_id_hits = [chunk_id] if chunk_id in expected_chunk_ids else []

    score = 0
    score += len(entity_hits) * 3
    score += len(keyword_hits) * 2
    score += len(query_hits)
    score += len(expected_id_hits) * 5

    return score, {
        "entity_hits": entity_hits,
        "citation_keyword_hits": keyword_hits,
        "query_term_hits": query_hits,
        "expected_chunk_id_hits": expected_id_hits,
    }


def _citation_page_missing(record: dict) -> bool:
    citation = record.get("citation")
    return not isinstance(citation, dict) or citation.get("page") is None


def evaluate_batch(chunk_path: Path, query_path: Path) -> dict:
    records, parse_errors = load_jsonl_records(chunk_path)
    query_cases = load_query_cases(query_path)
    seen_ids: set[str] = set()
    schema_errors: list[str] = []
    schema_warnings: list[str] = []

    for line_no, record in enumerate(records, 1):
        errors, warnings = validate_record(record, line_no, seen_ids)
        schema_errors.extend(errors)
        schema_warnings.extend(warnings)

    query_reports = []
    for case in query_cases:
        scored_items = []
        for record in records:
            score, matches = score_record_for_query(record, case)
            if score <= 0:
                continue
            scored_items.append(
                {
                    "id": record.get("id"),
                    "title": record.get("title"),
                    "citation": record.get("citation"),
                    "score": score,
                    "matches": matches,
                }
            )
        scored_items.sort(key=lambda item: item["score"], reverse=True)

        expected_ids = case.get("expected_chunk_ids", [])
        matched_expected_ids = [
            item["id"]
            for item in scored_items
            if isinstance(expected_ids, list) and item["id"] in expected_ids
        ]
        top_candidates = scored_items[:5]
        query_status = PASS_STATUS if top_candidates else WARNING_STATUS

        query_reports.append(
            {
                "id": case.get("id"),
                "query": case.get("query"),
                "expected_chunk_ids": expected_ids,
                "matched_expected_chunk_ids": matched_expected_ids,
                "top_candidates": top_candidates,
                "status": query_status,
            }
        )

    missing_page_count = sum(1 for record in records if _citation_page_missing(record))
    warning_query_count = sum(1 for item in query_reports if item["status"] == WARNING_STATUS)

    if parse_errors or schema_errors:
        overall_status = FAIL_STATUS
    elif warning_query_count:
        overall_status = WARNING_STATUS
    else:
        overall_status = PASS_STATUS

    return {
        "chunk_file": str(chunk_path),
        "query_file": str(query_path),
        "record_count": len(records),
        "parse_error_count": len(parse_errors),
        "schema_error_count": len(schema_errors),
        "schema_warning_count": len(schema_warnings),
        "missing_page_count": missing_page_count,
        "warning_query_count": warning_query_count,
        "parse_errors": parse_errors,
        "schema_errors": schema_errors,
        "schema_warnings": schema_warnings,
        "query_reports": query_reports,
        "overall_status": overall_status,
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a candidate chunk JSONL batch.")
    parser.add_argument("--chunks", required=True, help="Path to candidate chunk JSONL file.")
    parser.add_argument(
        "--queries",
        default="tests/demo_queries_sizheng_history.json",
        help="Path to demo query acceptance JSON file.",
    )
    parser.add_argument("--output", default="", help="Optional JSON report output path.")
    args = parser.parse_args()

    report = evaluate_batch(Path(args.chunks), Path(args.queries))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)

    if args.output:
        _write_report(Path(args.output), report)

    return 1 if report["overall_status"] == FAIL_STATUS else 0


if __name__ == "__main__":
    raise SystemExit(main())
