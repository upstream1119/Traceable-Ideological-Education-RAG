INTENT_KNOWLEDGE_QA = "knowledge_qa"
INTENT_SPATIOTEMPORAL = "spatiotemporal"
INTENT_CHARACTER_NARRATIVE = "character_narrative"
INTENT_UNKNOWN = "unknown"

MODE_EVIDENCE_CARDS = "evidence_cards"
MODE_TIMELINE_MAP = "timeline_map"
MODE_DIGITAL_HUMAN = "digital_human"

VALID_TARGET_GRADES = {
    "primary",
    "junior_high",
    "senior_high",
    "university",
}

GRADE_QUERY_RULES = (
    (("小学生", "小学"), "primary"),
    (("初中生", "初中"), "junior_high"),
    (("高中生", "高中"), "senior_high"),
    (("大学生", "大学"), "university"),
)

CHARACTER_NARRATIVE_CUES = (
    "人物叙事",
    "数字人",
    "人物讲解",
    "第一人称",
    "人物视角",
)

SPATIOTEMPORAL_CUES = (
    "地图",
    "时间线",
    "时间轴",
    "时空",
    "路线",
    "在哪里",
    "什么地点",
    "哪些地点",
    "按时间",
    "按地点",
)

NARRATIVE_CHARACTERS = (
    "张闻天",
    "毛泽东",
    "周恩来",
    "刘少奇",
    "朱德",
    "李大钊",
    "陈独秀",
    "陈望道",
)

TIMELINE_RULES = (
    (("党的一大", "中共一大"), "timeline_sizheng_1921_foundation_001"),
    (("遵义会议",), "timeline_sizheng_1935_zunyi_002"),
    (("延安整风", "延安时期", "延安"), "timeline_sizheng_yanan_period_003"),
    (("抗日战争", "抗战时期", "全面抗战"), "timeline_sizheng_war_resistance_004"),
    (
        ("新中国成立", "七届二中全会", "两个务必", "西柏坡"),
        "timeline_sizheng_1949_new_china_005",
    ),
)

LANDMARK_RULES = (
    (("党的一大", "中共一大", "嘉兴南湖"), "landmark_1921_jiaxing_nanhu_001"),
    (("井冈山",), "landmark_1927_jinggangshan_002"),
    (("瑞金",), "landmark_1931_ruijin_003"),
    (("遵义会议", "遵义"), "landmark_1935_zunyi_004"),
    (("延安时期", "延安"), "landmark_1935_yanan_005"),
    (("七届二中全会", "两个务必", "西柏坡"), "landmark_1948_xibaipo_006"),
)


def _resolve_target_grade(query: str, target_grade: str | None) -> str | None:
    if target_grade in VALID_TARGET_GRADES:
        return target_grade
    for cues, grade in GRADE_QUERY_RULES:
        if any(cue in query for cue in cues):
            return grade
    return None


def _resolve_intent(query: str) -> str:
    if not query:
        return INTENT_UNKNOWN
    if any(cue in query for cue in CHARACTER_NARRATIVE_CUES):
        return INTENT_CHARACTER_NARRATIVE
    if any(cue in query for cue in SPATIOTEMPORAL_CUES):
        return INTENT_SPATIOTEMPORAL
    return INTENT_KNOWLEDGE_QA


def _resolve_narrative_character(query: str, query_entities: list[str]) -> str | None:
    content = " ".join([query, *query_entities])
    candidates = [name for name in NARRATIVE_CHARACTERS if name in content]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda name: query.find(name) if name in query else len(query),
    )


def _match_asset_ids(
    content: str,
    rules: tuple[tuple[tuple[str, ...], str], ...],
) -> list[str]:
    matched_ids = []
    for keywords, asset_id in rules:
        if any(keyword in content for keyword in keywords) and asset_id not in matched_ids:
            matched_ids.append(asset_id)
    return matched_ids


def build_display_route(
    query: str,
    query_entities: list[str],
    target_grade: str | None = None,
) -> dict:
    """生成前端可直接消费的确定性展示路由。"""
    query_text = (query or "").strip()
    entities = query_entities or []
    intent_type = _resolve_intent(query_text)
    resolved_grade = _resolve_target_grade(query_text, target_grade)

    narrative_character = None
    if intent_type == INTENT_CHARACTER_NARRATIVE:
        narrative_character = _resolve_narrative_character(query_text, entities)

    presentation_mode = MODE_EVIDENCE_CARDS
    if intent_type == INTENT_SPATIOTEMPORAL:
        presentation_mode = MODE_TIMELINE_MAP
    elif intent_type == INTENT_CHARACTER_NARRATIVE and narrative_character:
        presentation_mode = MODE_DIGITAL_HUMAN

    timeline_ids = []
    landmark_ids = []
    if presentation_mode == MODE_TIMELINE_MAP:
        route_content = " ".join([query_text, *entities])
        timeline_ids = _match_asset_ids(route_content, TIMELINE_RULES)
        landmark_ids = _match_asset_ids(route_content, LANDMARK_RULES)

    return {
        "intent_type": intent_type,
        "target_grade": resolved_grade,
        "presentation_mode": presentation_mode,
        "timeline_ids": timeline_ids,
        "landmark_ids": landmark_ids,
        "narrative_character": narrative_character,
    }
