import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "id",
    "source",
    "source_type",
    "title",
    "text",
    "chunk_type",
    "topic",
    "entities",
    "tags",
    "citation",
]

SOURCE_TYPE_ENUM = {
    "event_doc",
    "textbook",
    "courseware",
    "paper",
    "policy_doc",
    "letter",
    "landmark",
    "exam",
}

CHUNK_TYPE_ENUM = {
    "event",
    "textbook_chunk",
    "courseware_chunk",
    "paper_chunk",
    "policy_chunk",
    "narrative",
    "qa",
    "landmark",
}

MIN_TEXT_LENGTH = 30
MAX_TEXT_LENGTH = 1200


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _line_message(level: str, line_no: int, message: str) -> str:
    return f"{level} 行 {line_no}: {message}"


def validate_record(data: dict, line_no: int, seen_ids: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in data or _is_blank(data[field]):
            errors.append(_line_message("ERROR", line_no, f"缺失必填字段或内容为空 -> {field}"))

    current_id = data.get("id")
    if not _is_blank(current_id):
        if current_id in seen_ids:
            errors.append(_line_message("ERROR", line_no, f"id 重复 -> {current_id}"))
        seen_ids.add(current_id)

    source_type = data.get("source_type")
    if not _is_blank(source_type) and source_type not in SOURCE_TYPE_ENUM:
        errors.append(_line_message("ERROR", line_no, f"source_type 不在允许范围内 -> {source_type}"))

    chunk_type = data.get("chunk_type")
    if not _is_blank(chunk_type) and chunk_type not in CHUNK_TYPE_ENUM:
        errors.append(_line_message("ERROR", line_no, f"chunk_type 不在允许范围内 -> {chunk_type}"))

    for list_field in ("entities", "tags"):
        value = data.get(list_field)
        if list_field in data and not isinstance(value, list):
            errors.append(_line_message("ERROR", line_no, f"{list_field} 必须是数组 list"))
        elif isinstance(value, list) and any(not isinstance(item, str) for item in value):
            errors.append(_line_message("ERROR", line_no, f"{list_field} 中的每一项都必须是字符串"))

    text = data.get("text")
    if isinstance(text, str):
        text_len = len(text.strip())
        if 0 < text_len < MIN_TEXT_LENGTH:
            warnings.append(_line_message("WARN", line_no, f"text 偏短，当前 {text_len} 字，建议不少于 {MIN_TEXT_LENGTH} 字"))
        if text_len > MAX_TEXT_LENGTH:
            warnings.append(_line_message("WARN", line_no, f"text 偏长，当前 {text_len} 字，建议不超过 {MAX_TEXT_LENGTH} 字"))

    citation = data.get("citation")
    if "citation" in data and not isinstance(citation, dict):
        errors.append(_line_message("ERROR", line_no, "citation 必须是对象 dict"))
    elif isinstance(citation, dict):
        if _is_blank(citation.get("doc")):
            errors.append(_line_message("ERROR", line_no, "citation.doc 缺失，无法进行零幻觉溯源"))
        if _is_blank(citation.get("section")):
            errors.append(_line_message("ERROR", line_no, "citation.section 缺失；无天然 section 时应由 ETL 自动生成"))

        page = citation.get("page")
        if page is not None:
            if not isinstance(page, int):
                errors.append(_line_message("ERROR", line_no, f"citation.page 必须是整数或 null -> {page}"))
            elif page <= 0:
                errors.append(_line_message("ERROR", line_no, f"citation.page 必须是正整数或 null -> {page}"))

    return errors, warnings


def validate_jsonl(file_path: str) -> int:
    path = Path(file_path)
    print(f"[多智能体思政系统] 开启知识库 JSONL 入库质检: {path}")

    if not path.exists():
        print(f"ERROR 找不到文件: {path}")
        return 1

    seen_ids: set[str] = set()
    all_errors: list[str] = []
    all_warnings: list[str] = []
    total_records = 0

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            raw = line.strip()
            if not raw:
                continue
            total_records += 1
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                all_errors.append(_line_message("ERROR", line_no, f"无效 JSON 格式 -> {exc.msg}"))
                continue

            if not isinstance(data, dict):
                all_errors.append(_line_message("ERROR", line_no, "每一行必须是 JSON 对象"))
                continue

            errors, warnings = validate_record(data, line_no, seen_ids)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

    for warning in all_warnings:
        print(warning)
    for error in all_errors:
        print(error)

    print(f"检查完成: records={total_records}, warnings={len(all_warnings)}, errors={len(all_errors)}")

    if all_errors:
        print("质检未通过，请修正 ERROR 后再提交。")
        return 1

    print("质检通过，可进入本地索引或负责人验收阶段。")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python src/utils/validate_jsonl.py <path_to_jsonl>")
        return 1
    return validate_jsonl(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
