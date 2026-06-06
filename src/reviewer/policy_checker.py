PASS_STATUS = "pass"
WARNING_STATUS = "warning"
NEED_REVIEW_STATUS = "need_review"

ABSOLUTE_CLAIM_PHRASES = [
    "唯一原因",
    "必然导致",
    "完全证明",
    "彻底解决",
    "毫无问题",
    "永远正确",
    "不可能出错",
]

HISTORICAL_CONTEXT_TERMS = [
    "国民党被俘",
    "起义部队",
    "投诚部队",
    "阶级斗争",
    "政治路线",
]

FEEDBACK_LABEL_OPTIONS = [
    "通过",
    "证据不足",
    "表述不够稳妥",
    "历史语境不清",
    "结论超出材料",
    "需要专家复核",
]


def _build_feedback_collection(
    stage: str,
    recommended_reviewer: str,
    expert_review_priority: str,
) -> dict:
    return {
        "stage": stage,
        "recommended_reviewer": recommended_reviewer,
        "expert_review_priority": expert_review_priority,
        "label_options": FEEDBACK_LABEL_OPTIONS,
    }


def _contains_any(text: str, phrases: list[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase in text]


def _add_issue(
    issues: list[str],
    risk_types: list[str],
    risk_type: str,
    issue: str,
) -> None:
    if risk_type not in risk_types:
        risk_types.append(risk_type)
    issues.append(issue)


def _build_result(
    status: str,
    risk_types: list[str],
    issues: list[str],
    suggestion: str,
    reviewer: str,
    priority: str,
    stage: str = "rule_seed",
) -> dict:
    return {
        "status": status,
        "risk_types": risk_types,
        "issues": issues,
        "suggestion": suggestion,
        "feedback_collection": _build_feedback_collection(
            stage=stage,
            recommended_reviewer=reviewer,
            expert_review_priority=priority,
        ),
    }


def check_policy_risk(answer: str, citations_used: list[dict], source_check: dict) -> dict:
    """
    政治红线审查智能体最小原型。
    当前定位为专家反馈数据引擎的规则型初筛，不替代赵老师专家审查。
    """
    issues = []
    risk_types = []

    if not answer.strip() or not citations_used:
        return {
            "status": NEED_REVIEW_STATUS,
            "risk_types": ["evidence_missing"],
            "issues": ["当前回答缺少可用证据支撑，不建议直接输出。"],
            "suggestion": "请补充检索证据，或交由人工复核。",
            "feedback_collection": _build_feedback_collection(
                stage="student_initial_label",
                recommended_reviewer="研究生或项目组员先初标，赵老师抽样校准。",
                expert_review_priority="high",
            ),
        }

    source_status = source_check.get("status")
    if source_status in {"fail", "no_evidence"}:
        return _build_result(
            status=NEED_REVIEW_STATUS,
            risk_types=["source_check_failed"],
            issues=["溯源审查未通过，回答来源链条不完整。"],
            suggestion="请先修复 citation，再进行政治红线审查。",
            reviewer="研究生或项目组员先初标，赵老师抽样校准。",
            priority="high",
            stage="student_initial_label",
        )

    if source_status == "warning":
        _add_issue(
            issues,
            risk_types,
            "source_check_warning",
            "溯源审查存在 warning，需要人工复核来源完整性。",
        )

    if "仅依据当前检索到的证据" not in answer:
        _add_issue(
            issues,
            risk_types,
            "missing_scope_statement",
            "回答缺少证据边界说明，可能让使用者误以为结论已经完全定稿。",
        )

    absolute_claims = _contains_any(answer, ABSOLUTE_CLAIM_PHRASES)
    if absolute_claims:
        _add_issue(
            issues,
            risk_types,
            "unsupported_absolute_claim",
            f"回答出现较绝对的表述：{absolute_claims}。需要确认是否超出材料。",
        )

    context_terms = _contains_any(answer, HISTORICAL_CONTEXT_TERMS)
    if context_terms:
        _add_issue(
            issues,
            risk_types,
            "historical_context_needs_review",
            f"回答涉及需要谨慎处理的历史语境：{context_terms}。建议专家抽样复核。",
        )

    status = WARNING_STATUS if issues else PASS_STATUS
    return _build_result(
        status=status,
        risk_types=risk_types,
        issues=issues,
        suggestion="建议保留研究生初标与赵老师抽样校准机制。",
        reviewer="低风险样例由研究生或组员初标，高风险和争议样例交赵老师校准。",
        priority="normal" if status == PASS_STATUS else "medium",
    )
