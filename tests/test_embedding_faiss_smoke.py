from types import SimpleNamespace

import numpy as np
import pytest

from scripts import run_embedding_faiss_smoke_test as smoke
from src.vector.faiss_store import FaissVectorStore


def test_embed_in_batches_preserves_order_and_accumulates_usage():
    calls = []

    class FakeProvider:
        def embed(self, texts):
            calls.append(list(texts))
            return SimpleNamespace(
                status="success",
                vectors=[[float(text)] for text in texts],
                input_tokens=len(texts) * 2,
            )

    vectors, input_tokens = smoke._embed_in_batches(
        FakeProvider(),
        ["1", "2", "3", "4", "5"],
        batch_size=2,
    )

    assert calls == [["1", "2"], ["3", "4"], ["5"]]
    assert vectors == [[1.0], [2.0], [3.0], [4.0], [5.0]]
    assert input_tokens == 10


def test_expected_section_match_ignores_spacing():
    hits = [
        {
            "citation": {
                "section": "第一章 中国共产党成立 / 第一节 马克思主义传播"
            }
        }
    ]

    matched = smoke._has_expected_section(
        hits,
        ["第一章中国共产党成立 / 第一节马克思主义传播"],
    )

    assert matched is True


def test_expected_section_match_rejects_missing_section():
    matched = smoke._has_expected_section(
        [{"citation": {"section": ""}}],
        ["第一章 / 第一节"],
    )

    assert matched is False


def test_retrieval_metrics_report_first_rank_and_recall_at_k():
    hits = [
        {"citation": {"section": "无关章节"}},
        {"citation": {"section": "第一章 / 第一节"}},
        {"citation": {"section": "第一章 / 第一节"}},
    ]

    metrics = smoke._calculate_retrieval_metrics(
        hits,
        ["第一章 / 第一节"],
    )

    assert metrics == {
        "first_expected_rank": 2,
        "recall_at_1": 0,
        "recall_at_3": 1,
        "recall_at_5": 1,
        "reciprocal_rank": 0.5,
    }


def test_retrieval_metrics_report_miss():
    metrics = smoke._calculate_retrieval_metrics(
        [{"citation": {"section": "无关章节"}}],
        ["第一章 / 第一节"],
    )

    assert metrics == {
        "first_expected_rank": None,
        "recall_at_1": 0,
        "recall_at_3": 0,
        "recall_at_5": 0,
        "reciprocal_rank": 0.0,
    }


def test_aggregate_metrics_calculates_recall_and_mrr():
    metrics = smoke._aggregate_metrics(
        [
            {
                "recall_at_1": 1,
                "recall_at_3": 1,
                "recall_at_5": 1,
                "reciprocal_rank": 1.0,
            },
            {
                "recall_at_1": 0,
                "recall_at_3": 1,
                "recall_at_5": 1,
                "reciprocal_rank": 0.5,
            },
            {
                "recall_at_1": 0,
                "recall_at_3": 0,
                "recall_at_5": 0,
                "reciprocal_rank": 0.0,
            },
        ]
    )

    assert metrics == {
        "recall_at_1": 1 / 3,
        "recall_at_3": 2 / 3,
        "recall_at_5": 2 / 3,
        "mrr": 0.5,
    }


def test_load_reused_store_validates_existing_index(tmp_path):
    records = [{"id": "chunk_001", "citation": {"section": "第一章"}}]
    store = FaissVectorStore()
    store.build(records, np.asarray([[1.0, 0.0]], dtype="float32"))
    store.save(tmp_path / "index.faiss", tmp_path / "metadata.json")
    (tmp_path / "summary.md").write_text(
        "- Embedding 模型：text-embedding-v4\n"
        "- 向量维度：2\n",
        encoding="utf-8",
    )

    loaded = smoke._load_reused_store(
        tmp_path,
        records,
        dimensions=2,
        model="text-embedding-v4",
    )

    assert loaded.record_count == 1
    assert loaded.dimension == 2


def test_load_reused_store_rejects_changed_chunks(tmp_path):
    store = FaissVectorStore()
    store.build(
        [{"id": "chunk_001"}],
        np.asarray([[1.0, 0.0]], dtype="float32"),
    )
    store.save(tmp_path / "index.faiss", tmp_path / "metadata.json")
    (tmp_path / "summary.md").write_text(
        "- Embedding 模型：text-embedding-v4\n"
        "- 向量维度：2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="chunk data"):
        smoke._load_reused_store(
            tmp_path,
            [{"id": "chunk_002"}],
            dimensions=2,
            model="text-embedding-v4",
        )


def test_load_reused_store_rejects_model_mismatch(tmp_path):
    records = [{"id": "chunk_001"}]
    store = FaissVectorStore()
    store.build(records, np.asarray([[1.0, 0.0]], dtype="float32"))
    store.save(tmp_path / "index.faiss", tmp_path / "metadata.json")
    (tmp_path / "summary.md").write_text(
        "- Embedding 模型：other-model\n"
        "- 向量维度：2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="model"):
        smoke._load_reused_store(
            tmp_path,
            records,
            dimensions=2,
            model="text-embedding-v4",
        )


def test_prepare_vector_store_does_not_embed_chunks_when_reusing(tmp_path):
    records = [{"id": "chunk_001"}]
    store = FaissVectorStore()
    store.build(records, np.asarray([[1.0, 0.0]], dtype="float32"))
    store.save(tmp_path / "index.faiss", tmp_path / "metadata.json")
    (tmp_path / "summary.md").write_text(
        "- Embedding 模型：text-embedding-v4\n"
        "- 向量维度：2\n",
        encoding="utf-8",
    )

    class FailingProvider:
        def embed(self, texts):
            raise AssertionError("chunk embedding must not run")

    loaded, chunk_tokens, reused = smoke._prepare_vector_store(
        provider=FailingProvider(),
        records=records,
        batch_size=10,
        dimensions=2,
        model="text-embedding-v4",
        reuse_index_dir=tmp_path,
    )

    assert loaded.record_count == 1
    assert chunk_tokens == 0
    assert reused is True
