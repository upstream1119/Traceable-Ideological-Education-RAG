import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np


def build_embedding_text(record: dict) -> str:
    citation = record.get("citation")
    if not isinstance(citation, dict):
        citation = {}

    fields = [
        record.get("title"),
        record.get("text"),
        record.get("topic"),
        citation.get("section"),
    ]
    for list_field in ("entities", "tags"):
        value = record.get(list_field)
        if isinstance(value, list):
            fields.append(" ".join(str(item) for item in value))

    return "\n".join(str(field).strip() for field in fields if field)


class FaissVectorStore:
    def __init__(self) -> None:
        self._index = None
        self._records: list[dict[str, Any]] = []

    def build(self, records: list[dict], vectors: np.ndarray) -> None:
        matrix = np.asarray(vectors, dtype="float32")
        if matrix.ndim != 2:
            raise ValueError("vectors must be a two-dimensional matrix")
        if len(records) != matrix.shape[0]:
            raise ValueError("record count must match vector count")
        if matrix.shape[0] == 0:
            raise ValueError("at least one record is required")

        matrix = matrix.copy()
        faiss.normalize_L2(matrix)
        self._index = faiss.IndexFlatIP(matrix.shape[1])
        self._index.add(matrix)
        self._records = list(records)

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict]:
        if self._index is None:
            raise RuntimeError("vector store has not been built")

        query = np.asarray(query_vector, dtype="float32").reshape(1, -1)
        if query.shape[1] != self._index.d:
            raise ValueError("query vector dimension does not match index")

        faiss.normalize_L2(query)
        limit = min(max(top_k, 0), len(self._records))
        if limit == 0:
            return []

        scores, indices = self._index.search(query, limit)
        hits = []
        for score, record_index in zip(scores[0], indices[0]):
            if record_index < 0:
                continue
            record = self._records[int(record_index)]
            hits.append(
                {
                    "id": record.get("id"),
                    "source": record.get("source"),
                    "title": record.get("title"),
                    "text": record.get("text"),
                    "citation": record.get("citation"),
                    "vector_score": round(float(score), 6),
                }
            )
        return hits

    def save(self, index_path: Path, metadata_path: Path) -> None:
        if self._index is None:
            raise RuntimeError("vector store has not been built")

        index_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_path))
        metadata_path.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, index_path: Path, metadata_path: Path) -> "FaissVectorStore":
        store = cls()
        store._index = faiss.read_index(str(index_path))
        records = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("metadata must contain a JSON list")
        if len(records) != store._index.ntotal:
            raise ValueError("metadata count does not match index count")
        store._records = records
        return store
