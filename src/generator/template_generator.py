NO_EVIDENCE_ANSWER = "当前知识库中没有检索到足够证据，暂不生成回答。请补充资料或换一个问题。"
ANSWER_SNIPPET_LIMIT = 180


def _shorten_text(text: str, limit: int = ANSWER_SNIPPET_LIMIT) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    candidate = text[:limit]
    sentence_end = max(candidate.rfind(mark) for mark in "。！？；")
    if sentence_end >= 20:
        return candidate[:sentence_end + 1]
    return candidate.rstrip("，。；、 ") + "。"


def _format_citation(citation: dict) -> str:
    doc = citation.get("doc") or "未知文献"
    section = citation.get("section") or "未知章节"
    page = citation.get("page")
    if page is None:
        return f"《{doc}》，{section}，PDF 页码待复核"
    return f"《{doc}》，{section}，PDF 页码 {page}"


def generate_answer_from_hits(query: str, hybrid_hits: list[dict], max_hits: int = 1) -> dict:
    """
    生成智能体最小原型：只基于 hybrid_hits 组织回答，不调用外部大模型。
    后续可将函数内部替换为 LLM API，但输入输出契约保持不变。
    """
    selected_hits = hybrid_hits[:max_hits]
    if not selected_hits:
        return {
            "answer": NO_EVIDENCE_ANSWER,
            "citations_used": [],
        }

    citation_lines = []
    citations_used = []
    for index, hit in enumerate(selected_hits, start=1):
        citation = hit.get("citation", {})
        citation_text = _format_citation(citation)
        citation_lines.append(
            f"{index}. {hit.get('title', '未命名证据')}：来源：{citation_text}"
        )
        citations_used.append(
            {
                "id": hit.get("id"),
                "title": hit.get("title"),
                "source": hit.get("source"),
                "citation": citation,
                "hybrid_score": hit.get("hybrid_score"),
            }
        )

    top_hit = selected_hits[0]
    top_text = _shorten_text(top_hit.get("text", ""))

    answer = (
        f"针对问题“{query}”，根据当前检索到的资料，可以形成如下阶段性回答："
        f"{top_text}"
        "\n\n"
        "引用依据：\n"
        + "\n".join(citation_lines)
        + "\n\n以上回答仅依据当前检索到的证据生成，后续仍需要溯源审查智能体和政治红线审查智能体进一步复核。"
    )
    return {
        "answer": answer,
        "citations_used": citations_used,
    }
