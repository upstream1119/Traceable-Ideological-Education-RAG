import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graph.graph_store import load_triples


def load_chunk_ids(
    chunk_paths: list[str | Path],
) -> tuple[set[str], int, list[str]]:
    chunk_ids: set[str] = set()
    total_chunks = 0
    errors: list[str] = []

    for chunk_path in chunk_paths:
        path = Path(chunk_path)
        if not path.exists():
            errors.append(f"ERROR 找不到 chunk 文件: {path}")
            continue

        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                total_chunks += 1

                try:
                    chunk = json.loads(raw)
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"ERROR {path} 行 {line_number}: 无效 JSON -> {exc.msg}"
                    )
                    continue

                if not isinstance(chunk, dict):
                    errors.append(f"ERROR {path} 行 {line_number}: 每行必须是 JSON 对象")
                    continue

                chunk_id = chunk.get("id")
                if not isinstance(chunk_id, str) or not chunk_id.strip():
                    errors.append(f"ERROR {path} 行 {line_number}: chunk id 缺失或为空")
                    continue

                if chunk_id in chunk_ids:
                    errors.append(
                        f"ERROR {path} 行 {line_number}: chunk id 重复 -> {chunk_id}"
                    )
                    continue
                chunk_ids.add(chunk_id)

    return chunk_ids, total_chunks, errors


def validate_triples(
    triples_path: str | Path,
    chunk_paths: list[str | Path],
) -> int:
    triples_file = Path(triples_path)
    print(f"[多智能体思政系统] 开启三元组证据引用质检: {triples_file}")

    chunk_ids, total_chunks, errors = load_chunk_ids(chunk_paths)
    triples: list[dict] = []

    if not triples_file.exists():
        errors.append(f"ERROR 找不到三元组文件: {triples_file}")
    else:
        try:
            triples = load_triples(triples_file)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append(f"ERROR 三元组格式无效: {exc}")

    reference_count = 0
    missing_ids: set[str] = set()
    for line_number, triple in enumerate(triples, start=1):
        for chunk_id in triple["source_chunk_ids"]:
            reference_count += 1
            if chunk_id in chunk_ids:
                continue
            missing_ids.add(chunk_id)
            errors.append(
                f"ERROR 三元组行 {line_number}: source_chunk_id 不存在 -> {chunk_id}"
            )

    for error in errors:
        print(error)

    print(
        "检查完成: "
        f"chunks={total_chunks}, triples={len(triples)}, "
        f"references={reference_count}, unique_missing={len(missing_ids)}, "
        f"errors={len(errors)}"
    )

    if errors:
        print("质检未通过，请修正 ERROR 后再提交。")
        return 1

    print("质检通过，三元组引用均能定位到正式 chunk。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="校验三元组对正式 chunk 的证据引用")
    parser.add_argument("--triples", required=True, help="待校验的三元组 JSONL 文件")
    parser.add_argument(
        "--chunks",
        required=True,
        nargs="+",
        help="一个或多个正式 chunk JSONL 文件",
    )
    args = parser.parse_args()
    return validate_triples(args.triples, args.chunks)


if __name__ == "__main__":
    raise SystemExit(main())
