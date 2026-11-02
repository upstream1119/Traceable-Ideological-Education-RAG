"""回迁的关键集成边界：正式语料、学段传递及已核实的内容修复。"""
import json

import pytest
from src.api.main import RetrieveRequest, retrieve
from src.generator import evidence_generator
from src.generator.llm_provider import LLMGenerationResult


@pytest.mark.parametrize("grade", ["primary", "junior_high", "senior_high", "university"])
def test_real_retrieval_keeps_template_grade_unapplied(monkeypatch, grade):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "local")
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "template")
    monkeypatch.delenv("DACHUANG_VECTOR_BACKEND", raising=False)
    data = retrieve(RetrieveRequest(
        query="1977年恢复高考采用什么招生办法，参加考试和录取人数是多少？",
        target_grade=grade,
    ))
    assert data["display_route"]["target_grade"] == grade
    assert data["teaching_adaptation"]["status"] == "not_applied"
    assert set(data["teaching_adaptation"]["checks"].values()) == {None}
    assert any(c["id"] == "chunk_sizheng_v4_008" for c in data["citations_used"])
    assert "570万" in data["answer"] and "27.3万" in data["answer"]


def test_online_path_preserves_verified_order_and_background_limit(monkeypatch):
    hits = [
        {"id": "chunk_sizheng_v1_167", "source": "教材", "title": "张闻天起草党的宣传鼓动工作提纲",
         "text": "张闻天的提纲第四方面说明组织领导。", "hybrid_score": .9,
         "citation": {"doc": "教材", "section": "提纲", "page": 130}},
        {"id": "chunk_sizheng_v1_166", "source": "教材", "title": "张闻天起草党的宣传鼓动工作提纲",
         "text": "张闻天起草提纲，第一方面说明概念。", "hybrid_score": .8,
         "citation": {"doc": "教材", "section": "提纲", "page": 130}},
    ]
    calls = []
    class Provider:
        def generate(self, prompt):
            calls.append(prompt)
            if len(calls) == 1:
                payload = {"paragraphs": [{"text": "第一方面说明概念。", "supports": [{"quote_id": "E1S1"}]}]}
            else:
                payload = {"answers_question": True, "checks": [
                    {"paragraph": 1, "supported": True, "reason": "有直接原文。"}]}
            return LLMGenerationResult(json.dumps(payload, ensure_ascii=False), "fake", "success")
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "llm")
    monkeypatch.setattr(evidence_generator, "get_llm_provider", lambda _: Provider())
    result = evidence_generator.generate_answer("张闻天起草《党的宣传鼓动工作提纲》的背景和主要内容是什么？", hits)
    assert result["used_fallback"] is False
    assert result["citations_used"][0]["id"] == "chunk_sizheng_v1_166"
    assert "未提供该文起草背景的直接说明" in result["answer"]
    assert "服务端已核实的证据边界" in calls[0]
    assert len(calls) == 2
