from src.api.main import RetrieveRequest, retrieve as api_retrieve
from src.retriever.hybrid_retriever import retrieve
from src.router.display_router import build_display_route


def test_knowledge_query_uses_evidence_cards():
    route = build_display_route(
        "马克思主义最初在中国如何传入？",
        ["马克思主义"],
    )

    assert route == {
        "intent_type": "knowledge_qa",
        "target_grade": None,
        "presentation_mode": "evidence_cards",
        "timeline_ids": [],
        "landmark_ids": [],
        "narrative_character": None,
    }


def test_party_foundation_query_returns_official_spatiotemporal_ids():
    route = build_display_route(
        "党的一大在哪里召开？请按时间和地点展示。",
        ["中国共产党", "思想政治教育"],
    )

    assert route["intent_type"] == "spatiotemporal"
    assert route["presentation_mode"] == "timeline_map"
    assert route["timeline_ids"] == ["timeline_sizheng_1921_foundation_001"]
    assert route["landmark_ids"] == ["landmark_1921_jiaxing_nanhu_001"]


def test_character_narrative_returns_primary_character_and_grade():
    route = build_display_route(
        "请面向高中生，以人物叙事方式介绍张闻天起草《党的宣传鼓动工作提纲》的背景和主要内容。",
        ["张闻天", "中共中央宣传部"],
    )

    assert route == {
        "intent_type": "character_narrative",
        "target_grade": "senior_high",
        "presentation_mode": "digital_human",
        "timeline_ids": [],
        "landmark_ids": [],
        "narrative_character": "张闻天",
    }


def test_explicit_target_grade_has_priority_over_query_inference():
    route = build_display_route(
        "请面向高中生介绍遵义会议。",
        ["遵义会议"],
        target_grade="university",
    )

    assert route["target_grade"] == "university"


def test_character_intent_without_known_character_falls_back_to_cards():
    route = build_display_route(
        "请使用人物叙事方式讲解这一历史事件。",
        [],
    )

    assert route["intent_type"] == "character_narrative"
    assert route["presentation_mode"] == "evidence_cards"
    assert route["narrative_character"] is None


def test_route_never_returns_proposed_timeline_ids():
    route = build_display_route(
        "请用时间线展示张闻天起草宣传鼓动工作提纲的过程。",
        ["张闻天"],
    )

    assert route["intent_type"] == "spatiotemporal"
    assert route["timeline_ids"] == []
    assert all(not item.startswith("proposed_timeline_") for item in route["timeline_ids"])


def test_empty_query_uses_safe_fallback():
    route = build_display_route("", [])

    assert route == {
        "intent_type": "unknown",
        "target_grade": None,
        "presentation_mode": "evidence_cards",
        "timeline_ids": [],
        "landmark_ids": [],
        "narrative_character": None,
    }


def test_retrieve_keeps_existing_contract_and_adds_display_route(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")

    result = retrieve(
        "请面向高中生介绍马克思主义最初在中国如何传入。",
        target_grade="senior_high",
    )

    assert result["hybrid_hits"]
    assert result["citations_used"]
    assert result["source_check"]
    assert result["policy_check"]
    assert result["agent_trace"]
    assert result["final_decision"]
    assert result["display_route"] == {
        "intent_type": "knowledge_qa",
        "target_grade": "senior_high",
        "presentation_mode": "evidence_cards",
        "timeline_ids": [],
        "landmark_ids": [],
        "narrative_character": None,
    }


def test_api_request_accepts_target_grade_and_returns_display_route(monkeypatch):
    monkeypatch.setenv("DACHUANG_RETRIEVE_MODE", "mock")
    monkeypatch.setenv("DACHUANG_LOCAL_MOCK_ACK", "1")
    payload = RetrieveRequest(
        query="请面向大学生，以人物叙事方式介绍张闻天。",
        target_grade="university",
    )

    result = api_retrieve(payload)

    assert payload.target_grade == "university"
    assert result["display_route"]["target_grade"] == "university"
    assert result["display_route"]["presentation_mode"] == "digital_human"
