import numpy as np
import pytest

from src.vector.faiss_store import FaissVectorStore, build_embedding_text


def test_faiss_search_returns_most_similar_record_with_citation():
    records = [
        {
            "id": "chunk_001",
            "source": "测试教材",
            "title": "马克思主义传播",
            "text": "马克思主义在中国的早期传播。",
            "citation": {
                "doc": "测试教材",
                "section": "第一章",
                "page": 10,
            },
        },
        {
            "id": "chunk_002",
            "source": "测试教材",
            "title": "三湾改编",
            "text": "三湾改编加强了党对军队的领导。",
            "citation": {
                "doc": "测试教材",
                "section": "第二章",
                "page": 20,
            },
        },
    ]
    vectors = np.asarray(
        [
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        dtype="float32",
    )
    store = FaissVectorStore()
    store.build(records, vectors)

    hits = store.search(np.asarray([0.9, 0.1], dtype="float32"), top_k=1)

    assert hits == [
        {
            "id": "chunk_001",
            "source": "测试教材",
            "title": "马克思主义传播",
            "text": "马克思主义在中国的早期传播。",
            "citation": {
                "doc": "测试教材",
                "section": "第一章",
                "page": 10,
            },
            "vector_score": hits[0]["vector_score"],
        }
    ]
    assert hits[0]["vector_score"] > 0.99


def test_build_embedding_text_contains_retrieval_fields():
    record = {
        "title": "新式整军运动",
        "text": "通过政治整训提高部队战斗力。",
        "topic": "人民解放军思想政治教育",
        "entities": ["人民解放军", "新式整军运动"],
        "tags": ["解放战争", "政治工作"],
        "citation": {
            "doc": "中国共产党思想政治教育史",
            "section": "第四章 / 第二节",
            "page": 180,
        },
    }

    content = build_embedding_text(record)

    for expected in (
        "新式整军运动",
        "通过政治整训提高部队战斗力",
        "人民解放军思想政治教育",
        "人民解放军",
        "解放战争",
        "第四章 / 第二节",
    ):
        assert expected in content


def test_faiss_store_can_save_and_load(tmp_path):
    records = [
        {
            "id": "chunk_001",
            "source": "测试教材",
            "title": "干部教育",
            "text": "干部教育是重要战略任务。",
            "citation": {
                "doc": "测试教材",
                "section": "第三章",
                "page": 30,
            },
        }
    ]
    store = FaissVectorStore()
    store.build(records, np.asarray([[1.0, 0.0]], dtype="float32"))
    index_path = tmp_path / "index.faiss"
    metadata_path = tmp_path / "metadata.json"

    store.save(index_path, metadata_path)
    loaded = FaissVectorStore.load(index_path, metadata_path)
    hits = loaded.search(np.asarray([1.0, 0.0], dtype="float32"), top_k=1)

    assert hits[0]["id"] == "chunk_001"
    assert hits[0]["citation"]["page"] == 30


def test_faiss_search_rejects_dimension_mismatch():
    store = FaissVectorStore()
    store.build(
        [{"id": "chunk_001"}],
        np.asarray([[1.0, 0.0]], dtype="float32"),
    )

    with pytest.raises(ValueError, match="dimension"):
        store.search(np.asarray([1.0, 0.0, 0.0], dtype="float32"))
