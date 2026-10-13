NODE_TYPES = {"person", "organization", "event", "place", "document", "time", "concept"}
NODE_FIELDS = {"id", "label", "type", "source_chunk_ids", "degree"}
EDGE_FIELDS = {"id", "source", "target", "relation", "source_chunk_ids", "directed", "display_label"}


def _validate_chunk_ids(value: object, known_chunk_ids: set[str], location: str) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{location}.source_chunk_ids must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{location}.source_chunk_ids contains an invalid id")
    missing = sorted(set(value) - known_chunk_ids)
    if missing:
        raise ValueError(f"{location}.source_chunk_ids cannot be resolved: {missing}")


def validate_force_graph_payload(payload: dict, known_chunk_ids: set[str]) -> None:
    nodes = payload.get("nodes")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("nodes and edges must be lists")

    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        location = f"nodes[{index}]"
        if not NODE_FIELDS.issubset(node):
            raise ValueError(f"{location} is missing required fields")
        node_id = node["id"]
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError(f"{location}.id must be a non-empty string")
        if node_id in node_ids:
            raise ValueError(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
        if not isinstance(node["label"], str) or not node["label"].strip():
            raise ValueError(f"{location}.label must be a non-empty string")
        if node["type"] not in NODE_TYPES:
            raise ValueError(f"{location}.type is invalid: {node['type']}")
        if not isinstance(node["degree"], int) or isinstance(node["degree"], bool) or node["degree"] < 0:
            raise ValueError(f"{location}.degree must be a non-negative integer")
        _validate_chunk_ids(node["source_chunk_ids"], known_chunk_ids, location)

    edge_ids: set[str] = set()
    for index, edge in enumerate(edges):
        location = f"edges[{index}]"
        if not EDGE_FIELDS.issubset(edge):
            raise ValueError(f"{location} is missing required fields")
        edge_id = edge["id"]
        if not isinstance(edge_id, str) or not edge_id.strip():
            raise ValueError(f"{location}.id must be a non-empty string")
        if edge_id in edge_ids:
            raise ValueError(f"duplicate edge id: {edge_id}")
        edge_ids.add(edge_id)
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            raise ValueError(f"{location} has a dangling endpoint")
        if type(edge["directed"]) is not bool:
            raise ValueError(f"{location}.directed must be boolean")
        for field in ("relation", "display_label"):
            if not isinstance(edge[field], str) or not edge[field].strip():
                raise ValueError(f"{location}.{field} must be a non-empty string")
        _validate_chunk_ids(edge["source_chunk_ids"], known_chunk_ids, location)


def validate_graph_path(path: dict, known_chunk_ids: set[str]) -> None:
    nodes = path.get("path")
    relations = path.get("relations")
    edges = path.get("edges")
    hops = path.get("hops")
    if not isinstance(nodes, list) or len(nodes) < 2:
        raise ValueError("path.path must contain at least two nodes")
    if not isinstance(relations, list) or not isinstance(edges, list):
        raise ValueError("path.relations and path.edges must be lists")
    if not isinstance(hops, int) or isinstance(hops, bool) or hops <= 0:
        raise ValueError("path.hops must be a positive non-boolean integer")
    if path.get("from") != nodes[0] or path.get("to") != nodes[-1]:
        raise ValueError("path from/to must match the first/last node")
    expected_hops = len(nodes) - 1
    if hops != expected_hops or len(relations) != expected_hops or len(edges) != expected_hops:
        raise ValueError("path hop count is inconsistent")
    for index, edge in enumerate(edges):
        location = f"path.edges[{index}]"
        if edge.get("source") != nodes[index] or edge.get("target") != nodes[index + 1]:
            raise ValueError(f"{location} does not match path endpoints")
        if edge.get("relation") != relations[index]:
            raise ValueError(f"{location} does not match path relation")
        if type(edge.get("original_direction")) is not bool:
            raise ValueError(f"{location}.original_direction must be boolean")
        _validate_chunk_ids(edge.get("source_chunk_ids"), known_chunk_ids, location)
    _validate_chunk_ids(path.get("source_chunk_ids"), known_chunk_ids, "path")
    expected_chunk_ids: list[str] = []
    for edge in edges:
        for chunk_id in edge["source_chunk_ids"]:
            if chunk_id not in expected_chunk_ids:
                expected_chunk_ids.append(chunk_id)
    if path["source_chunk_ids"] != expected_chunk_ids:
        raise ValueError("path.source_chunk_ids must equal the deduplicated edge evidence ids")

