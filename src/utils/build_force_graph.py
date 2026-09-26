import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graph.graph_store import (
    build_adjacency,
    build_edge_lookup,
    build_relation_lookup,
    find_entity_paths,
)


DEFAULT_TRIPLES = REPO_ROOT / "data" / "graph" / "triples_demo.jsonl"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "graph" / "force_graph.json"
DEFAULT_CHUNKS = (
    REPO_ROOT / "data" / "processed" / "text_chunks_sizheng_v1.jsonl",
    REPO_ROOT / "data" / "processed" / "text_chunks_sizheng_v2.jsonl",
)

EVENT_SUFFIXES = ("革命", "会议", "运动", "长征", "战争", "起义", "会师")
DOCUMENT_MARKERS = ("《", "决议", "提纲", "通令", "指示", "纲领")
ORGANIZATION_TERMS = (
    "党", "军", "工会", "小组", "中央局", "宣传部", "教育部", "学校", "大学",
)
PLACE_TERMS = ("延安", "陕北", "陕甘宁边区")
TIME_TERMS = ("年", "月", "日")
PERSONS = {"毛泽东", "张闻天", "刘少奇", "刘伯承", "小叶丹", "陈望道", "陈独秀", "李达"}
DEMO_PATH_SPECS = (
    {
        "id": "demo_zhangwentian_propaganda_outline",
        "question": "张闻天起草的《党的宣传鼓动工作提纲》为什么重要？",
        "seed_entities": ["张闻天"],
        "target_entities": ["党的宣传教育工作系统化、规范化"],
        "max_hops": 2,
    },
)


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def infer_node_type(label: str) -> str:
    if label in PERSONS:
        return "person"
    if label in PLACE_TERMS:
        return "place"
    if any(marker in label for marker in DOCUMENT_MARKERS):
        return "document"
    if any(term in label for term in TIME_TERMS) and any(char.isdigit() for char in label):
        return "time"
    # 事件优先于组织识别，避免“新式整军运动”因包含“军”被误分为组织。
    if label.endswith(EVENT_SUFFIXES):
        return "event"
    if any(term in label for term in ORGANIZATION_TERMS):
        return "organization"
    return "concept"


def build_display_paths(triples: list[dict], chunks: dict[str, dict]) -> list[dict]:
    adjacency = build_adjacency(triples)
    relation_lookup = build_relation_lookup(triples)
    edge_lookup = build_edge_lookup(triples)
    display_paths: list[dict] = []

    for spec in DEMO_PATH_SPECS:
        paths = find_entity_paths(
            spec["seed_entities"],
            spec["target_entities"],
            adjacency,
            relation_lookup,
            max_hops=spec["max_hops"],
            limit=1,
            edge_lookup=edge_lookup,
        )
        if not paths:
            raise ValueError(f"demo path cannot be resolved from triples: {spec['id']}")

        path = paths[0]
        chunk_ids = path["source_chunk_ids"]
        missing_chunk_ids = [chunk_id for chunk_id in chunk_ids if chunk_id not in chunks]
        if missing_chunk_ids:
            raise ValueError(
                f"demo path references missing chunks: {spec['id']} -> {missing_chunk_ids}"
            )

        display_paths.append(
            {
                "id": spec["id"],
                "question": spec["question"],
                "seed_entities": list(spec["seed_entities"]),
                "hops": path["hops"],
                "nodes": path["path"],
                "relations": path["relations"],
                "source_chunk_ids": chunk_ids,
                "path_text": path["path_text"],
                "evidence_chunks": [
                    {
                        "id": chunk_id,
                        "title": chunks[chunk_id]["title"],
                        "citation": chunks[chunk_id].get("citation", {}),
                        "text": chunks[chunk_id]["text"],
                    }
                    for chunk_id in chunk_ids
                ],
            }
        )

    return display_paths


def build_payload(triples: list[dict], chunks: dict[str, dict]) -> dict:
    node_chunks: dict[str, list[str]] = defaultdict(list)
    degrees: dict[str, int] = defaultdict(int)
    edges: list[dict] = []

    for index, triple in enumerate(triples, start=1):
        head, tail = triple["head"], triple["tail"]
        chunk_ids = list(triple["source_chunk_ids"])
        degrees[head] += 1
        degrees[tail] += 1
        for label in (head, tail):
            for chunk_id in chunk_ids:
                if chunk_id not in node_chunks[label]:
                    node_chunks[label].append(chunk_id)
        edges.append(
            {
                "id": f"edge_{index:03d}",
                "source": head,
                "target": tail,
                "relation": triple["relation"],
                "source_chunk_ids": chunk_ids,
                "directed": True,
                "display_label": triple["relation"],
            }
        )

    nodes = [
        {
            "id": label,
            "label": label,
            "type": infer_node_type(label),
            "source_chunk_ids": node_chunks[label],
            "degree": degrees[label],
        }
        for label in sorted(node_chunks)
    ]

    display_paths = build_display_paths(triples, chunks)

    return {
        "schema_version": "1.0",
        "directed": True,
        "node_type_values": ["person", "organization", "event", "place", "document", "time", "concept"],
        "nodes": nodes,
        "edges": edges,
        "display_paths": display_paths,
        "stats": {"nodes": len(nodes), "edges": len(edges), "evidence_chunks": len(chunks)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build frontend-ready force graph data")
    parser.add_argument("--triples", type=Path, default=DEFAULT_TRIPLES)
    parser.add_argument("--chunks", nargs="+", type=Path, default=list(DEFAULT_CHUNKS))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    triples = load_jsonl(args.triples)
    chunks = {
        chunk["id"]: chunk
        for chunk_path in args.chunks
        for chunk in load_jsonl(chunk_path)
    }
    payload = build_payload(triples, chunks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Force LF so Windows regeneration does not create a whole-file CRLF diff.
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"force graph written: {args.output} nodes={len(payload['nodes'])} edges={len(payload['edges'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
