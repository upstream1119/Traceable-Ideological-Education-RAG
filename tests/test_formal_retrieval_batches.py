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
        for version, count in ((1, 196), (2, 49), (3, 24), (4, 24), (5, 15))
        for index in range(1, count + 1)
    }
    assert len(records) == 308
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


@pytest.mark.parametrize("case_index", range(10))
def test_v5_queries_recall_and_cite_expected_evidence(local_retrieval, case_index):
    path = Path(__file__).with_name("queries_sizheng_v5_batch03.json")
    case = json.loads(path.read_text(encoding="utf-8"))[case_index]
    result = hybrid_retriever.retrieve(case["question"])
    hits = {hit["id"]: hit for hit in result["hybrid_hits"]}
    citations = {item["id"]: item for item in result["citations_used"]}
    for chunk_id in case["expected_chunk_ids"]:
        assert chunk_id in hits
        assert hits[chunk_id]["citation"] == case["expected_citation"]
        assert chunk_id in citations
        assert citations[chunk_id]["citation"] == case["expected_citation"]


def test_v5_generic_entities_gain_specific_topic(local_retrieval):
    entities = hybrid_retriever.extract_query_entities(
        "大学生思想政治教育意见于何时由谁印发？"
    )
    assert "大学生思想政治教育" in entities


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


def test_complete_gaokao_question_keeps_required_facts(local_retrieval):
    query = (
        "1977年恢复高考的全国高等学校招生工作会议何时、在哪里召开？"
        "采用什么招生办法，随后规定哪些人可以报考、需要什么文化水平，"
        "并实行什么考核录取原则？当年12月报考和录取人数分别是多少？"
        "请给出教材PDF页码。"
    )
    result = hybrid_retriever.retrieve(query)
    for fact in (
        "1977年8月13日至9月25日", "北京", "统一考试、择优录取",
        "工人、农民、上山下乡和回乡知识青年、复员军人、干部和应届毕业生",
        "高中毕业或相当于高中毕业", "德、智、体全面考核",
        "1977年12月", "570万", "27.3万",
    ):
        assert fact in result["answer"]
    citation = next(
        item for item in result["citations_used"]
        if item["id"] == "chunk_sizheng_v4_008"
    )
    assert citation["citation"]["page"] == 303
    assert result["final_decision"]["status"] == "approved"


def test_zhang_wentian_keeps_four_aspects_and_review_gate(local_retrieval):
    result = hybrid_retriever.retrieve(
        "请面向高中生，以人物叙事方式介绍张闻天起草"
        "《党的宣传鼓动工作提纲》的背景和主要内容。"
    )
    for fact in (
        "1941年6月", "中共中央宣传部", "第一", "第二",
        "第三", "第四", "党内教育", "群众教育",
    ):
        assert fact in result["answer"]
    citations = {item["id"]: item for item in result["citations_used"]}
    for chunk_id in ("chunk_sizheng_v1_166", "chunk_sizheng_v1_167"):
        assert citations[chunk_id]["citation"]["page"] == 130
    assert result["final_decision"]["status"] == "needs_review"
    assert result["final_decision"]["can_output"] is False
    assert [item["id"] for item in result["citations_used"]] == [
        "chunk_sizheng_v1_166", "chunk_sizheng_v1_167",
    ]
    assert result["answer"].index("1941年6月") < result["answer"].index(
        "要根据群众自身的政治经验"
    )
    assert "未提供该文起草背景的直接说明" in result["answer"]
