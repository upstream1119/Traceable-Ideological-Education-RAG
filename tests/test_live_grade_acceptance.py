import json
import os

import pytest

from scripts import run_live_grade_acceptance as runner
from src.generator import llm_provider


def configure(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-not-a-real-key")
    monkeypatch.setenv("DACHUANG_QWEN_MODEL", "test-model")
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "template")


def test_default_preflight_never_calls_provider_and_restores_mode(monkeypatch, tmp_path):
    configure(monkeypatch)

    def forbidden(*args):
        raise AssertionError("离线预检不允许调用Provider")

    monkeypatch.setattr(llm_provider.QwenLLMProvider, "generate", forbidden)
    report = runner.run(tmp_path)
    assert report["completed_cases"] == 10
    assert report["external_request_attempts"] == 0
    assert report["online_generated_without_fallback"] == 0
    assert os.environ["DACHUANG_GENERATOR_MODE"] == "template"
    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    assert plan["planned_max_calls"] == 20
    assert "test-not-a-real-key" not in (tmp_path / "plan.json").read_text(encoding="utf-8")


def test_call_budget_stops_before_an_extra_provider_request(monkeypatch, tmp_path):
    configure(monkeypatch)
    attempts = []

    def fake_generate(self, prompt):
        attempts.append(prompt)
        return llm_provider.LLMGenerationResult("", "qwen", "empty_response")

    monkeypatch.setattr(llm_provider.QwenLLMProvider, "generate", fake_generate)
    with pytest.raises(RuntimeError, match="调用上限"):
        runner.run(tmp_path, execute=True, max_calls=1)
    assert len(attempts) == 1
    assert (tmp_path / "call-01.json").exists()
    assert (tmp_path / "v1qa_004_primary.json").exists()
    assert os.environ["DACHUANG_GENERATOR_MODE"] == "template"


def test_authentication_failure_stops_remaining_cases(monkeypatch, tmp_path):
    configure(monkeypatch)
    monkeypatch.setattr(llm_provider.QwenLLMProvider, "generate", lambda self, prompt:
                        llm_provider.LLMGenerationResult("", "qwen", "provider_auth_error"))
    report = runner.run(tmp_path, execute=True)
    assert report["stopped_early"] is True
    assert report["completed_cases"] == 1
    assert report["external_request_attempts"] == 1


def test_targeted_retest_only_prepares_selected_case(monkeypatch, tmp_path):
    configure(monkeypatch)
    report = runner.run(tmp_path, case_ids=["v1qa_022"])
    assert report["completed_cases"] == 1
    assert report["external_request_attempts"] == 0
    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    assert plan["planned_max_calls"] == 2
    assert plan["cases"][0]["id"] == "v1qa_022"
