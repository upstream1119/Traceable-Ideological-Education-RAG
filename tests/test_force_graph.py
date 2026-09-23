import json
import subprocess
import sys
from pathlib import Path

from src.utils.build_force_graph import build_display_paths, infer_node_type


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

    edge_keys = {
        (edge["source"], edge["relation"], edge["target"]): edge
        for edge in payload["edges"]
    }
    for display_path in payload["display_paths"]:
        assert display_path["hops"] == len(display_path["relations"])
        assert len(display_path["nodes"]) == display_path["hops"] + 1
        evidence_ids = {chunk["id"] for chunk in display_path["evidence_chunks"]}
        assert evidence_ids == set(display_path["source_chunk_ids"])
        for source, relation, target in zip(
            display_path["nodes"],
            display_path["relations"],
            display_path["nodes"][1:],
        ):
            edge = edge_keys[(source, relation, target)]
            assert set(edge["source_chunk_ids"]).issubset(
                display_path["source_chunk_ids"]
            )

    demo = payload["display_paths"][0]
    assert demo["hops"] == 2
    assert demo["source_chunk_ids"] == ["chunk_sizheng_v1_166", "chunk_sizheng_v1_167"]


def test_event_type_takes_precedence_over_organization_term_matches():
    assert infer_node_type("新式整军运动") == "event"
    assert infer_node_type("诉苦与三查运动") == "event"
    assert infer_node_type("中国人民解放军") == "organization"


def test_force_graph_is_written_with_lf_only(tmp_path):
    output_path = tmp_path / "force_graph.json"
    subprocess.run(
        [sys.executable, "src/utils/build_force_graph.py", "--output", str(output_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert b"\r\n" not in output_path.read_bytes()


def test_display_path_is_computed_from_triples_and_fails_when_edge_is_missing():
    chunks = {
        "chunk_1": {"id": "chunk_1", "title": "第一段", "text": "甲到乙"},
        "chunk_2": {"id": "chunk_2", "title": "第二段", "text": "乙到丙"},
    }
    triples = [
        {"head": "张闻天", "relation": "起草", "tail": "《党的宣传鼓动工作提纲》", "source_chunk_ids": ["chunk_1"]},
        {"head": "《党的宣传鼓动工作提纲》", "relation": "标志着", "tail": "党的宣传教育工作系统化、规范化", "source_chunk_ids": ["chunk_2"]},
    ]

    path = build_display_paths(triples, chunks)[0]
    assert path["nodes"] == ["张闻天", "《党的宣传鼓动工作提纲》", "党的宣传教育工作系统化、规范化"]
    assert path["source_chunk_ids"] == ["chunk_1", "chunk_2"]

    triples.pop()
    try:
        build_display_paths(triples, chunks)
    except ValueError as exc:
        assert "demo path cannot be resolved" in str(exc)
    else:
        raise AssertionError("missing demo edge must fail graph generation")
