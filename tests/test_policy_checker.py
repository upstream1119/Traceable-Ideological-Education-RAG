from src.reviewer.policy_checker import (
    NEED_REVIEW_STATUS,
    PASS_STATUS,
    WARNING_STATUS,
    check_policy_risk,
)


def _citation() -> dict:
    return {
        "id": "chunk_test_001",
        "title": "测试证据",
        "source": "中国共产党思想政治教育史",
        "citation": {
            "doc": "中国共产党思想政治教育史",
            "section": "测试章节",
            "page": 1,
        },
        "hybrid_score": 0.9,
    }


def test_policy_check_requires_evidence():
    result = check_policy_risk("", [], {"status": "no_evidence"})

    assert result["status"] == NEED_REVIEW_STATUS
    assert "evidence_missing" in result["risk_types"]
    assert result["review_required"] is True
    assert result["max_severity"] == "high"
    assert result["review_items"][0]["risk_type"] == "evidence_missing"


def test_policy_check_blocks_failed_source_check():
    result = check_policy_risk(
        "有回答但溯源失败。",
        [_citation()],
        {"status": "fail"},
    )

    assert result["status"] == NEED_REVIEW_STATUS
    assert "source_check_failed" in result["risk_types"]


def test_policy_check_warns_when_scope_statement_is_missing():
    result = check_policy_risk(
        "这是一个有证据的回答。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == WARNING_STATUS
    assert "missing_scope_statement" in result["risk_types"]
    assert result["review_required"] is True
    assert result["max_severity"] == "medium"
    assert result["review_items"][0]["risk_type"] == "missing_scope_statement"
    assert result["review_items"][0]["dimension"] == "evidence_alignment"
    assert result["review_items"][0]["suggestion"]
    assert result["feedback_collection"]["review_dimensions"]
    assert result["feedback_collection"]["decision_options"]
    assert result["feedback_collection"]["required_fields"]


def test_policy_check_accepts_alternative_evidence_boundary_statement():
    result = check_policy_risk(
        "根据给定证据，可以认为该回答仍需要结合教材章节进一步复核。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == PASS_STATUS
    assert "missing_scope_statement" not in result["risk_types"]


def test_policy_check_warns_for_absolute_claims():
    result = check_policy_risk(
        "仅依据当前检索到的证据，可以说这是唯一原因。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == WARNING_STATUS
    assert "unsupported_absolute_claim" in result["risk_types"]


def test_policy_check_warns_for_sensitive_historical_context():
    result = check_policy_risk(
        "仅依据当前检索到的证据，人民解放军教育改造国民党被俘和起义部队。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == WARNING_STATUS
    assert "historical_context_needs_review" in result["risk_types"]


def test_policy_check_warns_for_incomplete_long_march_mobilization_answer():
    result = check_policy_risk(
        "仅依据当前检索到的证据，长征中红军通过政治动员鼓舞士气，主要依靠关心战士生活和生活保障。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == WARNING_STATUS
    assert "political_mobilization_needs_review" in result["risk_types"]
    item = next(
        review_item
        for review_item in result["review_items"]
        if review_item["risk_type"] == "political_mobilization_needs_review"
    )
    assert item["dimension"] == "mobilization_completeness"
    assert "关心战士生活" in item["reason"]


def test_policy_check_passes_complete_long_march_mobilization_answer():
    result = check_policy_risk(
        "仅依据当前检索到的证据，长征中红军通过政治动员鼓舞士气，既强调理想信念和革命目标，也依托组织纪律、连队党支部、宣传鼓动和生活关怀。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == PASS_STATUS
    assert "political_mobilization_needs_review" not in result["risk_types"]


def test_policy_check_passes_bounded_answer_with_clean_source_check():
    result = check_policy_risk(
        "以上回答仅依据当前检索到的证据生成，后续仍需要专家进一步复核。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == PASS_STATUS
    assert result["risk_types"] == []
    assert result["review_required"] is False
    assert result["max_severity"] == "none"
    assert result["review_items"] == []
    assert result["feedback_collection"]["label_options"]


def test_policy_check_marks_source_failure_as_high_severity():
    result = check_policy_risk(
        "有回答但溯源失败。",
        [_citation()],
        {"status": "fail"},
    )

    assert result["status"] == NEED_REVIEW_STATUS
    assert result["review_required"] is True
    assert result["max_severity"] == "high"
    assert result["review_items"][0]["risk_type"] == "source_check_failed"
