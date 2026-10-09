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
        pytest.param("v3_batch01", "v3_b01_q02", marks=pytest.mark.xfail(
            strict=True, reason="现有轻量排序未召回知识分子问题会议证据")),
        ("v3_batch01", "v3_b01_q03"),
        ("v3_batch01", "v3_b01_q04"),
        pytest.param("v3_batch01", "v3_b01_q05", marks=pytest.mark.xfail(
            strict=True, reason="现有轻量排序未召回工商业者改造证据")),
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
