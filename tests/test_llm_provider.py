from types import SimpleNamespace

from src.generator import llm_provider


def _install_fake_openai(monkeypatch, captured):
    class FakeCompletions:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="基于证据生成的答案")
                    )
                ]
            )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(llm_provider, "OpenAI", FakeOpenAI, raising=False)


def test_zhipu_provider_is_selected_by_name():
    provider = llm_provider.get_llm_provider("zhipu")

    assert provider.name == "zhipu"


def test_zhipu_provider_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(llm_provider, "_read_local_env_value", lambda name: "", raising=False)

    result = llm_provider.get_llm_provider("zhipu").generate("测试提示词")

    assert result.text == ""
    assert result.provider_name == "zhipu"
    assert result.status == "missing_api_key"


def test_zhipu_provider_calls_glm_45_air(monkeypatch):
    captured = {}

    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    _install_fake_openai(monkeypatch, captured)

    result = llm_provider.get_llm_provider("zhipu").generate("测试提示词")

    assert result.text == "基于证据生成的答案"
    assert result.status == "success"
    assert captured["client"]["api_key"] == "test-key"
    assert captured["client"]["base_url"] == "https://open.bigmodel.cn/api/paas/v4/"
    assert captured["request"]["model"] == "glm-4.5-air"
    assert captured["request"]["messages"] == [
        {"role": "user", "content": "测试提示词"}
    ]
    assert captured["request"]["temperature"] == 0.2
    assert captured["request"]["max_tokens"] == 800
    assert captured["request"]["extra_body"] == {
        "thinking": {"type": "disabled"}
    }


def test_deepseek_provider_uses_openai_compatible_endpoint(monkeypatch):
    captured = {}

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.delenv("DACHUANG_DEEPSEEK_MODEL", raising=False)
    monkeypatch.setattr(llm_provider, "_read_local_env_value", lambda name: "", raising=False)
    _install_fake_openai(monkeypatch, captured)

    result = llm_provider.get_llm_provider("deepseek").generate("测试提示词")

    assert result.text == "基于证据生成的答案"
    assert result.status == "success"
    assert captured["client"]["api_key"] == "test-key"
    assert captured["client"]["base_url"] == "https://api.deepseek.com"
    assert captured["request"]["model"] == "deepseek-v4-flash"
    assert captured["request"]["messages"] == [
        {"role": "user", "content": "测试提示词"}
    ]
    assert "extra_body" not in captured["request"]


def test_qwen_provider_uses_dashscope_endpoint(monkeypatch):
    captured = {}

    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.delenv("DACHUANG_QWEN_MODEL", raising=False)
    monkeypatch.setattr(llm_provider, "_read_local_env_value", lambda name: "", raising=False)
    _install_fake_openai(monkeypatch, captured)

    result = llm_provider.get_llm_provider("qwen").generate("测试提示词")

    assert result.text == "基于证据生成的答案"
    assert result.status == "success"
    assert captured["client"]["api_key"] == "test-key"
    assert captured["client"]["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert captured["request"]["model"] == "qwen-plus"
    assert captured["request"]["messages"] == [
        {"role": "user", "content": "测试提示词"}
    ]
    assert "extra_body" not in captured["request"]


def test_zhipu_provider_converts_exception_to_safe_status(monkeypatch):
    class FailingOpenAI:
        def __init__(self, **kwargs):
            raise RuntimeError("测试异常中可能包含敏感信息")

    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    monkeypatch.setattr(llm_provider, "OpenAI", FailingOpenAI, raising=False)

    result = llm_provider.get_llm_provider("zhipu").generate("测试提示词")

    assert result.text == ""
    assert result.provider_name == "zhipu"
    assert result.status == "provider_error"


def test_unknown_provider_keeps_stub_fallback():
    provider = llm_provider.get_llm_provider("unknown")

    assert provider.name == "stub"
