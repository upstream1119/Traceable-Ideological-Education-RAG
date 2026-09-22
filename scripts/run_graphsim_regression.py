"""Run reproducible GraphSim regression cases and write raw + summary outputs."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
DEFAULT_CASES = REPO_ROOT / "data" / "graph" / "graphsim_regression_cases.json"
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "graphsim_regression_results.json"
DEFAULT_SUMMARY = REPO_ROOT / "reports" / "graphsim_regression_summary.md"
RUN_COMMAND = (
    "DACHUANG_RETRIEVE_MODE=mock DACHUANG_LOCAL_MOCK_ACK=1 "
    "python scripts/run_graphsim_regression.py"
)


def _path_matches(path: dict, expected: dict) -> bool:
    return path.get("path") == expected.get("nodes") and path.get("relations") == expected.get("relations")


def _iter_paths(top_three_hits: list[dict]):
    for hit in top_three_hits:
        yield from hit.get("graph_paths", [])


def _edge_evidence_complete(path: dict) -> bool:
    edges = path.get("edges", [])
    if not edges or len(edges) != path.get("hops"):
        return False
    return all(edge.get("source_chunk_ids") for edge in edges)


def _metric(numerator: int, denominator: int) -> dict[str, float | int]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": round(numerator / denominator, 4) if denominator else None,
    }


def run_cases(cases: list[dict[str, Any]]) -> tuple[dict, dict]:
    # Keep the environment explicit so a local run cannot silently use team mode.
    os.environ["DACHUANG_RETRIEVE_MODE"] = "mock"
    os.environ["DACHUANG_LOCAL_MOCK_ACK"] = "1"
    from src.retriever.hybrid_retriever import retrieve

    raw_cases: list[dict] = []
    entity_hits = entity_total = 0
    graph_hits = graph_total = 0
    path_hits = path_total = 0
    edge_complete = edge_total = 0

    for case in cases:
        result = retrieve(case["query"])
        top_three = result.get("graph_hits", [])[:3]
        returned_entities = result.get("query_entities", [])
        expected_entities = case.get("expected_entities", [])
        entity_hits += sum(entity in returned_entities for entity in expected_entities)
        entity_total += len(expected_entities)

        hit_ids = [hit.get("id") for hit in top_three]
        expected_hit_ids = set(case.get("expected_hit_ids", []))
        if expected_hit_ids:
            graph_total += 1
            graph_hits += bool(expected_hit_ids.intersection(hit_ids))

        paths = list(_iter_paths(top_three))
        expected_path = case.get("expected_path")
        if expected_path:
            path_total += 1
            path_hits += any(_path_matches(path, expected_path) for path in paths)
        elif case.get("expect_no_reliable_path"):
            path_total += 1
            path_hits += not paths

        for path in paths:
            edge_total += 1
            edge_complete += _edge_evidence_complete(path)

        raw_cases.append(
            {
                "id": case["id"],
                "query": case["query"],
                "query_entities": returned_entities,
                "top_3_graph_hits": [
                    {
                        "id": hit.get("id"),
                        "graph_score": hit.get("graph_score"),
                        "related_entities": hit.get("related_entities", []),
                        "graph_paths": hit.get("graph_paths", []),
                    }
                    for hit in top_three
                ],
                "expected_entities": expected_entities,
                "expected_hit_ids": sorted(expected_hit_ids),
                "expected_path": expected_path,
                "expect_no_reliable_path": bool(case.get("expect_no_reliable_path")),
            }
        )

    summary = {
        "case_count": len(cases),
        "entity_hit_rate": _metric(entity_hits, entity_total),
        "graph_hit_recall_at_3": _metric(graph_hits, graph_total),
        "path_hit_rate": _metric(path_hits, path_total),
        "edge_evidence_completeness_rate": _metric(edge_complete, edge_total),
        "raw_edge_count": edge_total,
        "run_command": RUN_COMMAND,
    }
    report = {
        "schema_version": "1.0",
        "source": "data/graph/triples_demo.jsonl + formal sizheng chunks",
        "mode": "mock",
        "summary": summary,
        "cases": raw_cases,
    }
    return report, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GraphSim专项回归")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    report, summary = run_cases(cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    summary_text = "# GraphSim 专项回归报告\n\n"
    summary_text += f"- 题目数：{summary['case_count']}\n"
    summary_text += f"- 实体命中率：{summary['entity_hit_rate']['numerator']}/{summary['entity_hit_rate']['denominator']} = {summary['entity_hit_rate']['rate']}\n"
    summary_text += f"- Graph Hit Recall@3：{summary['graph_hit_recall_at_3']['numerator']}/{summary['graph_hit_recall_at_3']['denominator']} = {summary['graph_hit_recall_at_3']['rate']}\n"
    summary_text += f"- 路径命中率：{summary['path_hit_rate']['numerator']}/{summary['path_hit_rate']['denominator']} = {summary['path_hit_rate']['rate']}\n"
    summary_text += f"- 边证据完整率：{summary['edge_evidence_completeness_rate']['numerator']}/{summary['edge_evidence_completeness_rate']['denominator']} = {summary['edge_evidence_completeness_rate']['rate']}\n"
    summary_text += f"\n复跑命令：`{RUN_COMMAND}`\n"
    args.summary.write_text(summary_text, encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
