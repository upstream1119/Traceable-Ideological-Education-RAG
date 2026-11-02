import json

import pytest

from src.reviewer.semantic_checker import EvidenceAlignmentError, validate_grounded_passages


SOURCE = "红军展现了革命英雄主义气概。思想政治教育无愧于红军的生命线。"
HITS = [{"text": SOURCE}]


def test_accepts_single_complete_json_fence():
    payload = json.dumps({"passages": [{"evidence_number": 1, "quote": SOURCE}]})
    for wrapped in [f"```json\n{payload}\n```", f" \n```json\r\n{payload}\r\n```\n "]:
        assert validate_grounded_passages(wrapped, HITS) == [{"evidence_number": 1, "quote": SOURCE}]


@pytest.mark.parametrize("wrapper", [
    "解释：```json\n%s\n```", "```json\n%s\n```\n额外结论",
    "```python\n%s\n```", "```json\n%s", "```json\n%s\n```\n```json\n{}\n```",
])
def test_rejects_non_json_content_outside_fence(wrapper):
    payload = json.dumps({"passages": [{"evidence_number": 1, "quote": SOURCE}]})
    with pytest.raises(EvidenceAlignmentError):
        validate_grounded_passages(wrapper % payload, HITS)


@pytest.mark.parametrize("passage", [
    {"evidence_number": 1, "quote": "编造原文。"},
    {"evidence_number": 99, "quote": SOURCE},
    {"evidence_number": 1, "quote": SOURCE, "explanation": "额外结论"},
])
def test_fence_does_not_bypass_evidence_validation(passage):
    with pytest.raises(EvidenceAlignmentError):
        validate_grounded_passages("```json\n" + json.dumps({"passages": [passage]}) + "\n```", HITS)


@pytest.mark.parametrize("payload", [
    "not json", "[]", '{}',
    '{"passages": []}',
    '{"passages": [{"evidence_number": true, "quote": "红军展现了革命英雄主义气概。"}]}',
    '{"passages": [{"evidence_number": 0, "quote": "红军展现了革命英雄主义气概。"}]}',
    '{"passages": [{"evidence_number": 99, "quote": "红军展现了革命英雄主义气概。"}]}',
    '{"passages": [{"evidence_number": 1, "quote": "展现了革命英雄主义气概。"}]}',
    '{"passages": [{"evidence_number": 1, "quote": "红军展现了革命英雄主义气概"}]}',
    '{"passages": [{"evidence_number": 1, "quote": "长征精神无愧于红军的生命线。"}]}',
    '{"passages": [{"evidence_number": 1, "quote": "红军展现了革命英雄主义气概。", "claim": "因此军事胜利"}]}',
    '{"passages": [{"evidence_number": 1, "quote": ""}]}',
])
def test_rejects_unverified_or_partial_claims(payload):
    with pytest.raises(EvidenceAlignmentError):
        validate_grounded_passages(payload, HITS)


@pytest.mark.parametrize("quote", [SOURCE, "红军展现了革命英雄主义气概。", "思想政治教育无愧于红军的生命线。"])
def test_accepts_complete_original_sentences_with_subject(quote):
    payload = json.dumps({"passages": [{"evidence_number": 1, "quote": quote}]})
    assert validate_grounded_passages(payload, HITS) == [{"evidence_number": 1, "quote": quote}]


def test_rejects_repeated_passages():
    passage = {"evidence_number": 1, "quote": SOURCE}
    with pytest.raises(EvidenceAlignmentError):
        validate_grounded_passages(json.dumps({"passages": [passage, passage]}), HITS)


@pytest.mark.parametrize("quote", ["思想政治教育无愧于", "红军展现了革命英雄主义气概。思想政治教育无愧于"])
def test_rejects_unterminated_tail_even_when_it_matches_source(quote):
    hits = [{"text": "红军展现了革命英雄主义气概。思想政治教育无愧于"}]
    with pytest.raises(EvidenceAlignmentError):
        validate_grounded_passages(json.dumps({"passages": [{"evidence_number": 1, "quote": quote}]}), hits)


def test_accepts_complete_sentence_before_unterminated_tail():
    quote = "红军展现了革命英雄主义气概。"
    hits = [{"text": quote + "思想政治教育无愧于"}]
    assert validate_grounded_passages(json.dumps({"passages": [{"evidence_number": 1, "quote": quote}]}), hits) == [{"evidence_number": 1, "quote": quote}]


def test_leading_punctuation_cannot_shift_sentence_boundaries():
    hits = [{"text": "。甲乙。"}]
    with pytest.raises(EvidenceAlignmentError):
        validate_grounded_passages(json.dumps({"passages": [{"evidence_number": 1, "quote": "。甲乙"}]}), hits)
    assert validate_grounded_passages(json.dumps({"passages": [{"evidence_number": 1, "quote": "甲乙。"}]}), hits) == [{"evidence_number": 1, "quote": "甲乙。"}]
