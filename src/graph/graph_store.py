import json
from collections import defaultdict, deque
from pathlib import Path

from src.graph.graph_sim import calculate_graph_similarity


REQUIRED_TRIPLE_FIELDS = {"head", "relation", "tail", "source_chunk_ids"}


class GraphStore:
    """Small in-memory graph store for the demo triple dataset."""

    def __init__(self, triples: list[dict]):
        self.triples = triples
        self.adjacency: dict[str, list[dict]] = defaultdict(list)
        self._build_adjacency()

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "GraphStore":
        triples = []
        with Path(path).open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                triple = json.loads(line)
                missing_fields = REQUIRED_TRIPLE_FIELDS - triple.keys()
                if missing_fields:
                    missing = ", ".join(sorted(missing_fields))
                    raise ValueError(f"line {line_number} missing fields: {missing}")
                if not triple["source_chunk_ids"]:
                    raise ValueError(f"line {line_number} has no source_chunk_ids")
                triples.append(triple)
        return cls(triples)

    def _build_adjacency(self) -> None:
        for triple in self.triples:
            shared = {
                "relation": triple["relation"],
                "source_chunk_ids": tuple(triple["source_chunk_ids"]),
            }
            self.adjacency[triple["head"]].append(
                {**shared, "neighbor": triple["tail"], "direction": "out"}
            )
            self.adjacency[triple["tail"]].append(
                {**shared, "neighbor": triple["head"], "direction": "in"}
            )

    def neighbors(self, entity: str, max_hops: int = 1) -> list[dict]:
        """Return cycle-free paths starting at an entity, up to max_hops."""
        if max_hops < 1:
            raise ValueError("max_hops must be at least 1")

        results = []
        queue = deque([(entity, 0, (entity,), ())])
        while queue:
            current, hop, path, relations = queue.popleft()
            if hop >= max_hops:
                continue
            for edge in self.adjacency.get(current, []):
                neighbor = edge["neighbor"]
                if neighbor in path:
                    continue
                next_path = (*path, neighbor)
                next_relations = (*relations, edge["relation"])
                next_hop = hop + 1
                results.append(
                    {
                        "entity": neighbor,
                        "hop": next_hop,
                        "path": list(next_path),
                        "relations": list(next_relations),
                        "source_chunk_ids": list(edge["source_chunk_ids"]),
                    }
                )
                queue.append((neighbor, next_hop, next_path, next_relations))
        return results

    def search(
        self,
        query_entities: list[str],
        top_k: int = 3,
        max_hops: int = 2,
    ) -> list[dict]:
        """Rank source chunks reached by 1-hop or 2-hop graph paths."""
        unique_query_entities = list(dict.fromkeys(query_entities))
        if not unique_query_entities or top_k <= 0:
            return []

        candidates: dict[str, dict] = {}
        for query_entity in unique_query_entities:
            for path_hit in self.neighbors(query_entity, max_hops=max_hops):
                for chunk_id in path_hit["source_chunk_ids"]:
                    candidate = candidates.setdefault(
                        chunk_id,
                        {
                            "matched_query_entities": set(),
                            "min_hop": path_hit["hop"],
                            "path_count": 0,
                            "related_entities": set(),
                            "relations": set(),
                            "paths": [],
                        },
                    )
                    candidate["matched_query_entities"].add(query_entity)
                    candidate["min_hop"] = min(candidate["min_hop"], path_hit["hop"])
                    candidate["path_count"] += 1
                    candidate["related_entities"].update(path_hit["path"])
                    candidate["relations"].update(path_hit["relations"])
                    candidate["paths"].append(path_hit["path"])

        graph_hits = []
        for chunk_id, candidate in candidates.items():
            graph_hits.append(
                {
                    "id": chunk_id,
                    "related_entities": sorted(candidate["related_entities"]),
                    "relations": sorted(candidate["relations"]),
                    "paths": candidate["paths"],
                    "min_hop": candidate["min_hop"],
                    "graph_score": calculate_graph_similarity(
                        query_entity_count=len(unique_query_entities),
                        matched_query_entities=len(candidate["matched_query_entities"]),
                        min_hop=candidate["min_hop"],
                        path_count=candidate["path_count"],
                    ),
                }
            )

        graph_hits.sort(key=lambda hit: (-hit["graph_score"], hit["min_hop"], hit["id"]))
        return graph_hits[:top_k]
