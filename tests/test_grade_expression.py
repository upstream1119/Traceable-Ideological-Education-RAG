import pytest

from src.reviewer.semantic_checker import (
    EvidenceAlignmentError, build_teaching_review_prompt,
    expand_grade_support_context, validate_grade_expression,
)
import json
from src.generator.grade_profiles import focus_grade_evidence


def paragraphs(*texts):
    return [{"text": text, "supports": []} for text in texts]


@pytest.mark.parametrize("text", [
    "遵义会议统一了思想，让正确路线武装了大家。",
    "红军通过统一思想，为长征胜利奠定了思想基础。",
    "遵义会议通过" + "传达会议精神并组织大家学习" * 7 + "发挥作用。",
])
def test_primary_rejects_unexplained_abstraction_or_overlong_sentence(text):
    with pytest.raises(EvidenceAlignmentError):
        validate_grade_expression(paragraphs(text), "primary")


def test_primary_accepts_explained_concept_without_rewriting_answer():
    value = paragraphs("红军逐级传达会议精神，让干部和战士对共同的目标形成一致认识。")
    original = value[0]["text"]
    validate_grade_expression(value, "primary")
    assert value[0]["text"] == original
    validate_grade_expression(paragraphs("统一思想，就是对共同的目标形成一致认识。"), "primary")


def test_primary_rejects_excessive_paragraphs_and_dangling_opening():
    for value in (paragraphs("第一段。", "第二段。", "第三段。"),
                  paragraphs("这些胜利说明了教育的作用。")):
        with pytest.raises(EvidenceAlignmentError):
            validate_grade_expression(value, "primary")


def test_unselected_grade_preserves_existing_behavior():
    value = paragraphs("这些胜利使正确路线武装了头脑。" * 30)
    validate_grade_expression(value, None)
    validate_grade_expression(value, "unknown")


def test_senior_and_university_can_use_academic_terms_within_limits():
    value = paragraphs("逐级传达会议精神有助于统一思想；具体作用需要结合材料中的行动与主体分析。")
    validate_grade_expression(value, "senior_high")
    validate_grade_expression(value, "university")


def test_review_separates_learner_text_from_original_supports():
    value = [{"text": "大家对共同目标有了一致认识。", "supports": [
        {"evidence_number": 1, "quote": "统一思想是紧迫任务。"}]}]
    prompt = build_teaching_review_prompt("问题", value, [{"text": "统一思想是紧迫任务。"}], "primary")
    payload = json.loads(prompt.split("\n\n", 1)[1])
    assert payload["answer_paragraphs"] == [{"paragraph": 1, "text": value[0]["text"]}]
    assert payload["support_context"][0]["supports"] == value[0]["supports"]
    assert "supports" not in payload["answer_paragraphs"][0]


def test_context_stays_in_cited_chunk_preserves_text_and_does_not_mutate_original():
    value = [{"text": "回答。", "supports": [{"evidence_number": 1, "quote": "第二句。"}]}]
    result = expand_grade_support_context(value, [{"text": "第一句。第二句。第三句。"}, {"text": "其他材料。"}])
    assert result[0]["text"] == value[0]["text"]
    assert len(value[0]["supports"]) == 1
    assert {support["quote"] for support in result[0]["supports"]} == {"第一句。", "第二句。", "第三句。"}
    assert {support["evidence_number"] for support in result[0]["supports"]} == {1}


def test_single_event_focus_excludes_background_but_composite_keeps_both():
    hits = [{"id": "meeting", "title": "传达贯彻遵义会议精神"},
            {"id": "background", "title": "宣传民族政策"}]
    entities = ["遵义会议", "思想政治教育"]
    assert focus_grade_evidence("遵义会议如何发挥思想政治教育作用？", hits, entities) == hits[:1]
    assert focus_grade_evidence("结合遵义会议与长征精神说明作用。", hits, entities) == hits
    assert focus_grade_evidence("思想政治教育有哪些作用？", hits, ["思想政治教育"]) == hits


def test_junior_definition_is_not_a_result_of_military_victory():
    with pytest.raises(EvidenceAlignmentError):
        validate_grade_expression(paragraphs("这些实践证明了正确路线指的是符合实际的方针。"), "junior_high")
    validate_grade_expression(paragraphs("正确路线指的是材料中的正确方针。红军逐级传达会议精神。"), "junior_high")
