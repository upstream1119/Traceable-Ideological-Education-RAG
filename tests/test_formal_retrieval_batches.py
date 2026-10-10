import json
from pathlib import Path

import pytest

from src.retriever import hybrid_retriever


@pytest.fixture
def local_retrieval(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "local")
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "template")
    monkeypatch.delenv("DACHUANG_VECTOR_BACKEND", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    hybrid_retriever._load_demo_knowledge_base.cache_clear()
    hybrid_retriever._entity_document_frequency.cache_clear()
    yield
    hybrid_retriever._load_demo_knowledge_base.cache_clear()
    hybrid_retriever._entity_document_frequency.cache_clear()


def test_formal_batches_are_loaded(local_retrieval):
    records = hybrid_retriever._load_demo_knowledge_base()
    expected_ids = {
        f"chunk_sizheng_v{version}_{index:03}"
        for version, count in ((1, 196), (2, 49), (3, 24), (4, 24))
        for index in range(1, count + 1)
    }
    assert len(records) == 293
    assert {record["id"] for record in records} == expected_ids


@pytest.mark.parametrize(
    "batch,case_id",
    [
        ("v3_batch01", "v3_b01_q01"),
        ("v3_batch01", "v3_b01_q02"),
        ("v3_batch01", "v3_b01_q03"),
        ("v3_batch01", "v3_b01_q04"),
        ("v3_batch01", "v3_b01_q05"),
        ("v4_batch02", "v4_b02_q01"),
        ("v4_batch02", "v4_b02_q02"),
        ("v4_batch02", "v4_b02_q03"),
        ("v4_batch02", "v4_b02_q04"),
        ("v4_batch02", "v4_b02_q05"),
    ],
)
def test_batch_query_recalls_expected_evidence(local_retrieval, batch, case_id):
    path = Path(__file__).with_name(f"queries_sizheng_{batch}.json")
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    case = next(case for case in cases if case["id"] == case_id)
    result = hybrid_retriever.retrieve(case["question"])
    hits = {hit["id"]: hit for hit in result["hybrid_hits"]}
    for chunk_id in case["expected_chunk_ids"]:
        assert chunk_id in hits
        assert hits[chunk_id]["citation"]["doc"] == "中国共产党思想政治教育史"


def test_restored_gaokao_evidence_can_pass_gate(local_retrieval):
    path = Path(__file__).with_name("queries_sizheng_v4_batch02.json")
    case = json.loads(path.read_text(encoding="utf-8"))["cases"][0]
    result = hybrid_retriever.retrieve(case["question"])
    assert "恢复高考" in result["query_entities"]
    citation = next(
        item for item in result["citations_used"]
        if item["id"] == "chunk_sizheng_v4_008"
    )
    assert citation["citation"]["doc"] == "中国共产党思想政治教育史"
    assert citation["citation"]["page"] == 303
    assert result["final_decision"]["status"] == "approved"
    assert result["final_decision"]["can_output"] is True


@pytest.mark.parametrize("query", ["batch02", "教材切片", "火星量子香蕉传送"])
def test_non_topic_queries_remain_blocked(local_retrieval, query):
    result = hybrid_retriever.retrieve(query)
    assert result["query_entities"] == []
    assert result["citations_used"] == []
    assert result["final_decision"]["status"] == "blocked"
    assert result["final_decision"]["can_output"] is False
