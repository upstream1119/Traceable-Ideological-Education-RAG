import os
from dataclasses import dataclass
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI


ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_ZHIPU_MODEL = "glm-4.5-air"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_QWEN_MODEL = "qwen-plus"
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
        key = key.lstrip("\ufeff")
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return ""


@dataclass
class LLMGenerationResult:
    text: str
    provider_name: str
    status: str


class StubLLMProvider:
    name = "stub"

    def generate(self, prompt: str) -> LLMGenerationResult:
        return LLMGenerationResult(
            text="",
            provider_name=self.name,
            status="stub_no_external_call",
        )


class OpenAICompatibleLLMProvider:
    name = ""
    api_key_env = ""
    model_env = ""
    default_model = ""
    base_url = ""
    extra_body = None
    max_retries = 2
    max_tokens = 800
    timeout_seconds = 30
    system_prompt = ""

    def generate(self, prompt: str) -> LLMGenerationResult:
        api_key = (
            os.getenv(self.api_key_env, "").strip()
            or _read_local_env_value(self.api_key_env)
        )
        if not api_key:
            return LLMGenerationResult(
                text="",
                provider_name=self.name,
                status="missing_api_key",
            )

        model = (
            os.getenv(self.model_env, "").strip()
            or _read_local_env_value(self.model_env)
            or self.default_model
        )
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                max_retries=self.max_retries,
            )
            request = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": self.max_tokens,
            }
            if self.system_prompt:
                request["messages"].insert(0, {"role": "system", "content": self.system_prompt})
            if self.extra_body:
                request["extra_body"] = self.extra_body
            response = client.chat.completions.create(**request)
            if getattr(response.choices[0], "finish_reason", None) == "length":
                return LLMGenerationResult(
                    text="",
                    provider_name=self.name,
                    status="truncated_response",
                )
            text = response.choices[0].message.content or ""
            text = text.strip()
            if not text:
                return LLMGenerationResult(
                    text="",
                    provider_name=self.name,
                    status="empty_response",
                )
            return LLMGenerationResult(
                text=text,
                provider_name=self.name,
                status="success",
            )
        except Exception as exc:
            # 不把异常正文返回给接口，避免意外泄露请求或认证信息。
            status = "provider_error"
            if isinstance(exc, APITimeoutError):
                status = "provider_timeout"
            elif isinstance(exc, APIConnectionError):
                status = "provider_connection_error"
            elif isinstance(exc, APIStatusError):
                status = {401: "provider_auth_error", 403: "provider_access_denied",
                          429: "provider_rate_limit", 400: "provider_invalid_request",
                          404: "provider_model_unavailable"}.get(exc.status_code, "provider_http_error")
            return LLMGenerationResult(
                text="",
                provider_name=self.name,
                status=status,
            )


class ZhipuLLMProvider(OpenAICompatibleLLMProvider):
    name = "zhipu"
    api_key_env = "ZAI_API_KEY"
    model_env = "DACHUANG_LLM_MODEL"
    default_model = DEFAULT_ZHIPU_MODEL
    base_url = ZHIPU_BASE_URL
    extra_body = {"thinking": {"type": "disabled"}}


class DeepSeekLLMProvider(OpenAICompatibleLLMProvider):
    name = "deepseek"
    api_key_env = "DEEPSEEK_API_KEY"
    model_env = "DACHUANG_DEEPSEEK_MODEL"
    default_model = DEFAULT_DEEPSEEK_MODEL
    base_url = DEEPSEEK_BASE_URL


class QwenLLMProvider(OpenAICompatibleLLMProvider):
    name = "qwen"
    max_retries = 0
    max_tokens = 1200
    extra_body = {"enable_thinking": False}
    api_key_env = "DASHSCOPE_API_KEY"
    model_env = "DACHUANG_QWEN_MODEL"
    default_model = DEFAULT_QWEN_MODEL
    base_url = QWEN_BASE_URL


def get_llm_provider(provider_name: str):
    provider_name = (provider_name or "").strip().lower()
    if provider_name in {"zhipu", "glm", "glm-4.5-air"}:
        return ZhipuLLMProvider()
    if provider_name in {"deepseek", "deepseek-chat", "deepseek-v4-flash"}:
        return DeepSeekLLMProvider()
    if provider_name in {"qwen", "dashscope", "bailian", "qwen-plus"}:
        return QwenLLMProvider()
    return StubLLMProvider()
