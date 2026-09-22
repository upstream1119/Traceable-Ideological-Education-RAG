import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = REPO_ROOT / "data" / "graph" / "graphsim_regression_cases.json"
REPORT_PATH = REPO_ROOT / "reports" / "graphsim_regression_results.json"


def test_graphsim_regression_has_required_coverage_and_raw_fields():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert len(cases) >= 15
    assert len(report["cases"]) == len(cases)
    assert {case["id"] for case in cases} == {case["id"] for case in report["cases"]}
    assert any(case.get("expect_no_reliable_path") for case in cases)

    required_types = {"person", "event", "organization", "document", "concept"}
    case_text = " ".join(case["id"] for case in cases)
    for required_type in required_types:
        assert required_type in case_text

    for result in report["cases"]:
        assert "query_entities" in result
        assert len(result["top_3_graph_hits"]) <= 3
        for hit in result["top_3_graph_hits"]:
            for path in hit["graph_paths"]:
                assert len(path["edges"]) == path["hops"]
                assert path["source_chunk_ids"]
                assert all(edge["source_chunk_ids"] for edge in path["edges"])


def test_graphsim_regression_metrics_are_complete():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    summary = report["summary"]
    assert summary["case_count"] >= 15
    for metric_name in (
        "entity_hit_rate",
        "graph_hit_recall_at_3",
        "path_hit_rate",
        "edge_evidence_completeness_rate",
    ):
        metric = summary[metric_name]
        assert metric["denominator"] > 0
        assert 0 <= metric["rate"] <= 1
    assert summary["edge_evidence_completeness_rate"]["rate"] == 1.0
