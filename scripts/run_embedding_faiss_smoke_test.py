import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.vector.embedding_provider import QwenEmbeddingProvider
from src.vector.faiss_store import FaissVectorStore, build_embedding_text


LOCAL_ENV_PATH = REPO_ROOT / ".env.local"
DEFAULT_CHUNK_PATH = REPO_ROOT / "data" / "processed" / "text_chunks_sizheng_v1.jsonl"
DEFAULT_QUERY_PATH = REPO_ROOT / "tests" / "demo_queries_sizheng_history.json"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "vector_experiments" / "2026-06-faiss-smoke"


def _load_local_env() -> None:
    if not LOCAL_ENV_PATH.exists():
        return

    for line in LOCAL_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.lstrip("\ufeff").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, 1):
            raw = line.strip()
            if not raw:
                continue
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError(f"line {line_no} must contain a JSON object")
            records.append(data)
    return records


def _load_queries(path: Path, limit: int) -> list[dict]:
    items = json.loads(path.read_text(encoding="utf-8"))
    queries = [item for item in items if item.get("is_suitable_for_demo", True)]
    if limit <= 0:
        return queries
    return queries[:limit]


def _embed_in_batches(provider, texts: list[str], batch_size: int) -> tuple[list[list[float]], int]:
    vectors: list[list[float]] = []
    input_tokens = 0
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        result = provider.embed(batch)
        if result.status != "success":
            raise RuntimeError(f"embedding provider failed: {result.status}")
        if len(result.vectors) != len(batch):
            raise RuntimeError("embedding response count does not match input count")
        vectors.extend(result.vectors)
        input_tokens += result.input_tokens or 0
        print(
            f"[embedding] {min(start + len(batch), len(texts))}/{len(texts)}",
            flush=True,
        )
    return vectors, input_tokens


def _normalize_section(value: str) -> str:
    return "".join(str(value).split())


def _has_expected_section(hits: list[dict], expected_sections: list[str]) -> bool:
    normalized_expected = [
        _normalize_section(section) for section in expected_sections if section
    ]
    for hit in hits:
        citation = hit.get("citation") or {}
        actual = _normalize_section(citation.get("section", ""))
        if not actual:
            continue
        if any(expected in actual or actual in expected for expected in normalized_expected):
            return True
    return False


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_summary(
    path: Path,
    rows: list[dict],
    chunk_count: int,
    model: str,
    dimensions: int,
    input_tokens: int,
    elapsed_seconds: float,
) -> None:
    section_hit_count = sum(row["expected_section_hit"] for row in rows)
    lines = [
        "# Embedding + FAISS 冒烟测试结果",
        "",
        f"- 运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Chunk 数量：{chunk_count}",
        f"- Embedding 模型：{model}",
        f"- 向量维度：{dimensions}",
        f"- API 输入 token：{input_tokens}",
        f"- 总耗时：{elapsed_seconds:.2f} 秒",
        f"- 预期章节命中：{section_hit_count}/{len(rows)}",
        "",
        "| 序号 | 问题 | Top-1 | Top-1页码 | 预期章节命中 |",
        "|---:|---|---|---:|---|",
    ]
    for index, row in enumerate(rows, 1):
        top_hit = row["hits"][0] if row["hits"] else {}
        citation = top_hit.get("citation") or {}
        lines.append(
            f"| {index} | {row['query']} | {top_hit.get('title', '')} | "
            f"{citation.get('page', '')} | "
            f"{'是' if row['expected_section_hit'] else '否'} |"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 本轮用于验证真实 Embedding 与 FAISS 链路，不代表正式实验结论。",
            "- 当前数据覆盖 PDF 页码 21-150，后段章节需要在 v2 数据补齐后重建索引。",
            "- 正式实验需要增加人工相关性标注，并计算 Recall@K、MRR 等指标。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNK_PATH)
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERY_PATH)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--dimensions", type=int, default=1024)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    _load_local_env()
    records = _load_jsonl(args.chunks)
    queries = _load_queries(args.queries, args.limit)
    provider = QwenEmbeddingProvider(dimensions=args.dimensions)
    model = (
        os.getenv("DACHUANG_EMBEDDING_MODEL", "").strip()
        or "text-embedding-v4"
    )

    started = time.perf_counter()
    chunk_texts = [build_embedding_text(record) for record in records]
    chunk_vectors, chunk_tokens = _embed_in_batches(
        provider,
        chunk_texts,
        args.batch_size,
    )
    query_vectors, query_tokens = _embed_in_batches(
        provider,
        [item["query"] for item in queries],
        args.batch_size,
    )

    store = FaissVectorStore()
    store.build(records, np.asarray(chunk_vectors, dtype="float32"))
    rows = []
    for query_item, query_vector in zip(queries, query_vectors):
        hits = store.search(
            np.asarray(query_vector, dtype="float32"),
            top_k=args.top_k,
        )
        rows.append(
            {
                "id": query_item.get("id"),
                "query": query_item["query"],
                "expected_citation_sections": query_item.get(
                    "expected_citation_sections",
                    [],
                ),
                "expected_section_hit": _has_expected_section(
                    hits,
                    query_item.get("expected_citation_sections", []),
                ),
                "hits": hits,
            }
        )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.faiss"
    metadata_path = output_dir / "metadata.json"
    results_path = output_dir / "results.jsonl"
    summary_path = output_dir / "summary.md"
    store.save(index_path, metadata_path)
    _write_jsonl(results_path, rows)
    elapsed_seconds = time.perf_counter() - started
    _write_summary(
        summary_path,
        rows,
        chunk_count=len(records),
        model=model,
        dimensions=args.dimensions,
        input_tokens=chunk_tokens + query_tokens,
        elapsed_seconds=elapsed_seconds,
    )

    print(f"INDEX={index_path}")
    print(f"METADATA={metadata_path}")
    print(f"RESULTS={results_path}")
    print(f"SUMMARY={summary_path}")


if __name__ == "__main__":
    main()
