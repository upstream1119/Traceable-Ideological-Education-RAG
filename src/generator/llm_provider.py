import os
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI


ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
DEFAULT_ZHIPU_MODEL = "glm-4.5-air"
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


class ZhipuLLMProvider:
    name = "zhipu"

    def generate(self, prompt: str) -> LLMGenerationResult:
        api_key = os.getenv("ZAI_API_KEY", "").strip() or _read_local_env_value("ZAI_API_KEY")
        if not api_key:
            return LLMGenerationResult(
                text="",
                provider_name=self.name,
                status="missing_api_key",
            )

        model = os.getenv("DACHUANG_LLM_MODEL", DEFAULT_ZHIPU_MODEL).strip()
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=ZHIPU_BASE_URL,
                timeout=30,
                max_retries=2,
            )
            response = client.chat.completions.create(
                model=model or DEFAULT_ZHIPU_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=800,
                extra_body={"thinking": {"type": "disabled"}},
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
        except Exception:
            # 不把异常正文返回给接口，避免意外泄露请求或认证信息。
            return LLMGenerationResult(
                text="",
                provider_name=self.name,
                status="provider_error",
            )


def get_llm_provider(provider_name: str):
    if provider_name in {"zhipu", "glm", "glm-4.5-air"}:
        return ZhipuLLMProvider()
    return StubLLMProvider()
