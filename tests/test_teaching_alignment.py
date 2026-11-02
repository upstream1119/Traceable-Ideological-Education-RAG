import json

import pytest

from src.reviewer.semantic_checker import EvidenceAlignmentError, build_teaching_prompt, validate_teaching_answer


def payload(quote, number=1):
    return json.dumps({"paragraphs": [{"text": "有依据的解释。", "supports": [{"evidence_number": number, "quote": quote}]}]})


def test_partial_exact_clause_is_expanded_to_its_original_complete_sentence():
    source = "总政治部强调：要严格纪律；要尊重群众；要做好宣传。后续另述。"
    result = validate_teaching_answer(payload("要尊重群众；要做好宣传。"), [{"text": source}])
    assert result[0]["supports"] == [{"evidence_number": 1, "quote": "总政治部强调：要严格纪律；要尊重群众；要做好宣传。"}]


def test_wrong_model_number_is_repaired_only_from_unique_exact_text():
    result = validate_teaching_answer(payload("干部逐级传达会议精神。", 6), [
        {"text": "要尊重群众。"}, {"text": "干部逐级传达会议精神。"}])
    assert result[0]["supports"] == [{"evidence_number": 2, "quote": "干部逐级传达会议精神。"}]


@pytest.mark.parametrize("quote,hits", [
    ("伪造的引文。", [{"text": "真实的材料。"}]),
    ("尊重群众。", [{"text": "必须尊重群众。"}, {"text": "需要尊重群众。"}]),
    ("尊重群众", [{"text": "需要尊重群众"}]),
])
def test_absent_ambiguous_or_unterminated_source_remains_rejected(quote, hits):
    with pytest.raises(EvidenceAlignmentError):
        validate_teaching_answer(payload(quote, 99), hits)


def test_server_sentence_identifiers_resolve_to_exact_originals_without_model_copying():
    hits = [{"text": "第一句。第二句：要尊重群众；要做好宣传。"}, {"text": "干部逐级传达精神。"}]
    prompt = build_teaching_prompt("问题", hits)
    assert 'E2S1' in prompt
    answer = json.dumps({"paragraphs": [{"text": "逐级传达有助于统一认识。", "supports": [{"quote_id": "E2S1"}]}]})
    assert validate_teaching_answer(answer, hits)[0]["supports"] == [{"evidence_number": 2, "quote": "干部逐级传达精神。"}]
    with pytest.raises(EvidenceAlignmentError):
        validate_teaching_answer(answer.replace("E2S1", "E3S1"), hits)


def test_composite_paragraph_can_cite_several_complete_sentences_but_has_a_bound():
    hits = [{"text": "甲说明。乙说明。丙说明。丁说明。戊说明。己说明。庚说明。辛说明。壬说明。"}]
    paragraph = {"text": "多个方面的解释。", "supports": [{"quote_id": f"E1S{i}"} for i in range(1, 6)]}
    assert len(validate_teaching_answer(json.dumps({"paragraphs": [paragraph]}), hits)[0]["supports"]) == 5
    paragraph["supports"] = [{"quote_id": f"E1S{i}"} for i in range(1, 10)]
    with pytest.raises(EvidenceAlignmentError):
        validate_teaching_answer(json.dumps({"paragraphs": [paragraph]}), hits)


def test_known_internal_sentence_markers_become_supports_not_display_citations():
    hits = [{"text": "第一句。第二句。"}]
    answer = {"paragraphs": [{"text": "解释。[E1S2]", "supports": [{"quote_id": "E1S1"}]}]}
    checked = validate_teaching_answer(json.dumps(answer), hits)
    assert checked[0]["text"] == "解释。"
    assert {s["quote"] for s in checked[0]["supports"]} == {"第一句。", "第二句。"}
    answer["paragraphs"][0]["text"] = "解释。[E99S1]"
    with pytest.raises(EvidenceAlignmentError):
        validate_teaching_answer(json.dumps(answer), hits)
