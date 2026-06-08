import json

import pytest

from src.graph.graph_store import (
    build_adjacency,
    build_relation_lookup,
    expand_entities,
    find_entity_paths,
    load_triples,
)


def _write_jsonl(path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
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
