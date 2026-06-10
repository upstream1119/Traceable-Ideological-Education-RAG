from src.generator.evidence_generator import generate_answer


def _hit(
    *,
    hit_id: str = "chunk_test_001",
    title: str = "测试证据",
    text: str = "思想政治教育需要依据具体历史材料展开。",
    hybrid_score: float = 0.9,
) -> dict:
    return {
        "id": hit_id,
        "source": "中国共产党思想政治教育史",
        "title": title,
        "text": text,
        "citation": {
            "doc": "中国共产党思想政治教育史",
            "section": "测试章节",
            "page": 1,
        },
        "hybrid_score": hybrid_score,
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


def test_template_answer_is_compact_and_citation_grounded(monkeypatch):
    monkeypatch.delenv("DACHUANG_GENERATOR_MODE", raising=False)

    result = generate_answer(
        "思想政治教育为什么重要？",
        [
            _hit(),
            _hit(
                hit_id="chunk_test_002",
                title="无关补充证据",
                text="这是一条不应进入模板回答的低分候选。",
                hybrid_score=0.1,
            ),
        ],
    )

    assert "引用依据" in result["answer"]
    assert "来源：" in result["answer"]
    assert "PDF 页码" in result["answer"]
    assert "仅依据当前检索到的证据" in result["answer"]
    assert "无关补充证据" not in result["answer"]
    assert len(result["citations_used"]) == 1
    assert len(result["answer"]) < 700


def test_template_answer_prefers_complete_sentence_boundary(monkeypatch):
    monkeypatch.delenv("DACHUANG_GENERATOR_MODE", raising=False)
    long_text = (
        "第一句话用于说明核心结论，并且已经完整结束。"
        + "第二句话包含大量补充说明，" * 30
    )

    result = generate_answer("测试长文本截断。", [_hit(text=long_text)])

    assert "第一句话用于说明核心结论，并且已经完整结束。" in result["answer"]
    assert "第二句话包含大量补充说明，第二句话" not in result["answer"]
