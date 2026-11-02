import copy
import json
import os
from pathlib import Path
import tempfile

import pytest

from scripts.run_v1_acceptance import check_case, load_cases, run_cases
from scripts import run_v1_acceptance as acceptance
from src.generator import evidence_generator
from src.retriever import hybrid_retriever
from src.router.display_router import build_display_route


def test_offline_runner_overrides_paid_paths_and_restores_environment(monkeypatch):
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "llm")
    monkeypatch.setenv("DACHUANG_VECTOR_BACKEND", "faiss")
    def forbidden(*args, **kwargs):
        raise AssertionError("离线验收不得调用外部provider")
    monkeypatch.setattr(evidence_generator, "get_llm_provider", forbidden)
    monkeypatch.setattr(hybrid_retriever, "QwenEmbeddingProvider", forbidden)
    report = run_cases(load_cases(), "priority")
    assert report["summary"]["case_count"] == 10
    assert report["summary"]["failed"] == 0
    assert report["paid_calls"] == 0
    assert os.environ["DACHUANG_GENERATOR_MODE"] == "llm"
    assert os.environ["DACHUANG_VECTOR_BACKEND"] == "faiss"


@pytest.fixture(scope="module")
def complete_report():
    return run_cases(load_cases())


def test_forty_cases_cover_real_corpus_and_keep_manual_acceptance_separate(complete_report):
    report = complete_report
    assert report["chunk_count"] == 308
    assert report["summary"]["case_count"] == 40
    assert report["summary"]["failed"] == 0
    assert report["summary"]["fixed_decision_case_count"] == 10
    assert report["summary"]["checks"]["fixed_decision"] == {"passed": 10, "checked": 10}
    assert report["summary"]["human_content_acceptance"] == "pending"
    assert report["summary"]["grade_language_quality"] == "not_tested_template_only"


def test_checker_rejects_wrong_citation_gate_and_metadata_only_fact(complete_report):
    row = next(r for r in complete_report["cases"] if r["case"]["id"] == "v1qa_022")
    corpus = {c["id"]: c for c in hybrid_retriever._load_demo_knowledge_base()}
    bad = copy.deepcopy(row["response"])
    bad["citations_used"][0]["citation"]["page"] = 9999
    bad["final_decision"]["can_output"] = False
    bad["answer"] = "没有回答人数。\n\n引用依据：570万，27.3万"
    result = check_case(row["case"], bad, corpus)
    assert not result["checks"]["citation_integrity"]
    assert not result["checks"]["gate_contract"]
    assert not result["checks"]["answer_anchor_coverage"]
    assert "570万" in result["missing_answer_anchors"]


@pytest.mark.parametrize("query", [
    "党的思想路线有什么含义？",
    "总路线宣传有哪些要求？",
    "政治路线与思想政治教育有什么联系？",
])
def test_non_geographical_line_is_not_a_map_request(query):
    assert build_display_route(query, [])["presentation_mode"] == "evidence_cards"


def test_geographic_route_remains_map_request():
    assert build_display_route("请展示红军行军路线图", [])["presentation_mode"] == "timeline_map"


def test_external_case_file_still_writes_complete_reports(monkeypatch, tmp_path):
    # 使用系统临时目录，不能因pytest的basetemp位于仓库内而漏测边界。
    with tempfile.TemporaryDirectory(prefix="dachuang-v1qa-external-") as folder:
        external_cases = Path(folder) / "cases.json"
        assert acceptance.ROOT not in external_cases.resolve().parents
        external_cases.write_text(json.dumps(load_cases(), ensure_ascii=False), encoding="utf-8")
        output = tmp_path / "reports"
        monkeypatch.setattr("sys.argv", [
            "scripts/run_v1_acceptance.py", "--cases", str(external_cases),
            "--output-root", str(output), "--subset", "demo",
        ])
        assert acceptance.main() == 0
        result_files = list(output.glob("*/results.json"))
        assert len(result_files) == 1
        report = json.loads(result_files[0].read_text(encoding="utf-8"))
        assert report["summary"]["passed"] == 3
        assert result_files[0].with_name("summary.md").is_file()
        assert report["provenance"]["cases_sha256"] == acceptance.sha(external_cases)
