import json
import os
from pathlib import Path

import numpy as np

from src.generator.template_generator import NO_EVIDENCE_ANSWER
from src.retriever import hybrid_retriever
from src.retriever.hybrid_retriever import (
    _filter_valid_graph_paths,
    _score_graph_paths,
    retrieve,
)
from src.vector.faiss_store import FaissVectorStore
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
        assert isinstance(result["policy_check"]["review_items"], list), case["id"]
        assert isinstance(result["policy_check"]["review_required"], bool), case["id"]
        assert result["policy_check"]["max_severity"] in {"none", "low", "medium", "high"}, case["id"]
        assert result["policy_check"]["suggestion"], case["id"]
        assert result["policy_check"]["feedback_collection"]["label_options"], case["id"]
        assert result["policy_check"]["feedback_collection"]["decision_options"], case["id"]
        assert result["policy_check"]["feedback_collection"]["required_fields"], case["id"]
        assert len(result["agent_trace"]) == 4, case["id"]
        assert [step["agent"] for step in result["agent_trace"]] == [
            "retrieval_stage",
            "generator",
            "source_reviewer",
            "policy_reviewer",
        ], case["id"]
        assert result["final_decision"]["status"] in {
            "approved",
            "needs_review",
            "blocked",
        }, case["id"]
        assert isinstance(result["final_decision"]["can_output"], bool), case["id"]
        assert isinstance(result["final_decision"]["review_required"], bool), case["id"]
        assert result["final_decision"]["reason"], case["id"]

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


def test_graphsim_expansion_contributes_to_graph_hits(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve("张闻天起草的宣传鼓动工作提纲强调了什么？")

    graph_hit = next(
        hit for hit in result["graph_hits"]
        if hit["id"] == "chunk_szzjys_demo_025"
    )
    assert "张闻天" in result["query_entities"]
    assert "党的宣传鼓动工作提纲" in graph_hit["related_entities"]
    assert graph_hit["graph_paths"]
    assert any(
        "张闻天" in path["path"] and "党的宣传鼓动工作提纲" in path["path"]
        for path in graph_hit["graph_paths"]
    )
    assert graph_hit["graph_score"] > 0
    assert result["hybrid_hits"][0]["graph_paths"]


def test_graphsim_connects_antijapanese_war_to_cadre_education(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve("抗日战争时期党的干部教育为什么重要？")

    assert "干部教育" in result["query_entities"]
    assert result["hybrid_hits"][0]["id"] == "chunk_szzjys_demo_022"
    assert any(
        hit["id"] == "chunk_szzjys_demo_022" and hit["graph_score"] > 0
        for hit in result["graph_hits"]
    )
    assert any(
        hit["id"] == "chunk_szzjys_demo_022" and hit["graph_paths"]
        for hit in result["graph_hits"]
    )


def test_graphsim_handles_party_first_congress_query(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve("党的一大如何确定思想政治教育的根本目的？")

    assert "党的一大" in result["query_entities"]
    graph_hit = next(
        hit for hit in result["graph_hits"]
        if hit["id"] == "chunk_szzjys_demo_006"
    )
    assert "思想政治教育的根本目的" in graph_hit["related_entities"]
    assert any(
        path["path"] == ["党的一大", "思想政治教育的根本目的"]
        for path in graph_hit["graph_paths"]
    )


def test_graphsim_prefers_marxism_spread_trend_evidence(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve("马克思主义传播为什么成为潮流？")

    assert "马克思主义" in result["query_entities"]
    assert "滔滔滚滚的潮流" in result["query_entities"]
    assert result["graph_hits"][0]["id"] == "chunk_szzjys_demo_003"
    assert result["hybrid_hits"][0]["id"] == "chunk_szzjys_demo_003"


def test_graphsim_handles_kuomintang_surrendered_troops_query(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve("国民党起义投诚部队为什么要接受人民解放军教育改造？")

    assert "国民党被俘、起义部队" in result["query_entities"]
    graph_hit = next(
        hit for hit in result["graph_hits"]
        if hit["id"] == "chunk_szzjys_demo_034"
    )
    assert "人民解放军" in graph_hit["related_entities"]
    assert graph_hit["graph_paths"]
    assert result["graph_hits"][0]["id"] == "chunk_szzjys_demo_034"
    assert result["hybrid_hits"][0]["id"] == "chunk_szzjys_demo_034"


def test_graph_path_scoring_prefers_shorter_weighted_paths():
    short_path = {
        "from": "张闻天",
        "to": "党的宣传鼓动工作提纲",
        "hops": 1,
        "path": ["张闻天", "党的宣传鼓动工作提纲"],
        "relations": ["起草"],
    }
    long_path = {
        "from": "张闻天",
        "to": "思想政治教育",
        "hops": 2,
        "path": ["张闻天", "党的宣传鼓动工作提纲", "思想政治教育"],
        "relations": ["起草", "关联"],
    }

    assert _score_graph_paths([short_path]) > _score_graph_paths([long_path])


def test_invalid_graph_paths_are_filtered():
    paths = [
        {
            "from": "张闻天",
            "to": "党的宣传鼓动工作提纲",
            "hops": 1,
            "path": ["张闻天", "党的宣传鼓动工作提纲"],
            "relations": ["起草"],
        },
        {
            "from": "张闻天",
            "to": "无关实体",
            "hops": 1,
            "path": ["张闻天", "无关实体"],
            "relations": ["关联"],
        },
        {
            "from": "张闻天",
            "to": "张闻天",
            "hops": 2,
            "path": ["张闻天", "干部教育部", "张闻天"],
            "relations": ["任部长", "关联"],
        },
    ]

    assert _filter_valid_graph_paths(
        paths,
        query_entities=["张闻天"],
        related_entities=["党的宣传鼓动工作提纲"],
    ) == [paths[0]]


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
    assert result["policy_check"]["review_required"] is True
    assert result["policy_check"]["max_severity"] == "high"
    assert result["agent_trace"][0]["status"] == "no_evidence"
    assert result["final_decision"]["status"] == "blocked"
    assert result["final_decision"]["can_output"] is False
    assert result["final_decision"]["review_required"] is True


def test_retrieve_vector_can_use_optional_faiss_backend(monkeypatch, tmp_path):
    records = [
        {
            "id": "anti_encirclement",
            "source": "测试教材",
            "title": "进行政治动员鼓舞士气",
            "text": "政治动员服务于反围剿斗争。",
            "citation": {
                "doc": "测试教材",
                "section": (
                    "第二章 / 第三节 红军反围剿斗争和长征中的思想政治教育"
                    " / 一、思想政治教育为反围剿斗争服务"
                ),
                "page": 90,
            },
        },
        {
            "id": "long_march",
            "source": "测试教材",
            "title": "深入开展政治动员，激发官兵革命斗志",
            "text": "红军长征中的思想政治教育重视政治动员。",
            "citation": {
                "doc": "测试教材",
                "section": (
                    "第二章 / 第三节 红军反围剿斗争和长征中的思想政治教育"
                    " / 三、红军长征中的思想政治教育"
                ),
                "page": 95,
            },
        },
    ]
    store = FaissVectorStore()
    store.build(records, np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype="float32"))
    store.save(tmp_path / "index.faiss", tmp_path / "metadata.json")

    class FakeEmbeddingProvider:
        def embed(self, texts):
            return type(
                "EmbeddingResult",
                (),
                {
                    "status": "success",
                    "vectors": [[0.718, 0.696]],
                },
            )()

    monkeypatch.setenv("DACHUANG_VECTOR_BACKEND", "faiss")
    monkeypatch.setenv("DACHUANG_FAISS_INDEX_DIR", str(tmp_path))
    monkeypatch.setattr(
        hybrid_retriever,
        "QwenEmbeddingProvider",
        FakeEmbeddingProvider,
        raising=False,
    )

    hits = hybrid_retriever.retrieve_vector(
        "长征中红军如何通过政治动员鼓舞士气？",
        [],
        top_k=2,
    )

    assert hits[0]["id"] == "long_march"
    assert hits[0]["citation"]["page"] == 95
    assert hits[0]["base_vector_score"] < hits[0]["vector_score"]


def test_retrieve_can_fuse_faiss_hits_outside_demo_knowledge_base(monkeypatch, tmp_path):
    records = [
        {
            "id": "external_chunk_001",
            "source": "测试教材",
            "title": "外部 FAISS 证据",
            "text": "这是不在 text_chunks_demo.jsonl 中的 FAISS 证据。",
            "citation": {
                "doc": "测试教材",
                "section": "第一章 / 第一节",
                "page": 1,
            },
        }
    ]
    store = FaissVectorStore()
    store.build(records, np.asarray([[1.0, 0.0]], dtype="float32"))
    store.save(tmp_path / "index.faiss", tmp_path / "metadata.json")

    class FakeEmbeddingProvider:
        def embed(self, texts):
            return type(
                "EmbeddingResult",
                (),
                {
                    "status": "success",
                    "vectors": [[1.0, 0.0]],
                },
            )()

    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")
    monkeypatch.setenv("DACHUANG_VECTOR_BACKEND", "faiss")
    monkeypatch.setenv("DACHUANG_FAISS_INDEX_DIR", str(tmp_path))
    monkeypatch.setattr(
        hybrid_retriever,
        "QwenEmbeddingProvider",
        FakeEmbeddingProvider,
        raising=False,
    )

    result = retrieve("外部 FAISS 证据")

    assert result["hybrid_hits"][0]["id"] == "external_chunk_001"
    assert result["hybrid_hits"][0]["citation"]["page"] == 1
    assert result["citations_used"][0]["id"] == "external_chunk_001"


def test_retrieve_response_exposes_generator_status(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve("张闻天起草的宣传鼓动工作提纲强调了什么？")

    assert result["generator_mode"]
    assert "generator_provider" in result
    assert "provider_status" in result
    assert "used_fallback" in result
