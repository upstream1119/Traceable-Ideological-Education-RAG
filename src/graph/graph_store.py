import json
from collections import deque
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


def build_relation_lookup(
    triples: list[dict],
    bidirectional: bool = True,
) -> dict[tuple[str, str], str]:
    relation_lookup: dict[tuple[str, str], str] = {}

    for triple in triples:
        head = triple["head"]
        tail = triple["tail"]
        relation_lookup[(head, tail)] = triple["relation"]
        if bidirectional:
            # 反向边只用于检索扩展，避免把原始关系方向说反。
            relation_lookup[(tail, head)] = "关联"

    return relation_lookup


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


def find_entity_paths(
    seed_entities: list[str],
    target_entities: list[str],
    adjacency: dict[str, list[str]],
    relation_lookup: dict[tuple[str, str], str] | None = None,
    max_hops: int = 2,
    limit: int = 5,
) -> list[dict]:
    if max_hops < 0:
        raise ValueError("max_hops must be greater than or equal to 0")

    relation_lookup = relation_lookup or {}
    targets = set(_dedupe(target_entities))
    paths: list[dict] = []
    seen_paths: set[tuple[str, ...]] = set()

    for seed in _dedupe(seed_entities):
        queue = deque([[seed]])
        while queue and len(paths) < limit:
            path = queue.popleft()
            if len(path) - 1 >= max_hops:
                continue

            current = path[-1]
            for neighbor in adjacency.get(current, []):
                if neighbor in path:
                    continue

                next_path = path + [neighbor]
                if neighbor in targets:
                    path_key = tuple(next_path)
                    if path_key not in seen_paths:
                        seen_paths.add(path_key)
                        relations = _path_relations(next_path, relation_lookup)
                        paths.append(
                            {
                                "from": seed,
                                "to": neighbor,
                                "hops": len(next_path) - 1,
                                "path": next_path,
                                "relations": relations,
                                "path_text": _format_path_text(next_path, relations),
                            }
                        )
                    if len(paths) >= limit:
                        break

                queue.append(next_path)

    return paths


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


def _path_relations(
    path: list[str],
    relation_lookup: dict[tuple[str, str], str],
) -> list[str]:
    relations: list[str] = []
    for source, target in zip(path, path[1:]):
        relations.append(relation_lookup.get((source, target), "关联"))
    return relations


def _format_path_text(path: list[str], relations: list[str]) -> str:
    if not path:
        return ""

    text = path[0]
    for relation, target in zip(relations, path[1:]):
        text += f" --{relation}--> {target}"
    return text
