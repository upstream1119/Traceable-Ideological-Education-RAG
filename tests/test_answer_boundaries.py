import json

import pytest

from src.generator import evidence_generator
from src.generator.llm_provider import LLMGenerationResult
from src.reviewer.semantic_checker import (
    EvidenceAlignmentError, build_teaching_prompt, validate_question_boundaries,
)


SPIRIT_HITS = [{"text": "刘伯承与小叶丹结盟。红军展现了不怕困难的英雄主义气概和乐观主义态度。"}]
PERMISSION_HITS = [{"text": "工人、农民和应届毕业生，只要符合条件都可报考，考生应有高中毕业文化水平。考试有570万人参加。"}]


def paragraph(text, quote, number=1):
    return {"text": text, "supports": [{"evidence_number": number, "quote": quote}]}


def test_definition_prompt_excludes_nearby_events_without_renumbering():
    prompt = build_teaching_prompt("长征形成了什么精神？", SPIRIT_HITS, "primary")
    payload = json.loads(prompt.split("\n\n", 1)[1])
    assert payload["answer_constraints"]["definition_only"] is True
    assert payload["evidence"][0]["sentences"] == [
        {"quote_id": "E1S2", "text": "红军展现了不怕困难的英雄主义气概和乐观主义态度。"}]
    assert "刘伯承" not in payload["evidence"][0]["sentences"][0]["text"]
    full = json.loads(build_teaching_prompt("请举例说明长征精神如何体现？", SPIRIT_HITS).split("\n\n", 1)[1])
    assert len(full["evidence"][0]["sentences"]) == 2
    assert full["answer_constraints"]["definition_only"] is False


@pytest.mark.parametrize("text", [
    "工人、农民和应届毕业生均可报考。",
    "工人、农民和应届毕业生都可以报名。",
    "不需要符合条件也可以报考。",
])
def test_permission_cannot_drop_or_negate_original_condition(text):
    # 即便模型只挂了人数句，程序仍检查其引用文段中的许可条件。
    with pytest.raises(EvidenceAlignmentError, match="条件限定"):
        validate_question_boundaries("哪些人可以报考？", [paragraph(text, "考试有570万人参加。")], PERMISSION_HITS)


@pytest.mark.parametrize("text", [
    "工人、农民和应届毕业生只要符合条件都可报考。",
    "符合报考条件的工人、农民和应届毕业生可以报名。",
    "工人、农民和应届毕业生满足规定条件就可以报考。",
    "考试有570万人参加。",
])
def test_preserved_condition_and_unrelated_facts_remain_usable(text):
    validate_question_boundaries("招生情况是什么？", [paragraph(text, PERMISSION_HITS[0]["text"])], PERMISSION_HITS)


@pytest.mark.parametrize("support", ["刘伯承与小叶丹结盟。", "红军展现了不怕困难的英雄主义气概和乐观主义态度。"])
def test_example_cannot_be_added_to_spirit_definition_even_with_real_quotes(support):
    with pytest.raises(EvidenceAlignmentError, match="精神释义"):
        validate_question_boundaries("长征形成了什么精神？", [paragraph(
            "红军不怕困难，比如刘伯承与小叶丹结盟靠的就是坚持和真诚。", support)], SPIRIT_HITS)


def test_grounded_definition_is_allowed():
    validate_question_boundaries("长征形成了什么精神？", [paragraph(
        "红军面对困难不退缩，遇到困难也保持乐观。",
        "红军展现了不怕困难的英雄主义气概和乐观主义态度。")], SPIRIT_HITS)


def test_redundant_background_support_does_not_reject_a_grounded_definition():
    answer = paragraph("长征精神的内涵包括不怕困难的英雄主义气概和乐观主义态度。",
                       "红军展现了不怕困难的英雄主义气概和乐观主义态度。")
    answer["supports"].append({"evidence_number": 1, "quote": "刘伯承与小叶丹结盟。"})
    validate_question_boundaries("长征形成了什么精神？", [answer], SPIRIT_HITS)


def test_model_approval_cannot_bypass_local_condition_guard(monkeypatch):
    hits = [{**PERMISSION_HITS[0], "id": "permission", "title": "招生", "source": "教材",
             "citation": {"doc": "教材", "section": "招生", "page": 303}, "hybrid_score": 1}]
    calls = []
    class Provider:
        def generate(self, prompt):
            calls.append(prompt)
            payload = {"paragraphs": [{"text": "工人、农民和应届毕业生均可报考。",
                                        "supports": [{"quote_id": "E1S1"}]}]} if len(calls) == 1 else {
                "answers_question": True, "checks": [{"paragraph": 1, "supported": True,
                "subject_consistent": True, "sequence_consistent": True, "causality_supported": True,
                "language_appropriate": True, "depth_appropriate": True, "coherent": True, "reason": "模型误放行。"}]}
            return LLMGenerationResult(json.dumps(payload, ensure_ascii=False), "fake", "success")
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "llm")
    monkeypatch.setattr(evidence_generator, "get_llm_provider", lambda name: Provider())
    response = evidence_generator.generate_answer("哪些人可以报考？", hits, target_grade="senior_high")
    assert len(calls) == 2
    assert response["used_fallback"] is True
    assert response["failure_stage"] == "evidence_boundary"
    assert response["teaching_adaptation"]["status"] == "not_applied"
    assert "均可报考" not in response["answer"]
    assert "只要符合条件都可报考" in response["answer"]
