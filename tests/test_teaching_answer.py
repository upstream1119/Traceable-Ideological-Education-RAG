import json

import pytest

from src.generator import evidence_generator
from src.generator.llm_provider import LLMGenerationResult
from src.reviewer.source_checker import check_answer_sources
from src.reviewer.policy_checker import check_policy_risk


HITS = [{"id": "spirit", "title": "长征精神", "text": "红军展现了革命英雄主义气概和革命乐观主义态度。",
         "citation": {"doc": "教材", "section": "长征", "page": 97}, "hybrid_score": 0.9}]


def candidate(text="长征精神的重要表现包括革命英雄主义和革命乐观主义。"):
    return {"paragraphs": [{"text": text, "supports": [{"evidence_number": 1, "quote": HITS[0]["text"]}]}]}


def run(monkeypatch, payload, review=None, review_status="success", hits=None,
        target_grade=None):
    calls = []
    class Provider:
        def generate(self, prompt):
            calls.append(prompt)
            response = payload if len(calls) == 1 else review
            return LLMGenerationResult(json.dumps(response, ensure_ascii=False), "qwen",
                                       "success" if len(calls) == 1 else review_status)
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "llm")
    monkeypatch.setattr(evidence_generator, "get_llm_provider", lambda name: Provider())
    result = evidence_generator.generate_answer(
        "长征形成了什么精神？", HITS if hits is None else hits,
        target_grade=target_grade,
    )
    return result, calls


REVIEW = {"answers_question": True, "checks": [{"paragraph": 1, "supported": True, "reason": "两种精神均有原文依据。"}]}


def test_direct_answer_requires_quote_validation_and_separate_review(monkeypatch):
    result, calls = run(monkeypatch, candidate(), REVIEW)
    assert result["used_fallback"] is False
    assert result["answer"] == "长征精神的重要表现包括革命英雄主义和革命乐观主义。[1]"
    assert len(calls) == 2
    assert result["evidence_scope"] == "retrieved_evidence"
    assert "革命英雄主义" in calls[1]
    assert "来源：" not in result["answer"]
    assert "材料[" not in result["answer"]


@pytest.mark.parametrize("review", [
    {**REVIEW, "answers_question": False},
    {**REVIEW, "checks": [{"paragraph": 1, "supported": False, "reason": "超出依据"}]},
    {**REVIEW, "checks": []},
    {**REVIEW, "checks": [{"paragraph": 2, "supported": True, "reason": "错号"}]},
    {**REVIEW, "answers_question": "true"},
])
def test_rejected_or_malformed_review_falls_back(monkeypatch, review):
    result, calls = run(monkeypatch, candidate("未经支持的解释。"), review)
    assert len(calls) == 2
    assert result["used_fallback"] is True
    assert result["provider_status"] == "semantic_review_failed"
    assert "未经支持的解释。" not in result["answer"]
    assert result["failure_stage"] == "review"
    assert result["quality_issues"]


def test_provider_review_failure_falls_back(monkeypatch):
    result, calls = run(monkeypatch, candidate(), REVIEW, "provider_error")
    assert len(calls) == 2
    assert result["used_fallback"] is True


@pytest.mark.parametrize("mutate", [
    lambda p: p["paragraphs"][0]["supports"][0].update(quote="编造的原文。"),
    lambda p: p["paragraphs"][0].update(text="结论。[99]"),
    lambda p: p["paragraphs"][0].update(text="材料[1]表述：旧模板。"),
    lambda p: p["paragraphs"][0].update(supports=[]),
])
def test_invalid_support_stops_before_review(monkeypatch, mutate):
    payload = candidate(); mutate(payload)
    result, calls = run(monkeypatch, payload, REVIEW)
    assert result["used_fallback"] is True
    assert len(calls) == 1
    assert result["failure_stage"] == "validation"


def test_sparse_original_numbers_are_compacted_with_correct_citation_id(monkeypatch):
    payload = candidate(); payload["paragraphs"][0]["supports"][0]["evidence_number"] = 2
    hits = [dict(HITS[0], id="background"), HITS[0]]
    result, _ = run(monkeypatch, payload, REVIEW, hits=hits)
    assert result["answer"].endswith("[1]")
    assert [c["id"] for c in result["citations_used"]] == ["spirit"]


def test_no_evidence_never_calls_provider(monkeypatch):
    result, calls = run(monkeypatch, candidate(), REVIEW, hits=[])
    assert calls == []
    assert result["provider_status"] == "skipped_no_evidence"


def test_supported_core_survives_rejected_optional_explanation(monkeypatch):
    payload = candidate()
    payload["paragraphs"].append({"text": "背景被不当地解释为精神内涵。", "supports": payload["paragraphs"][0]["supports"]})
    review = {"answers_question": True, "checks": [REVIEW["checks"][0],
        {"paragraph": 2, "supported": False, "reason": "背景与精神内涵的联系缺少依据"}]}
    result, calls = run(monkeypatch, payload, review)
    assert len(calls) == 2
    assert result["used_fallback"] is False
    assert result["answer"] == "长征精神的重要表现包括革命英雄主义和革命乐观主义。[1]"
    assert "背景被不当地解释" not in result["answer"]
    assert "已省略" in result["quality_issues"][0]


def test_body_citations_replace_repeated_full_source_list():
    citations = [{"id": HITS[0]["id"], "citation": HITS[0]["citation"]}]
    assert check_answer_sources("有依据的正文。[1]", citations)["status"] == "pass"
    assert check_answer_sources("编号越界。[2]", citations)["status"] == "fail"


def test_explicit_program_scope_replaces_boilerplate_without_skipping_risk_checks():
    citations = [{"id": HITS[0]["id"], "citation": HITS[0]["citation"]}]
    source = {"status": "pass", "evidence_scope": "retrieved_evidence"}
    result = check_policy_risk("长征精神的重要表现包括革命英雄主义和革命乐观主义。[1]", citations, source)
    assert result["status"] == "pass"
    assert "missing_scope_statement" not in result["risk_types"]
    result = check_policy_risk("这是唯一原因。[1]", citations, source)
    assert "unsupported_absolute_claim" in result["risk_types"]
    result = check_policy_risk("有依据的正文。[1]", citations, dict(source, status="fail"))
    assert "source_check_failed" in result["risk_types"]


@pytest.mark.parametrize("grade,label", [
    ("primary", "面向小学生"),
    ("junior_high", "面向初中生"),
    ("senior_high", "面向高中生"),
    ("university", "面向大学生"),
])
def test_grade_reaches_generation_without_changing_evidence(monkeypatch, grade, label):
    baseline, baseline_calls = run(monkeypatch, candidate(), REVIEW)
    graded_review = {"answers_question": True, "checks": [{
        **REVIEW["checks"][0],
        "subject_consistent": True, "sequence_consistent": True,
        "causality_supported": True, "language_appropriate": True,
        "depth_appropriate": True, "coherent": True,
    }]}
    result, calls = run(monkeypatch, candidate("红军面对困难不退缩，也不轻易放弃希望。"), graded_review, target_grade=grade)
    assert label in calls[0]
    payload = json.loads(calls[0].split("\n\n", 1)[1])
    baseline_payload = json.loads(baseline_calls[0].split("\n\n", 1)[1])
    assert payload["evidence"] == baseline_payload["evidence"]
    assert payload["teaching_profile"]["target_grade"] == grade
    assert label.replace("面向", "").replace("生", "") in calls[1]
    assert result["citations_used"] == baseline["citations_used"]
    assert result["used_fallback"] is False
    assert result["teaching_adaptation"]["status"] == "passed"
    assert len(calls) == 2


@pytest.mark.parametrize("field", [
    "subject_consistent", "sequence_consistent",
    "causality_supported", "coherent",
])
@pytest.mark.parametrize("value", [False, "true", None])
def test_grade_review_rejects_failed_or_invalid_checks(monkeypatch, field, value):
    check = {
        **REVIEW["checks"][0],
        "subject_consistent": True, "sequence_consistent": True,
        "causality_supported": True, "language_appropriate": True,
        "depth_appropriate": True, "coherent": True,
    }
    check[field] = value
    review = {"answers_question": True, "checks": [check]}
    result, calls = run(monkeypatch, candidate("红军面对困难不退缩，也不轻易放弃希望。"), review, target_grade="primary")
    assert result["used_fallback"] is True
    assert result["failure_stage"] == "review"
    assert result["provider_status"] == "semantic_review_failed"
    assert len(calls) == 2


def test_selected_grade_rejects_legacy_review(monkeypatch):
    result, calls = run(monkeypatch, candidate("红军面对困难不退缩，也不轻易放弃希望。"), REVIEW, target_grade="primary")
    assert result["used_fallback"] is True
    assert result["failure_stage"] == "review"
    assert len(calls) == 2


def test_graded_answer_never_splices_remaining_paragraphs_after_rejection(monkeypatch):
    payload = candidate("红军把会议精神逐级告诉干部和战士。")
    payload["paragraphs"].append({
        "text": "红军取得胜利后，大家看到了好处。",
        "supports": payload["paragraphs"][0]["supports"],
    })
    check = {
        "paragraph": 1, "supported": True, "reason": "首段有依据。",
        "subject_consistent": True, "sequence_consistent": True,
        "causality_supported": True, "language_appropriate": True,
        "depth_appropriate": True, "coherent": True,
    }
    review = {"answers_question": True, "checks": [check,
        dict(check, paragraph=2, supported=False, causality_supported=False,
             reason="补充解释超出材料。")]}
    result, calls = run(monkeypatch, payload, review, target_grade="junior_high")
    assert result["used_fallback"] is True
    assert result["failure_stage"] == "review"
    assert "大家看到了好处" not in result["answer"]
    assert len(calls) == 2


@pytest.mark.parametrize("dimension", ["language_appropriate", "depth_appropriate"])
def test_style_failure_preserves_supported_answer_but_never_claims_adapted(monkeypatch, dimension):
    text = "红军面对困难不退缩，也不轻易放弃希望。"
    check = {
        "paragraph": 1, "supported": True, "reason": "事实有依据，但学段表达仍需完善。",
        "subject_consistent": True, "sequence_consistent": True,
        "causality_supported": True, "language_appropriate": True,
        "depth_appropriate": True, "coherent": True,
    }
    check[dimension] = False
    review = {"answers_question": True, "checks": [check]}
    result, calls = run(monkeypatch, candidate(text), review, target_grade="primary")
    assert result["used_fallback"] is False
    assert result["answer"] == text + "[1]"
    assert result["teaching_adaptation"]["status"] == "needs_review"
    assert result["teaching_adaptation"]["checks"]["facts"] is True
    assert result["teaching_adaptation"]["issues"]
    assert len(calls) == 2


def test_local_expression_issue_is_advisory_after_facts_pass(monkeypatch):
    check = {
        "paragraph": 1, "supported": True, "reason": "原文支持。",
        "subject_consistent": True, "sequence_consistent": True,
        "causality_supported": True, "language_appropriate": True,
        "depth_appropriate": True, "coherent": True,
    }
    result, calls = run(monkeypatch, candidate(), {"answers_question": True, "checks": [check]}, target_grade="primary")
    assert result["used_fallback"] is False
    assert result["teaching_adaptation"]["status"] == "needs_review"
    assert result["teaching_adaptation"]["checks"]["language"] is False
    assert len(calls) == 2
