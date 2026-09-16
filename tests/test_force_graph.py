import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORCE_GRAPH_PATH = REPO_ROOT / "data" / "graph" / "force_graph.json"


def test_force_graph_is_frontend_ready_and_evidence_grounded():
    payload = json.loads(FORCE_GRAPH_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.0"
    assert payload["directed"] is True
    assert payload["stats"]["nodes"] == len(payload["nodes"])
    assert payload["stats"]["edges"] == len(payload["edges"]) == 100
    assert all(node["id"] and node["type"] and node["source_chunk_ids"] for node in payload["nodes"])
    assert all(edge["source"] and edge["target"] and edge["source_chunk_ids"] for edge in payload["edges"])

    demo = payload["display_paths"][0]
    assert demo["hops"] == 2
    assert demo["source_chunk_ids"] == ["chunk_sizheng_v1_166", "chunk_sizheng_v1_167"]
    assert len(demo["evidence_chunks"]) == 2
