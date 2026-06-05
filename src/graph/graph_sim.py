def calculate_graph_similarity(
    query_entity_count: int,
    matched_query_entities: int,
    min_hop: int,
    path_count: int,
) -> float:
    """Score a graph evidence chunk by entity coverage, distance, and path support."""
    if query_entity_count <= 0 or matched_query_entities <= 0 or min_hop <= 0:
        return 0.0

    coverage_score = min(matched_query_entities / query_entity_count, 1.0)
    hop_score = 1.0 if min_hop == 1 else 0.65
    path_score = min(path_count / 3, 1.0)
    score = coverage_score * 0.65 + hop_score * 0.25 + path_score * 0.1
    return min(round(score, 3), 0.99)
