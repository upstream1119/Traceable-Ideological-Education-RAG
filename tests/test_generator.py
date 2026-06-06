from src.generator.evidence_generator import generate_answer


def _hit() -> dict:
    return {
        "id": "chunk_test_001",
        "source": "中国共产党思想政治教育史",
        "title": "测试证据",
        "text": "思想政治教育需要依据具体历史材料展开。",
        "citation": {
            "doc": "中国共产党思想政治教育史",
            "section": "测试章节",
            "page": 1,
        },
        "hybrid_score": 0.9,
    }


def test_template_generator_mode_is_default(monkeypatch):
    monkeypatch.delenv("DACHUANG_GENERATOR_MODE", raising=False)

    result = generate_answer("思想政治教育为什么重要？", [_hit()])

    assert result["generator_mode"] == "template"
    assert result["answer"]
    assert result["citations_used"]
    assert "prompt_preview" not in result


def test_llm_mode_keeps_contract_and_builds_prompt(monkeypatch):
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "llm")

    result = generate_answer("思想政治教育为什么重要？", [_hit()])

    assert result["generator_mode"] == "llm"
    assert result["generator_provider"] == "stub"
    assert result["provider_status"] == "stub_no_external_call"
    assert result["answer"]
    assert result["citations_used"]
    assert "只能依据给定证据回答" in result["prompt_preview"]
    assert "思想政治教育需要依据具体历史材料展开" in result["prompt_preview"]


def test_unknown_generator_mode_falls_back_to_template(monkeypatch):
    monkeypatch.setenv("DACHUANG_GENERATOR_MODE", "unknown")

    result = generate_answer("思想政治教育为什么重要？", [_hit()])

    assert result["generator_mode"] == "template"
    assert result["answer"]
