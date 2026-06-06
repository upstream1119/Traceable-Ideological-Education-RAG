NO_EVIDENCE_STATUS = "no_evidence"
PASS_STATUS = "pass"
WARNING_STATUS = "warning"
FAIL_STATUS = "fail"


def check_answer_sources(answer: str, citations_used: list[dict]) -> dict:
    """
    溯源审查智能体最小原型：检查生成回答是否有 citation 支撑。
    当前只做规则检查，不调用外部大模型。
    """
    if not citations_used:
        return {
            "status": NO_EVIDENCE_STATUS,
            "issues": ["当前回答没有可用 citation，系统应保持不生成或提示证据不足。"],
            "checked_citation_count": 0,
        }

    issues = []
    has_source_marker = "来源：" in answer or "PDF 页码" in answer
    if not has_source_marker:
        issues.append("answer 中没有明显来源说明。")

    for citation_item in citations_used:
        citation = citation_item.get("citation", {})
        hit_id = citation_item.get("id") or "未知证据"
        if not citation.get("doc"):
            issues.append(f"{hit_id} 缺少 citation.doc。")
        if not citation.get("section"):
            issues.append(f"{hit_id} 缺少 citation.section。")
        if citation.get("page") is None:
            issues.append(f"{hit_id} 的 citation.page 为空，需要后续页码复核。")

    status = PASS_STATUS
    if issues:
        status = WARNING_STATUS
    if any("缺少 citation.doc" in issue or "缺少 citation.section" in issue for issue in issues):
        status = FAIL_STATUS

    return {
        "status": status,
        "issues": issues,
        "checked_citation_count": len(citations_used),
    }
