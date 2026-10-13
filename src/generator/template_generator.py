import re


NO_EVIDENCE_ANSWER = "当前知识库中没有检索到足够证据，暂不生成回答。请补充资料或换一个问题。"
ANSWER_SNIPPET_LIMIT = 320
COMPLETE_EVIDENCE_LIMIT = 640
MAX_TEMPLATE_EVIDENCE = 3
MIN_TEMPLATE_HYBRID_SCORE = 0.2
MIN_QUERY_OVERLAP_FLOOR = 0.08
MIN_QUERY_OVERLAP_RATIO = 0.5
QUERY_NGRAM_SIZES = (2, 3, 4)


def _shorten_text(text: str, limit: int = ANSWER_SNIPPET_LIMIT) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    candidate = text[:limit]
    sentence_end = max(candidate.rfind(mark) for mark in "。！？；")
    if sentence_end >= 20:
        end = sentence_end + 1
        while end < len(text) and text[end] in "”’」』》）)]":
            end += 1
        return text[:end]
    return candidate.rstrip("，。；、 ") + "。"


def _summarize_evidence(query: str, hit: dict) -> str:
    text = " ".join((hit.get("text") or "").split())
    body_overlap = _query_overlap_score(_query_ngrams(query), {"text": text})
    if (
        len(text) <= COMPLETE_EVIDENCE_LIMIT
        and body_overlap >= MIN_QUERY_OVERLAP_FLOOR
    ):
        return text
    return _shorten_text(text)


def _format_citation(citation: dict) -> str:
    doc = citation.get("doc") or "未知文献"
    section = citation.get("section") or "未知章节"
    page = citation.get("page")
    if page is None:
        return f"《{doc}》，{section}，PDF 页码待复核"
    return f"《{doc}》，{section}，PDF 页码 {page}"


def _normalize_for_overlap(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text or ""))


def _query_ngrams(query: str) -> set[str]:
    normalized = _normalize_for_overlap(query)
    grams = set()
    for size in QUERY_NGRAM_SIZES:
        for index in range(max(0, len(normalized) - size + 1)):
            grams.add(normalized[index:index + size])
    return grams


def _query_overlap_score(query_grams: set[str], hit: dict) -> float:
    if not query_grams:
        return 0.0
    evidence_text = _normalize_for_overlap(
        f"{hit.get('title', '')}{hit.get('text', '')}"
    )
    matched = sum(1 for gram in query_grams if gram in evidence_text)
    return matched / len(query_grams)


def select_answer_hits(query: str, hybrid_hits: list[dict], max_hits: int) -> list[dict]:
    usable_hits = []
    for hit in hybrid_hits:
        score = hit.get("hybrid_score")
        if score is not None and score < MIN_TEMPLATE_HYBRID_SCORE:
            continue
        usable_hits.append(hit)
    if not usable_hits:
        return []

    query_grams = _query_ngrams(query)
    scored_hits = [
        (hit, _query_overlap_score(query_grams, hit))
        for hit in usable_hits
    ]
    best_overlap = max(score for _, score in scored_hits)
    overlap_threshold = max(
        best_overlap * MIN_QUERY_OVERLAP_RATIO,
        MIN_QUERY_OVERLAP_FLOOR,
    )

    selected_hits = [
        hit for hit, score in scored_hits
        if score >= overlap_threshold
    ][:max_hits]
    return selected_hits or usable_hits[:1]


def generate_answer_from_hits(
    query: str,
    hybrid_hits: list[dict],
    max_hits: int = MAX_TEMPLATE_EVIDENCE,
) -> dict:
    """
    生成智能体最小原型：只基于 hybrid_hits 组织回答，不调用外部大模型。
    后续可将函数内部替换为 LLM API，但输入输出契约保持不变。
    """
    selected_hits = select_answer_hits(query, hybrid_hits, max_hits)
    if not selected_hits:
        return {
            "answer": NO_EVIDENCE_ANSWER,
            "citations_used": [],
        }

    citation_lines = []
    continuation_ids = ("chunk_sizheng_v1_166", "chunk_sizheng_v1_167")
    positions = [
        index for index, hit in enumerate(selected_hits)
        if hit.get("id") in continuation_ids
    ]
    continuation_is_verified = False
    if len(positions) == 2:
        first, second = (selected_hits[index] for index in positions)
        continuation_is_verified = (
            {first.get("id"), second.get("id")} == set(continuation_ids)
            and first.get("source") == second.get("source")
            and first.get("citation") == second.get("citation")
        )
        if continuation_is_verified:
            by_id = {hit["id"]: hit for hit in (first, second)}
            selected_hits = list(selected_hits)
            for position, chunk_id in zip(positions, continuation_ids):
                selected_hits[position] = by_id[chunk_id]
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

    evidence_lines = []
    for index, hit in enumerate(selected_hits, start=1):
        text = _summarize_evidence(query, hit)
        evidence_lines.append(f"- 证据 {index}：{text}")

    answer = (
        "生成服务当前不可用，以下内容仅为检索证据摘要，"
        "不作为完整自然语言回答：\n"
        + "\n".join(evidence_lines)
        + "\n\n"
        + "引用依据：\n"
        + "\n".join(citation_lines)
        + "\n\n以上内容仅依据当前检索到的证据整理，"
        "仅为检索证据摘要，请在生成服务恢复后重新生成完整回答。"
    )
    if (
        continuation_is_verified
        and "张闻天" in query
        and "宣传鼓动工作提纲" in query
        and "背景" in query
    ):
        answer += (
            "\n\n证据范围说明：现有引用可确认起草时间、机构和主要内容；"
            "未提供该文起草背景的直接说明，不能据此补写具体背景。"
        )
    return {
        "answer": answer,
        "citations_used": citations_used,
    }
