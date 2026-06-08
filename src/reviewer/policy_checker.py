PASS_STATUS = "pass"
WARNING_STATUS = "warning"
NEED_REVIEW_STATUS = "need_review"
SEVERITY_NONE = "none"
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_ORDER = {
    SEVERITY_NONE: 0,
    SEVERITY_LOW: 1,
    SEVERITY_MEDIUM: 2,
    SEVERITY_HIGH: 3,
}

DECISION_OPTIONS = [
    "通过",
    "需要修改",
    "需要专家复核",
    "不能输出",
]
ANNOTATION_REQUIRED_FIELDS = [
    "decision",
    "reason",
    "corrected_suggestion",
]

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
        "decision_options": DECISION_OPTIONS,
        "required_fields": ANNOTATION_REQUIRED_FIELDS,
    }


def _contains_any(text: str, phrases: list[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase in text]


def _add_issue(
    issues: list[str],
    risk_types: list[str],
    review_items: list[dict],
    risk_type: str,
    issue: str,
    severity: str,
    suggestion: str,
    expert_focus: str,
) -> None:
    if risk_type not in risk_types:
        risk_types.append(risk_type)
    issues.append(issue)
    review_items.append(
        {
            "risk_type": risk_type,
            "severity": severity,
            "reason": issue,
            "suggestion": suggestion,
            "expert_focus": expert_focus,
        }
    )


def _max_severity(review_items: list[dict]) -> str:
    max_level = SEVERITY_NONE
    for item in review_items:
        severity = item.get("severity", SEVERITY_NONE)
        if SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER[max_level]:
            max_level = severity
    return max_level


def _build_result(
    status: str,
    risk_types: list[str],
    issues: list[str],
    review_items: list[dict],
    suggestion: str,
    reviewer: str,
    priority: str,
    stage: str = "rule_seed",
) -> dict:
    return {
        "status": status,
        "risk_types": risk_types,
        "issues": issues,
        "review_required": status != PASS_STATUS,
        "max_severity": _max_severity(review_items),
        "review_items": review_items,
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
    review_items = []

    if not answer.strip() or not citations_used:
        return {
            "status": NEED_REVIEW_STATUS,
            "risk_types": ["evidence_missing"],
            "issues": ["当前回答缺少可用证据支撑，不建议直接输出。"],
            "review_required": True,
            "max_severity": SEVERITY_HIGH,
            "review_items": [
                {
                    "risk_type": "evidence_missing",
                    "severity": SEVERITY_HIGH,
                    "reason": "当前回答缺少可用证据支撑，不建议直接输出。",
                    "suggestion": "请补充检索证据，或交由人工复核。",
                    "expert_focus": "请确认该问题是否需要补充资料后再回答。",
                }
            ],
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
            review_items=[
                {
                    "risk_type": "source_check_failed",
                    "severity": SEVERITY_HIGH,
                    "reason": "溯源审查未通过，回答来源链条不完整。",
                    "suggestion": "请先修复 citation，再进行政治红线审查。",
                    "expert_focus": "请确认回答是否存在无来源结论或 citation 挂载错误。",
                }
            ],
            suggestion="请先修复 citation，再进行政治红线审查。",
            reviewer="研究生或项目组员先初标，赵老师抽样校准。",
            priority="high",
            stage="student_initial_label",
        )

    if source_status == "warning":
        _add_issue(
            issues,
            risk_types,
            review_items,
            "source_check_warning",
            "溯源审查存在 warning，需要人工复核来源完整性。",
            SEVERITY_MEDIUM,
            "请核对 citation.page、citation.section 与回答内容是否一致。",
            "请专家或研究生确认引用证据是否足以支撑回答。",
        )

    if "仅依据当前检索到的证据" not in answer:
        _add_issue(
            issues,
            risk_types,
            review_items,
            "missing_scope_statement",
            "回答缺少证据边界说明，可能让使用者误以为结论已经完全定稿。",
            SEVERITY_MEDIUM,
            "补充“仅依据当前检索证据生成”的限定语。",
            "请专家判断该回答是否容易被误解为无条件定论。",
        )

    absolute_claims = _contains_any(answer, ABSOLUTE_CLAIM_PHRASES)
    if absolute_claims:
        _add_issue(
            issues,
            risk_types,
            review_items,
            "unsupported_absolute_claim",
            f"回答出现较绝对的表述：{absolute_claims}。需要确认是否超出材料。",
            SEVERITY_HIGH,
            "删除或弱化绝对化表述，并补充证据边界。",
            "请专家确认这些绝对化表述是否符合教材和政治表达口径。",
        )

    context_terms = _contains_any(answer, HISTORICAL_CONTEXT_TERMS)
    if context_terms:
        _add_issue(
            issues,
            risk_types,
            review_items,
            "historical_context_needs_review",
            f"回答涉及需要谨慎处理的历史语境：{context_terms}。建议专家抽样复核。",
            SEVERITY_MEDIUM,
            "补充历史阶段、对象和材料依据，避免脱离语境概括。",
            "请专家确认历史语境和表述边界是否稳妥。",
        )

    status = WARNING_STATUS if issues else PASS_STATUS
    return _build_result(
        status=status,
        risk_types=risk_types,
        issues=issues,
        review_items=review_items,
        suggestion="建议保留研究生初标与赵老师抽样校准机制。",
        reviewer="低风险样例由研究生或组员初标，高风险和争议样例交赵老师校准。",
        priority="normal" if status == PASS_STATUS else "medium",
    )
