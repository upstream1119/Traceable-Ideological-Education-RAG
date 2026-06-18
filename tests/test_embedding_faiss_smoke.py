from types import SimpleNamespace

from scripts import run_embedding_faiss_smoke_test as smoke


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
