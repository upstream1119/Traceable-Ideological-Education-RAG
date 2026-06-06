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


def test_policy_check_passes_bounded_answer_with_clean_source_check():
    result = check_policy_risk(
        "以上回答仅依据当前检索到的证据生成，后续仍需要专家进一步复核。",
        [_citation()],
        {"status": "pass"},
    )

    assert result["status"] == PASS_STATUS
    assert result["risk_types"] == []
    assert result["feedback_collection"]["label_options"]
