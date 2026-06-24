QUERY_SECTION_TERMS = (
    "长征",
    "新式整军",
    "宣传工作",
    "张闻天",
    "抗日战争",
    "党的一大",
    "马克思主义",
    "人民解放军",
)


def _split_section(section: str) -> list[str]:
    return [
        segment.strip()
        for segment in str(section).replace("／", "/").split("/")
        if segment.strip()
    ]


def _section_term_boost(query: str, hit: dict) -> float:
    citation = hit.get("citation") or {}
    section_segments = _split_section(citation.get("section", ""))
    title = str(hit.get("title", ""))
    text = str(hit.get("text", ""))
    boost = 0.0

    for term in QUERY_SECTION_TERMS:
        if term not in query:
            continue

        term_indices = [
            index
            for index, segment in enumerate(section_segments)
            if term in segment
        ]
        if term in title:
            boost += 0.02
        if term in text:
            boost += 0.01
        if not term_indices:
            continue

        deepest_term_index = max(term_indices)
        boost += 0.01
        if term == "长征":
            competing_indices = [
                index
                for index, segment in enumerate(section_segments)
                if "反围剿" in segment or "反“围剿”" in segment
            ]
            if competing_indices and max(competing_indices) > deepest_term_index:
                boost -= 0.04
            else:
                boost += 0.04
        else:
            boost += 0.03

    return round(boost, 6)


def rerank_hits_by_query_terms(query: str, hits: list[dict]) -> list[dict]:
    reranked = []
    for original_rank, hit in enumerate(hits):
        base_score = float(hit.get("vector_score") or 0.0)
        boost = _section_term_boost(query, hit)
        item = dict(hit)
        item["base_vector_score"] = round(base_score, 6)
        item["rerank_boost"] = boost
        item["vector_score"] = round(base_score + boost, 6)
        item["_original_rank"] = original_rank
        reranked.append(item)

    reranked.sort(
        key=lambda item: (-float(item["vector_score"]), int(item["_original_rank"]))
    )
    for item in reranked:
        item.pop("_original_rank", None)
    return reranked
