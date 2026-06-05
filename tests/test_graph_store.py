import json
from pathlib import Path

from src.graph.graph_sim import calculate_graph_similarity
from src.graph.graph_store import GraphStore, REQUIRED_TRIPLE_FIELDS
from src.retriever.hybrid_retriever import retrieve_graph


REPO_ROOT = Path(__file__).resolve().parents[1]
TRIPLES_PATH = REPO_ROOT / "data" / "graph" / "triples_demo.jsonl"
CHUNKS_PATH = REPO_ROOT / "data" / "processed" / "text_chunks_demo.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_demo_triples_have_required_fields_and_real_source_chunks():
    triples = _load_jsonl(TRIPLES_PATH)
    chunk_ids = {chunk["id"] for chunk in _load_jsonl(CHUNKS_PATH)}

    assert 20 <= len(triples) <= 40
    for triple in triples:
        assert REQUIRED_TRIPLE_FIELDS.issubset(triple)
        assert triple["head"]
        assert triple["relation"]
        assert triple["tail"]
        assert triple["source_chunk_ids"]
        assert set(triple["source_chunk_ids"]).issubset(chunk_ids)


def test_graph_store_builds_bidirectional_one_hop_adjacency():
    store = GraphStore.from_jsonl(TRIPLES_PATH)

    forward = store.neighbors("新式整军运动", max_hops=1)
    reverse = store.neighbors("人民解放军", max_hops=1)

    assert any(hit["entity"] == "人民解放军" for hit in forward)
    assert any(hit["entity"] == "新式整军运动" for hit in reverse)


def test_graph_store_supports_two_hop_paths():
    store = GraphStore.from_jsonl(TRIPLES_PATH)

    hits = store.neighbors("中国共产党", max_hops=2)

    assert any(hit["entity"] == "红军" and hit["hop"] == 2 for hit in hits)


def test_graph_similarity_rewards_coverage_and_short_paths():
    direct_full_match = calculate_graph_similarity(2, 2, 1, 1)
    two_hop_full_match = calculate_graph_similarity(2, 2, 2, 1)
    direct_partial_match = calculate_graph_similarity(2, 1, 1, 1)

    assert direct_full_match > two_hop_full_match
    assert direct_full_match > direct_partial_match
    assert 0 < direct_partial_match <= 0.99


def test_graph_search_adds_value_for_six_demo_queries():
    store = GraphStore.from_jsonl(TRIPLES_PATH)
    cases = [
        (["思想政治教育"], "chunk_szzjys_demo_001"),
        (["三湾改编"], "chunk_szzjys_demo_012"),
        (["红军"], "chunk_szzjys_demo_016"),
        (["宣传工作"], "chunk_szzjys_demo_025"),
        (["新式整军运动", "人民解放军"], "chunk_szzjys_demo_033"),
        (["中国共产党", "马克思主义"], "chunk_szzjys_demo_006"),
    ]

    for query_entities, expected_chunk_id in cases:
        hits = store.search(query_entities, top_k=3, max_hops=2)
        assert hits
        assert expected_chunk_id in {hit["id"] for hit in hits}
        assert all(hit["paths"] for hit in hits)
        assert all(hit["graph_score"] > 0 for hit in hits)


def test_retrieve_graph_uses_demo_triple_store():
    hits = retrieve_graph(["新式整军运动", "人民解放军"])

    assert hits[0]["id"] == "chunk_szzjys_demo_033"
    assert "诉苦和三查" in hits[0]["related_entities"]
    assert hits[0]["min_hop"] == 1
