import json

from scripts.evaluate_chunk_batch import FAIL_STATUS, PASS_STATUS, evaluate_batch


def _valid_chunk(**overrides):
    chunk = {
        "id": "chunk_test_001",
        "source": "中国共产党思想政治教育史",
        "source_type": "textbook",
        "title": "马克思主义的最初传入",
        "text": "马克思主义最初在中国经历了介绍、传播和论战过程，并逐步形成思想政治教育的重要理论基础。",
        "chunk_type": "textbook_chunk",
        "topic": "马克思主义传播",
        "entities": ["马克思主义"],
        "tags": ["传播"],
        "citation": {
            "doc": "中国共产党思想政治教育史",
            "section": "第一章 / 第一节",
            "page": 25,
        },
    }
    chunk.update(overrides)
    return chunk


def _write_jsonl(path, records):
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def test_evaluate_chunk_batch_reports_query_candidates(tmp_path):
    chunks = tmp_path / "chunks.jsonl"
    queries = tmp_path / "queries.json"
    _write_jsonl(chunks, [_valid_chunk()])
    queries.write_text(
        json.dumps(
            [
                {
                    "id": "q1",
                    "query": "马克思主义最初在中国如何传入？",
                    "expected_entities": ["马克思主义"],
                    "expected_citation_keywords": ["中国共产党思想政治教育史"],
                    "expected_chunk_ids": ["chunk_test_001"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = evaluate_batch(chunks, queries)

    assert report["overall_status"] == PASS_STATUS
    assert report["record_count"] == 1
    assert report["schema_error_count"] == 0
    assert report["query_reports"][0]["top_candidates"][0]["id"] == "chunk_test_001"
    assert report["query_reports"][0]["matched_expected_chunk_ids"] == ["chunk_test_001"]


def test_evaluate_chunk_batch_fails_on_schema_errors(tmp_path):
    chunks = tmp_path / "chunks.jsonl"
    queries = tmp_path / "queries.json"
    broken = _valid_chunk(citation={"doc": "中国共产党思想政治教育史"})
    _write_jsonl(chunks, [broken])
    queries.write_text("[]", encoding="utf-8")

    report = evaluate_batch(chunks, queries)

    assert report["overall_status"] == FAIL_STATUS
    assert report["schema_error_count"] > 0
