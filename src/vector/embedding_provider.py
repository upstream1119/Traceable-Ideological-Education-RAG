import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from openai import OpenAI


QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_EMBEDDING_MODEL = "text-embedding-v4"
DEFAULT_EMBEDDING_DIMENSIONS = 1024
REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_ENV_PATH = REPO_ROOT / ".env.local"


def _read_local_env_value(name: str) -> str:
    if not LOCAL_ENV_PATH.exists():
        return ""

    for line in LOCAL_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.lstrip("\ufeff").strip() == name:
            return value.strip().strip('"').strip("'")
    return ""


@dataclass
class EmbeddingResult:
    vectors: list[list[float]]
    provider_name: str
    model: str
    status: str
    input_tokens: int | None = None


class QwenEmbeddingProvider:
    name = "qwen"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
        client_factory: Callable = OpenAI,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._client_factory = client_factory

    def _resolve_api_key(self) -> str:
        if self._api_key is not None:
            return self._api_key.strip()
        return (
            os.getenv("DASHSCOPE_API_KEY", "").strip()
            or _read_local_env_value("DASHSCOPE_API_KEY")
        )

    def _resolve_model(self) -> str:
        if self._model:
            return self._model
        return (
            os.getenv("DACHUANG_EMBEDDING_MODEL", "").strip()
            or _read_local_env_value("DACHUANG_EMBEDDING_MODEL")
            or DEFAULT_QWEN_EMBEDDING_MODEL
        )

    def embed(self, texts: list[str]) -> EmbeddingResult:
        model = self._resolve_model()
        api_key = self._resolve_api_key()
        if not api_key:
            return EmbeddingResult(
                vectors=[],
                provider_name=self.name,
                model=model,
                status="missing_api_key",
            )

        if not texts:
            return EmbeddingResult(
                vectors=[],
                provider_name=self.name,
                model=model,
                status="empty_input",
                input_tokens=0,
            )

        try:
            client = self._client_factory(
                api_key=api_key,
                base_url=QWEN_BASE_URL,
                timeout=60,
                max_retries=2,
            )
            response = client.embeddings.create(
                model=model,
                input=texts,
                dimensions=self._dimensions,
                encoding_format="float",
            )
            vectors = [
                item.embedding
                for item in sorted(response.data, key=lambda item: item.index)
            ]
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", None)
            return EmbeddingResult(
                vectors=vectors,
                provider_name=self.name,
                model=model,
                status="success",
                input_tokens=input_tokens,
            )
        except Exception:
            return EmbeddingResult(
                vectors=[],
                provider_name=self.name,
                model=model,
                status="provider_error",
            )
