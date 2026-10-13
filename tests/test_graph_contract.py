import copy
import json
from pathlib import Path

import pytest

from scripts.export_graphsim_integration_samples import build_samples
from src.graph.schema_validation import validate_force_graph_payload, validate_graph_path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORCE_GRAPH_PATH = REPO_ROOT / "data" / "graph" / "force_graph.json"
SAMPLES_PATH = REPO_ROOT / "reports" / "graphsim_integration_samples.json"
CHUNK_PATHS = (
    REPO_ROOT / "data" / "processed" / "text_chunks_sizheng_v1.jsonl",
    REPO_ROOT / "data" / "processed" / "text_chunks_sizheng_v2.jsonl",
)


def _chunk_ids() -> set[str]:
    return {
        json.loads(line)["id"]
        for path in CHUNK_PATHS
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def test_force_graph_matches_frozen_contract():
    payload = json.loads(FORCE_GRAPH_PATH.read_text(encoding="utf-8"))
    validate_force_graph_payload(payload, _chunk_ids())
    assert payload["node_type_values"] == [
        "person", "organization", "event", "place", "document", "time", "concept"
    ]


def test_fresh_integration_samples_match_committed_samples_and_paths():
    fresh = build_samples()
    committed = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    assert fresh == committed
    assert [
        sample["graph_hits"][0]["graph_paths"][0]["hops"] if sample["graph_hits"] else 0
        for sample in fresh["samples"]
    ] == [1, 2, 0]
    for sample in fresh["samples"]:
        path = sample["graph_hits"][0]["graph_paths"][0] if sample["graph_hits"] else None
        if path:
            validate_graph_path(path, _chunk_ids())
            evidence_ids = {item["id"] for item in sample["evidence_chunks"]}
            assert evidence_ids == set(path["source_chunk_ids"])
            assert all(item["text"] and item["citation"] for item in sample["evidence_chunks"])
        else:
            assert sample["query_entities"] == []
            assert sample["top_3_graph_hit_ids"] == []
            assert sample["graph_hits"] == []
            assert sample["evidence_chunks"] == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value["nodes"].append(copy.deepcopy(value["nodes"][0])), "duplicate node id"),
        (lambda value: value["edges"].append(copy.deepcopy(value["edges"][0])), "duplicate edge id"),
        (lambda value: value["edges"][0].update(source="missing-node"), "dangling endpoint"),
        (lambda value: value["edges"][0].update(source_chunk_ids=[""]), "invalid id"),
        (lambda value: value["edges"][0].update(source_chunk_ids=["chunk_missing"]), "cannot be resolved"),
        (lambda value: value["edges"][0].update(directed="true"), "must be boolean"),
    ],
)
def test_force_graph_contract_rejects_agreed_invalid_data(mutation, message):
    payload = json.loads(FORCE_GRAPH_PATH.read_text(encoding="utf-8"))
    mutation(payload)
    with pytest.raises(ValueError, match=message):
        validate_force_graph_payload(payload, _chunk_ids())


@pytest.mark.parametrize("invalid_label", ["", "   ", None, 1])
def test_force_graph_contract_rejects_empty_or_non_string_node_label(invalid_label):
    payload = json.loads(FORCE_GRAPH_PATH.read_text(encoding="utf-8"))
    payload["nodes"][0]["label"] = invalid_label
    with pytest.raises(ValueError, match="label must be a non-empty string"):
        validate_force_graph_payload(payload, _chunk_ids())


def _one_hop_path() -> dict:
    return build_samples()["samples"][0]["graph_hits"][0]["graph_paths"][0]


@pytest.mark.parametrize("invalid_hops", [True, 0, -1, 1.0, "1"])
def test_graph_path_contract_rejects_non_positive_or_non_integer_hops(invalid_hops):
    path = copy.deepcopy(_one_hop_path())
    path["hops"] = invalid_hops
    with pytest.raises(ValueError, match="positive non-boolean integer"):
        validate_graph_path(path, _chunk_ids())


@pytest.mark.parametrize(("field", "value"), [("from", "wrong-start"), ("to", "wrong-end")])
def test_graph_path_contract_rejects_from_or_to_mismatch(field, value):
    path = copy.deepcopy(_one_hop_path())
    path[field] = value
    with pytest.raises(ValueError, match="must match the first/last node"):
        validate_graph_path(path, _chunk_ids())


def test_graph_path_contract_rejects_aggregate_evidence_mismatch():
    path = copy.deepcopy(_one_hop_path())
    path["source_chunk_ids"].append(path["source_chunk_ids"][0])
    with pytest.raises(ValueError, match="deduplicated edge evidence ids"):
        validate_graph_path(path, _chunk_ids())


def test_graph_path_contract_rejects_inconsistent_hop_count_and_direction():
    path = _one_hop_path()
    invalid_hops = copy.deepcopy(path)
    invalid_hops["hops"] = 2
    with pytest.raises(ValueError, match="hop count is inconsistent"):
        validate_graph_path(invalid_hops, _chunk_ids())

    invalid_direction = copy.deepcopy(path)
    invalid_direction["edges"][0]["original_direction"] = "true"
    with pytest.raises(ValueError, match="must be boolean"):
        validate_graph_path(invalid_direction, _chunk_ids())
