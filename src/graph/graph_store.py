import json
from pathlib import Path


REQUIRED_TRIPLE_FIELDS = {"head", "relation", "tail", "source_chunk_ids"}


def load_triples(path: str | Path) -> list[dict]:
    triples_path = Path(path)
    if not triples_path.exists():
        return []

    triples: list[dict] = []
    with triples_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            triple = json.loads(line)
            missing_fields = REQUIRED_TRIPLE_FIELDS - set(triple)
            if missing_fields:
                missing = ", ".join(sorted(missing_fields))
                raise ValueError(f"line {line_number} missing fields: {missing}")
            triples.append(triple)
    return triples


def build_adjacency(triples: list[dict], bidirectional: bool = True) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {}

    for triple in triples:
        head = triple["head"]
        tail = triple["tail"]
        _append_unique(adjacency, head, tail)
        if bidirectional:
            _append_unique(adjacency, tail, head)

    return adjacency


def expand_entities(
    seed_entities: list[str],
    adjacency: dict[str, list[str]],
    max_hops: int = 2,
) -> list[str]:
    if max_hops < 0:
        raise ValueError("max_hops must be greater than or equal to 0")

    expanded: list[str] = []
    visited: set[str] = set()
    frontier = _dedupe(seed_entities)

    for entity in frontier:
        _append_if_new(expanded, visited, entity)

    for _ in range(max_hops):
        next_frontier: list[str] = []
        for entity in frontier:
            for neighbor in adjacency.get(entity, []):
                if neighbor in visited:
                    continue
                _append_if_new(expanded, visited, neighbor)
                next_frontier.append(neighbor)
        frontier = next_frontier
        if not frontier:
            break

    return expanded


def _append_unique(adjacency: dict[str, list[str]], source: str, target: str) -> None:
    neighbors = adjacency.setdefault(source, [])
    if target not in neighbors:
        neighbors.append(target)


def _append_if_new(items: list[str], visited: set[str], item: str) -> None:
    if item and item not in visited:
        visited.add(item)
        items.append(item)


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
