import json
import os
from pathlib import Path

from src.generator.template_generator import NO_EVIDENCE_ANSWER
from src.retriever.hybrid_retriever import retrieve
from src.reviewer.policy_checker import NEED_REVIEW_STATUS
from src.reviewer.source_checker import NO_EVIDENCE_STATUS


REQUIRED_HYBRID_FIELDS = {
    "id",
    "source",
    "title",
    "text",
    "citation",
    "vector_score",
    "graph_score",
    "hybrid_score",
}


def _load_demo_queries() -> list[dict]:
    path = Path(__file__).with_name("demo_queries_sizheng_history.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_demo_queries_return_expected_evidence(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    for case in _load_demo_queries():
        result = retrieve(case["query"])

        for entity in case["expected_entities"]:
            assert entity in result["query_entities"], case["id"]

        hybrid_hits = result["hybrid_hits"]
        assert len(hybrid_hits) >= case["min_hybrid_hits"], case["id"]
        assert result["answer"], case["id"]
        assert result["citations_used"], case["id"]
        assert len(result["citations_used"]) <= len(hybrid_hits), case["id"]
        assert result["source_check"]["status"] in {"pass", "warning"}, case["id"]
        assert result["source_check"]["checked_citation_count"] == len(result["citations_used"]), case["id"]
        assert result["policy_check"]["status"] in {"pass", "warning"}, case["id"]
        assert isinstance(result["policy_check"]["risk_types"], list), case["id"]
        assert isinstance(result["policy_check"]["issues"], list), case["id"]
        assert result["policy_check"]["suggestion"], case["id"]
        assert result["policy_check"]["feedback_collection"]["label_options"], case["id"]

        for hit in hybrid_hits:
            assert REQUIRED_HYBRID_FIELDS.issubset(hit), case["id"]
            assert hit["title"], case["id"]
            assert hit["text"], case["id"]
            assert isinstance(hit["citation"], dict), case["id"]
            assert hit["citation"].get("doc"), case["id"]
            assert hit["citation"].get("section"), case["id"]
            for keyword in case["expected_citation_keywords"]:
                assert keyword in hit["citation"].get("doc", ""), case["id"]

        for citation in result["citations_used"]:
            assert citation["id"], case["id"]
            assert citation["citation"].get("doc"), case["id"]
            assert citation["citation"].get("section"), case["id"]


def test_cadre_education_query_prioritizes_specific_chunk(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve("抗日战争时期党的干部教育为什么重要？")

    assert "干部教育" in result["query_entities"]
    assert result["hybrid_hits"][0]["id"] == "chunk_szzjys_demo_022"


def test_team_mode_keeps_fixed_empty_contract(monkeypatch):
    monkeypatch.delenv("DACHUANG_RETRIEVE_MODE", raising=False)
    monkeypatch.delenv("DACHUANG_LOCAL_MOCK_ACK", raising=False)

    result = retrieve("遵义会议是在什么背景下召开的？")

    assert result["query_entities"] == []
    assert result["vector_hits"] == []
    assert result["graph_hits"] == []
    assert result["hybrid_hits"] == []
    assert result["answer"] == NO_EVIDENCE_ANSWER
    assert result["citations_used"] == []
    assert result["source_check"]["status"] == NO_EVIDENCE_STATUS
    assert result["source_check"]["checked_citation_count"] == 0
    assert result["policy_check"]["status"] == NEED_REVIEW_STATUS
    assert "evidence_missing" in result["policy_check"]["risk_types"]
