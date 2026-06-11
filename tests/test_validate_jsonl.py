import json

from src.utils.validate_jsonl import validate_jsonl


def _valid_record(**overrides):
    record = {
        "id": "chunk_test_001",
        "source": "中国共产党思想政治教育史",
        "source_type": "textbook",
        "title": "测试标题",
        "text": "这是一条用于测试知识库入库质量检查器的文本，长度满足基本检查要求。",
        "chunk_type": "textbook_chunk",
        "topic": "思想政治教育",
        "entities": ["思想政治教育", "中国共产党"],
        "tags": ["测试"],
        "citation": {
            "doc": "中国共产党思想政治教育史",
            "section": "测试章节",
            "page": 1,
        },
    }
    record.update(overrides)
    return record


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )


def test_validate_jsonl_accepts_valid_record(tmp_path):
    path = tmp_path / "valid.jsonl"
    _write_jsonl(path, [_valid_record()])

    assert validate_jsonl(str(path)) == 0


def test_validate_jsonl_rejects_missing_required_field(tmp_path):
    path = tmp_path / "missing.jsonl"
    record = _valid_record()
    record.pop("topic")
    _write_jsonl(path, [record])

    assert validate_jsonl(str(path)) == 1


def test_validate_jsonl_rejects_invalid_enums(tmp_path):
    path = tmp_path / "bad_enum.jsonl"
    _write_jsonl(
        path,
        [
            _valid_record(
                source_type="unknown_source",
                chunk_type="unknown_chunk",
            )
        ],
    )

    assert validate_jsonl(str(path)) == 1


def test_validate_jsonl_rejects_bad_citation_page(tmp_path):
    path = tmp_path / "bad_page.jsonl"
    _write_jsonl(path, [_valid_record(citation={"doc": "教材", "section": "章节", "page": "12"})])

    assert validate_jsonl(str(path)) == 1


def test_validate_jsonl_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "duplicate.jsonl"
    _write_jsonl(path, [_valid_record(), _valid_record(title="另一条文本")])

    assert validate_jsonl(str(path)) == 1


def test_validate_jsonl_allows_null_page(tmp_path):
    path = tmp_path / "null_page.jsonl"
    _write_jsonl(path, [_valid_record(citation={"doc": "教材", "section": "章节", "page": None})])

    assert validate_jsonl(str(path)) == 0
