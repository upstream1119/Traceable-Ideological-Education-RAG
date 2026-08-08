import json

from src.utils.validate_triples import validate_triples


def _write_jsonl(path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )


def _chunk(chunk_id: str) -> dict:
    return {
        "id": chunk_id,
        "title": "测试标题",
        "text": "这是一条用于三元组引用校验的测试文本。",
    }


def _triple(*source_chunk_ids: str) -> dict:
    return {
        "head": "中国共产党",
        "relation": "开展",
        "tail": "思想政治教育",
        "source_chunk_ids": list(source_chunk_ids),
    }


def test_validate_triples_accepts_references_from_multiple_chunk_files(tmp_path):
    chunks_v1 = tmp_path / "chunks_v1.jsonl"
    chunks_v2 = tmp_path / "chunks_v2.jsonl"
    triples = tmp_path / "triples.jsonl"
    _write_jsonl(chunks_v1, [_chunk("chunk_v1_001")])
    _write_jsonl(chunks_v2, [_chunk("chunk_v2_001")])
    _write_jsonl(triples, [_triple("chunk_v1_001", "chunk_v2_001")])

    result = validate_triples(triples, [chunks_v1, chunks_v2])

    assert result == 0


def test_validate_triples_rejects_unknown_source_chunk_id(tmp_path, capsys):
    chunks = tmp_path / "chunks.jsonl"
    triples = tmp_path / "triples.jsonl"
    _write_jsonl(chunks, [_chunk("chunk_v1_001")])
    _write_jsonl(triples, [_triple("chunk_missing_999")])

    result = validate_triples(triples, [chunks])

    captured = capsys.readouterr()
    assert result == 1
    assert "chunk_missing_999" in captured.out


def test_validate_triples_rejects_duplicate_chunk_ids_across_files(tmp_path, capsys):
    chunks_v1 = tmp_path / "chunks_v1.jsonl"
    chunks_v2 = tmp_path / "chunks_v2.jsonl"
    triples = tmp_path / "triples.jsonl"
    _write_jsonl(chunks_v1, [_chunk("chunk_duplicate_001")])
    _write_jsonl(chunks_v2, [_chunk("chunk_duplicate_001")])
    _write_jsonl(triples, [_triple("chunk_duplicate_001")])

    result = validate_triples(triples, [chunks_v1, chunks_v2])

    captured = capsys.readouterr()
    assert result == 1
    assert "chunk id 重复" in captured.out
