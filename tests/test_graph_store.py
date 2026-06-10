import json
from pathlib import Path

import pytest

from src.graph.graph_store import (
    build_adjacency,
    build_relation_lookup,
    expand_entities,
    find_entity_paths,
    load_triples,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CHUNKS_PATH = REPO_ROOT / "data" / "processed" / "text_chunks_demo.jsonl"
DEMO_TRIPLES_PATH = REPO_ROOT / "data" / "graph" / "triples_demo.jsonl"


def _write_jsonl(path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )


def _load_chunks_by_id() -> dict[str, dict]:
    chunks: dict[str, dict] = {}
    with DEMO_CHUNKS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                chunks[item["id"]] = item
    return chunks


def _chunk_evidence_text(chunk: dict) -> str:
    citation = chunk.get("citation", {})
    return " ".join(
        [
            chunk.get("title", ""),
            chunk.get("text", ""),
            citation.get("section", ""),
            " ".join(chunk.get("entities", [])),
            " ".join(chunk.get("tags", [])),
        ]
    )


def test_load_triples_reads_jsonl(tmp_path):
    triples_path = tmp_path / "triples_demo.jsonl"
    _write_jsonl(
        triples_path,
        [
            {
                "head": "思想政治教育",
                "relation": "传播",
                "tail": "马克思主义",
                "source_chunk_ids": ["chunk_001"],
            }
        ],
    )

    triples = load_triples(triples_path)

    assert triples == [
        {
            "head": "思想政治教育",
            "relation": "传播",
            "tail": "马克思主义",
            "source_chunk_ids": ["chunk_001"],
        }
    ]


def test_load_triples_rejects_missing_required_fields(tmp_path):
    triples_path = tmp_path / "bad_triples.jsonl"
    _write_jsonl(
        triples_path,
        [{"head": "思想政治教育", "relation": "传播", "tail": "马克思主义"}],
    )

    with pytest.raises(ValueError, match="source_chunk_ids"):
        load_triples(triples_path)


def test_load_triples_rejects_empty_or_invalid_source_chunk_ids(tmp_path):
    triples_path = tmp_path / "bad_triples.jsonl"
    _write_jsonl(
        triples_path,
        [
            {
                "head": "思想政治教育",
                "relation": "传播",
                "tail": "马克思主义",
                "source_chunk_ids": [],
            }
        ],
    )

    with pytest.raises(ValueError, match="source_chunk_ids"):
        load_triples(triples_path)


def test_demo_triples_are_grounded_in_real_chunks():
    chunks = _load_chunks_by_id()
    triples = load_triples(DEMO_TRIPLES_PATH)

    for index, triple in enumerate(triples, start=1):
        assert triple["source_chunk_ids"], f"line {index} has no source chunk ids"
        for chunk_id in triple["source_chunk_ids"]:
            assert chunk_id in chunks, f"line {index} uses unknown chunk id {chunk_id}"
            evidence = _chunk_evidence_text(chunks[chunk_id])
            assert triple["head"] in evidence, f"line {index} head not grounded: {triple}"
            assert triple["tail"] in evidence, f"line {index} tail not grounded: {triple}"


def test_demo_triples_cover_high_value_graphsim_queries():
    triples = load_triples(DEMO_TRIPLES_PATH)
    edges = {(triple["head"], triple["relation"], triple["tail"]) for triple in triples}

    assert ("党的一大", "确定", "思想政治教育的根本目的") in edges
    assert ("马克思主义", "在中国的传播成为", "滔滔滚滚的潮流") in edges
    assert ("中共中央", "成立", "干部教育部") in edges
    assert ("张闻天", "任部长", "干部教育部") in edges
    assert ("国民党被俘、起义部队", "服从", "人民解放军的指挥、调动") in edges


def test_build_adjacency_uses_bidirectional_edges_by_default():
    triples = [
        {
            "head": "思想政治教育",
            "relation": "传播",
            "tail": "马克思主义",
            "source_chunk_ids": ["chunk_001"],
        },
        {
            "head": "思想政治教育",
            "relation": "服务于",
            "tail": "群众动员",
            "source_chunk_ids": ["chunk_002"],
        },
    ]

    adjacency = build_adjacency(triples)

    assert adjacency["思想政治教育"] == ["马克思主义", "群众动员"]
    assert adjacency["马克思主义"] == ["思想政治教育"]
    assert adjacency["群众动员"] == ["思想政治教育"]


def test_expand_entities_returns_seed_one_hop_and_two_hop_entities():
    adjacency = {
        "思想政治教育": ["马克思主义", "群众动员"],
        "马克思主义": ["中国共产党"],
        "群众动员": ["宣传工作"],
        "中国共产党": ["新民主主义革命"],
    }

    expanded = expand_entities(["思想政治教育"], adjacency, max_hops=2)

    assert expanded == [
        "思想政治教育",
        "马克思主义",
        "群众动员",
        "中国共产党",
        "宣传工作",
    ]
    assert "新民主主义革命" not in expanded


def test_expand_entities_can_limit_to_one_hop():
    adjacency = {
        "延安": ["整风运动"],
        "整风运动": ["思想政治教育"],
    }

    expanded = expand_entities(["延安"], adjacency, max_hops=1)

    assert expanded == ["延安", "整风运动"]
    assert "思想政治教育" not in expanded


def test_find_entity_paths_returns_explainable_one_hop_path():
    triples = [
        {
            "head": "张闻天",
            "relation": "起草",
            "tail": "党的宣传鼓动工作提纲",
            "source_chunk_ids": ["chunk_szzjys_demo_025"],
        }
    ]
    adjacency = build_adjacency(triples)
    relation_lookup = build_relation_lookup(triples)

    paths = find_entity_paths(
        ["张闻天"],
        ["党的宣传鼓动工作提纲"],
        adjacency,
        relation_lookup,
    )

    assert paths == [
        {
            "from": "张闻天",
            "to": "党的宣传鼓动工作提纲",
            "hops": 1,
            "path": ["张闻天", "党的宣传鼓动工作提纲"],
            "relations": ["起草"],
            "path_text": "张闻天 --起草--> 党的宣传鼓动工作提纲",
        }
    ]


def test_find_entity_paths_returns_two_hop_path():
    triples = [
        {
            "head": "抗日战争",
            "relation": "需要",
            "tail": "干部教育",
            "source_chunk_ids": ["chunk_szzjys_demo_022"],
        },
        {
            "head": "干部教育",
            "relation": "服务于",
            "tail": "抗战胜利",
            "source_chunk_ids": ["chunk_szzjys_demo_022"],
        },
    ]
    adjacency = build_adjacency(triples)
    relation_lookup = build_relation_lookup(triples)

    paths = find_entity_paths(
        ["抗日战争"],
        ["抗战胜利"],
        adjacency,
        relation_lookup,
    )

    assert paths[0]["path"] == ["抗日战争", "干部教育", "抗战胜利"]
    assert paths[0]["relations"] == ["需要", "服务于"]
