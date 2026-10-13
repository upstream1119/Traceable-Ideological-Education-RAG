import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.retriever.hybrid_retriever import extract_query_entities, retrieve_graph


OUTPUT_PATH = REPO_ROOT / "reports" / "graphsim_integration_samples.json"
CHUNK_PATHS = (
    REPO_ROOT / "data" / "processed" / "text_chunks_sizheng_v1.jsonl",
    REPO_ROOT / "data" / "processed" / "text_chunks_sizheng_v2.jsonl",
)
SPECS = (
    {
        "id": "one_hop_mao_names_rectification",
        "query": "毛泽东如何命名新式整军运动？",
        "nodes": ["毛泽东", "新式整军运动"],
    },
    {
        "id": "two_hop_pla_awareness",
        "query": "中国人民解放军开展新式整军运动提高了什么？",
        "nodes": ["中国人民解放军", "新式整军运动", "干部战士的政治觉悟"],
    },
    {
        "id": "empty_path_unknown_entities",
        "query": "未知实体与不存在事件的关系？",
        "nodes": None,
    },
)


def _load_chunks() -> dict[str, dict]:
    chunks = {}
    for path in CHUNK_PATHS:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunk = json.loads(line)
                chunks[chunk["id"]] = chunk
    return chunks


def build_samples() -> dict:
    chunks = _load_chunks()
    samples = []
    for spec in SPECS:
        entities = extract_query_entities(spec["query"])
        hits = retrieve_graph(entities)
        selected_path = None
        selected_hit = None
        if spec["nodes"] is not None:
            selected_hit, selected_path = next(
                (hit, path)
                for hit in hits
                for path in hit.get("graph_paths", [])
                if path["path"] == spec["nodes"]
            )
        chunk_ids = selected_path["source_chunk_ids"] if selected_path else []
        samples.append(
            {
                "id": spec["id"],
                "query": spec["query"],
                "query_entities": entities,
                "top_3_graph_hit_ids": [hit["id"] for hit in hits],
                "graph_hits": [] if selected_hit is None else [{
                    "id": selected_hit["id"],
                    "graph_score": selected_hit["graph_score"],
                    "related_entities": selected_hit["related_entities"],
                    "graph_paths": [selected_path],
                }],
                "evidence_chunks": [
                    {
                        "id": chunk_id,
                        "title": chunks[chunk_id]["title"],
                        "text": chunks[chunk_id]["text"],
                        "citation": chunks[chunk_id]["citation"],
                    }
                    for chunk_id in chunk_ids
                ],
            }
        )
    return {
        "schema_version": "1.0",
        "source_triples": "data/graph/triples_demo.jsonl",
        "source_chunks": [str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in CHUNK_PATHS],
        "reproduce": "python scripts/export_graphsim_integration_samples.py",
        "samples": samples,
    }


def main() -> int:
    OUTPUT_PATH.write_text(
        json.dumps(build_samples(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"integration samples written: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

