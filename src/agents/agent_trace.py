SOURCE_BLOCK_STATUSES = {"no_evidence", "fail"}


def build_agent_trace(
    *,
    query_entities: list[str],
    hybrid_hits: list[dict],
    generated: dict,
    source_check: dict,
    policy_check: dict,
) -> list[dict]:
    return [
        {
            "agent": "retrieval_stage",
            "role": "证据检索中枢",
            "status": "pass" if hybrid_hits else "no_evidence",
            "summary": {
                "query_entities_count": len(query_entities),
                "hybrid_hits_count": len(hybrid_hits),
            },
        },
        {
            "agent": "generator",
            "role": "生成智能体",
            "status": "pass" if generated.get("answer") else "no_answer",
            "summary": {
                "generator_mode": generated.get("generator_mode"),
                "citations_used_count": len(generated.get("citations_used", [])),
            },
        },
        {
            "agent": "source_reviewer",
            "role": "溯源审查智能体",
            "status": source_check.get("status"),
            "summary": {
                "checked_citation_count": source_check.get("checked_citation_count", 0),
                "issue_count": len(source_check.get("issues", [])),
            },
        },
        {
            "agent": "policy_reviewer",
            "role": "政治红线审查智能体",
            "status": policy_check.get("status"),
            "summary": {
                "review_required": policy_check.get("review_required"),
                "max_severity": policy_check.get("max_severity"),
                "risk_types": policy_check.get("risk_types", []),
            },
        },
    ]


def build_final_decision(source_check: dict, policy_check: dict) -> dict:
    if source_check.get("status") in SOURCE_BLOCK_STATUSES:
        return {
            "status": "blocked",
            "can_output": False,
            "review_required": True,
            "reason": "缺少可用证据或溯源检查未通过。",
        }

    if policy_check.get("review_required"):
        return {
            "status": "needs_review",
            "can_output": False,
            "review_required": True,
            "reason": "政治红线初筛提示需要人工复核。",
        }

    return {
        "status": "approved",
        "can_output": True,
        "review_required": False,
        "reason": "溯源检查和政治红线初筛均通过。",
    }
