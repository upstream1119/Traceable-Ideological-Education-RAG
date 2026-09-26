from types import SimpleNamespace

from src.vector.embedding_provider import QwenEmbeddingProvider


def test_qwen_embedding_provider_reports_missing_api_key():
    provider = QwenEmbeddingProvider(api_key="")

    result = provider.embed(["测试文本"])

    assert result.status == "missing_api_key"
    assert result.provider_name == "qwen"
    assert result.vectors == []


def test_qwen_embedding_provider_returns_vectors_and_usage():
    captured = {}

    class FakeEmbeddings:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return SimpleNamespace(
                data=[
                    SimpleNamespace(index=1, embedding=[0.0, 1.0]),
                    SimpleNamespace(index=0, embedding=[1.0, 0.0]),
                ],
                usage=SimpleNamespace(prompt_tokens=12),
            )

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.embeddings = FakeEmbeddings()

    provider = QwenEmbeddingProvider(
        api_key="test-key",
        model="text-embedding-v4",
        dimensions=1024,
        client_factory=FakeClient,
    )

    result = provider.embed(["文本一", "文本二"])

    assert captured["client"]["base_url"].endswith("/compatible-mode/v1")
    assert captured["request"] == {
        "model": "text-embedding-v4",
        "input": ["文本一", "文本二"],
        "dimensions": 1024,
        "encoding_format": "float",
    }
    assert result.status == "success"
    assert result.vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert result.input_tokens == 12
