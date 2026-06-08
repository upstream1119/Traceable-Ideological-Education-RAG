import json
import os
from functools import lru_cache
from pathlib import Path

from src.generator.evidence_generator import generate_answer
from src.graph.graph_store import (
    build_adjacency,
    build_relation_lookup,
    expand_entities,
    find_entity_paths,
    load_triples,
)
from src.reviewer.policy_checker import check_policy_risk
from src.reviewer.source_checker import check_answer_sources


PROJECT_NAME = "多智能体赋能的跨模态零幻觉交互式思政教育系统"
TEAM_MODE = "team"
MOCK_MODE = "mock"
VECTOR_TOP_K = 3
GRAPH_TOP_K = 3
ALPHA = 0.7
VECTOR_WEIGHT = ALPHA
GRAPH_WEIGHT = 1 - ALPHA
REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_CHUNKS_PATH = REPO_ROOT / "data" / "processed" / "text_chunks_demo.jsonl"
DEMO_TRIPLES_PATH = REPO_ROOT / "data" / "graph" / "triples_demo.jsonl"

# 当前阶段用固定词表演示 query -> entities 的流程，后续替换为真实实体识别。
MOCK_ENTITY_MAP = {
    "抗日战争时期党的干部教育": "干部教育",
    "党的干部教育": "干部教育",
    "干部教育": "干部教育",
    "遵义会议": "遵义会议",
    "长征": "长征",
    "毛泽东": "毛泽东",
    "与妻书": "与妻书",
    "林觉民": "林觉民",
    "抗日战争": "抗日战争",
    "抗战": "抗日战争",
    "嘉兴南湖": "嘉兴南湖",
    "井冈山": "井冈山",
    "延安": "延安",
    "红色家书": "红色家书",
    "家书": "红色家书",
    "精神": "革命精神",
    "革命精神": "革命精神",
    "张闻天": "张闻天",
    "宣传鼓动工作提纲": "党的宣传鼓动工作提纲",
    "党的宣传鼓动工作提纲": "党的宣传鼓动工作提纲",
    "中共中央宣传部": "中共中央宣传部",
    "新式整军运动": "新式整军运动",
    "人民解放军": "人民解放军",
    "国民党起义投诚部队": "国民党被俘、起义部队",
    "国民党投诚部队": "国民党被俘、起义部队",
    "起义投诚部队": "国民党被俘、起义部队",
    "国民党军队": "国民党军队",
    "马克思主义传播": "马克思主义",
    "党的一大": "党的一大",
    "三湾改编": "三湾改编",
}

RELATION_TYPE_WEIGHTS = {
    "起草": 0.22,
    "成立": 0.2,
    "任部长": 0.18,
    "确定": 0.18,
    "首创": 0.18,
    "采取": 0.16,
    "开展": 0.16,
    "服从": 0.16,
    "需要": 0.14,
    "传播": 0.14,
    "宣传": 0.14,
    "是": 0.1,
    "关联": 0.04,
}
DEFAULT_RELATION_WEIGHT = 0.08


def _count_keyword_hits(keywords: list[str], content: str) -> int:
    return sum(1 for keyword in keywords if keyword and keyword in content)


@lru_cache(maxsize=1)
def _load_demo_knowledge_base() -> list[dict]:
    if not DEMO_CHUNKS_PATH.exists():
        return []

    items: list[dict] = []
    with DEMO_CHUNKS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            item.setdefault("entities", [])
            item.setdefault("tags", [])
            item.setdefault("related_entities", item.get("entities", []))
            item.setdefault("topic", "")
            items.append(item)
    return items


@lru_cache(maxsize=1)
def _load_demo_triples() -> list[dict]:
    return load_triples(DEMO_TRIPLES_PATH)


@lru_cache(maxsize=1)
def _load_demo_adjacency() -> dict[str, list[str]]:
    return build_adjacency(_load_demo_triples())


@lru_cache(maxsize=1)
def _load_demo_relation_lookup() -> dict[tuple[str, str], str]:
    return build_relation_lookup(_load_demo_triples())


def _resolve_mode() -> str:
    requested_mode = os.getenv("DACHUANG_RETRIEVE_MODE", TEAM_MODE).strip().lower()
    local_ack = os.getenv("DACHUANG_LOCAL_MOCK_ACK", "").strip()
    if requested_mode == MOCK_MODE and local_ack == "1":
        return MOCK_MODE
    return TEAM_MODE


def extract_query_entities(query: str) -> list[str]:
    entities: list[str] = []
    for keyword, entity in MOCK_ENTITY_MAP.items():
        if keyword in query and entity not in entities:
            entities.append(entity)
    for item in _load_demo_knowledge_base():
        for entity in item.get("entities", []):
            if entity in query and entity not in entities:
                entities.append(entity)
    return entities


def _score_vector_hit(query: str, query_entities: list[str], item: dict) -> float:
    score = 0.0
    entities = item.get("entities", [])
    text = item.get("text", "")
    title = item.get("title", "")
    citation_section = item.get("citation", {}).get("section", "")
    tags = item.get("tags", [])
    topic = item.get("topic", "")

    if any(entity in entities for entity in query_entities):
        score += 0.55
    text_hits = _count_keyword_hits(query_entities, text)
    title_hits = _count_keyword_hits(query_entities, title)
    section_hits = _count_keyword_hits(query_entities, citation_section)
    score += min(text_hits * 0.18, 0.36)
    score += min(title_hits * 0.2, 0.4)
    score += min(section_hits * 0.12, 0.24)
    if any(tag in query for tag in tags):
        score += 0.1
    if topic and topic in query:
        score += 0.1
    if query and query in text:
        score += 0.15
    return min(score, 0.99)


def _build_search_content(item: dict) -> str:
    citation = item.get("citation", {})
    fields = [
        item.get("title", ""),
        item.get("text", ""),
        item.get("topic", ""),
        citation.get("section", ""),
        " ".join(item.get("entities", [])),
        " ".join(item.get("related_entities", [])),
    ]
    return " ".join(field for field in fields if field)


def _matched_entities(entities: list[str], content: str) -> list[str]:
    return [entity for entity in entities if entity and entity in content]


def _relation_weight(relation: str) -> float:
    for relation_type, weight in RELATION_TYPE_WEIGHTS.items():
        if relation_type in relation:
            return weight
    return DEFAULT_RELATION_WEIGHT


def _filter_valid_graph_paths(
    paths: list[dict],
    query_entities: list[str],
    related_entities: list[str],
) -> list[dict]:
    query_set = set(query_entities)
    related_set = set(related_entities)
    valid_paths: list[dict] = []

    for path in paths:
        nodes = path.get("path", [])
        relations = path.get("relations", [])
        hops = path.get("hops", 0)
        if not nodes or hops <= 0:
            continue
        if hops > 2 or len(nodes) != hops + 1 or len(relations) != hops:
            continue
        if nodes[0] not in query_set or nodes[-1] not in related_set:
            continue
        if len(set(nodes)) != len(nodes):
            continue
        valid_paths.append(path)

    return valid_paths


def _score_graph_paths(paths: list[dict]) -> float:
    score = 0.0
    for path in paths:
        hops = path.get("hops", 0)
        hop_score = 0.26 if hops == 1 else 0.16
        relation_score = sum(_relation_weight(relation) for relation in path.get("relations", []))
        score += hop_score + relation_score / max(hops, 1)
    return min(score, 0.3)


def _score_graph_hit(
    query_entities: list[str],
    expanded_entities: list[str],
    item: dict,
) -> tuple[float, list[str], list[dict]]:
    score = 0.0
    content = _build_search_content(item)
    direct_matches = _matched_entities(query_entities, content)
    expanded_matches = _matched_entities(
        [entity for entity in expanded_entities if entity not in query_entities],
        content,
    )

    score += min(len(direct_matches) * 0.34, 0.45)
    score += min(len(expanded_matches) * 0.06, 0.18)
    if direct_matches and expanded_matches:
        score += 0.05

    related_entities = []
    for entity in direct_matches + expanded_matches:
        if entity not in related_entities:
            related_entities.append(entity)

    graph_paths = _filter_valid_graph_paths(
        find_entity_paths(
            query_entities,
            related_entities,
            _load_demo_adjacency(),
            _load_demo_relation_lookup(),
            max_hops=2,
        ),
        query_entities,
        related_entities,
    )
    score += _score_graph_paths(graph_paths)

    return min(score, 0.99), related_entities, graph_paths


def retrieve_vector(query: str, query_entities: list[str], top_k: int = VECTOR_TOP_K) -> list[dict]:
    """
    第一路召回：向量语义召回 (Vector Retrieval)
    架构师视角：利用 Embedding 捕获文本的深层语义。优点是“懂同义词，泛化好”，缺点是“容易不够精准”。
    未来改造：接入真实的 Embedding 模型 + FAISS 向量数据库。
    """
    scored_hits = []
    for item in _load_demo_knowledge_base():
        score = _score_vector_hit(query, query_entities, item)
        if score <= 0:
            continue
        scored_hits.append(
            {
                "id": item["id"],
                "source": item["source"],
                "title": item["title"],
                "text": item["text"],
                "citation": item["citation"],
                "vector_score": round(score, 3),
            }
        )
    scored_hits.sort(key=lambda hit: hit["vector_score"], reverse=True)
    return scored_hits[:top_k]


def retrieve_graph(query_entities: list[str], top_k: int = GRAPH_TOP_K) -> list[dict]:
    """
    第二路召回：知识图谱召回 (Graph Retrieval)
    架构师视角：基于实体间的明确关系进行游走。优点是“极其精准，逻辑严密（零幻觉底座）”，缺点是“缺乏语义泛化”。
    未来改造：接入真实的 Neo4j 图数据库，使用 Cypher 语句查询 1-hop 或 2-hop 关系节点。
    """
    expanded_entities = expand_entities(
        query_entities,
        _load_demo_adjacency(),
        max_hops=2,
    )
    scored_hits = []
    for item in _load_demo_knowledge_base():
        score, related_entities, graph_paths = _score_graph_hit(
            query_entities,
            expanded_entities,
            item,
        )
        if score <= 0:
            continue
        scored_hits.append(
            {
                "id": item["id"],
                "related_entities": related_entities,
                "graph_paths": graph_paths,
                "graph_score": round(score, 3),
            }
        )
    scored_hits.sort(key=lambda hit: hit["graph_score"], reverse=True)
    return scored_hits[:top_k]


def fuse_results(vector_hits: list[dict], graph_hits: list[dict], knowledge_base: list[dict]) -> list[dict]:
    """
    融合层：多路召回合并与重排 (Reranking & Fusion)
    架构师视角：采用加权线性组合机制，兼顾“语义丰富度”与“事实准确性”。
    """
    vector_by_id = {hit["id"]: hit for hit in vector_hits}
    graph_by_id = {hit["id"]: hit for hit in graph_hits}
    fused_ids = sorted(set(vector_by_id) | set(graph_by_id)) # 取两路结果的并集（去重）
    hybrid_hits = []

    for hit_id in fused_ids:
        vector_hit = vector_by_id.get(hit_id)
        graph_hit = graph_by_id.get(hit_id)
        item = next(entry for entry in knowledge_base if entry["id"] == hit_id)
        vector_score = vector_hit["vector_score"] if vector_hit else 0.0
        graph_score = graph_hit["graph_score"] if graph_hit else 0.0
        # 核心打分公式：通过 VECTOR_WEIGHT(0.7) 和 GRAPH_WEIGHT(0.3) 调节双路比重，答辩时可强调此参数的可调优性。
        hybrid_score = round(
            vector_score * VECTOR_WEIGHT + graph_score * GRAPH_WEIGHT,
            3,
        )
        hybrid_hits.append(
            {
                "id": hit_id,
                "source": item["source"],
                "title": item["title"],
                "text": item["text"],
                "citation": item["citation"],
                "vector_score": vector_score,
                "graph_score": graph_score,
                "related_entities": graph_hit.get("related_entities", []) if graph_hit else [],
                "graph_paths": graph_hit.get("graph_paths", []) if graph_hit else [],
                "hybrid_score": hybrid_score,
            }
        )

    hybrid_hits.sort(key=lambda hit: hit["hybrid_score"], reverse=True)
    return hybrid_hits


def _build_response(
    query: str,
    query_entities: list[str],
    vector_hits: list[dict],
    graph_hits: list[dict],
    hybrid_hits: list[dict],
    generated: dict | None = None,
    source_check: dict | None = None,
    policy_check: dict | None = None,
) -> dict:
    generated = generated or {"answer": "", "citations_used": []}
    source_check = source_check or {
        "status": "no_evidence",
        "issues": [],
        "checked_citation_count": 0,
    }
    policy_check = policy_check or {
        "status": "need_review",
        "risk_types": ["not_checked"],
        "issues": ["政治红线审查尚未执行。"],
        "suggestion": "请执行 policy_check 后再输出。",
        "feedback_collection": {
            "stage": "not_started",
            "recommended_reviewer": "等待规则初筛。",
            "expert_review_priority": "high",
            "label_options": [],
        },
    }
    return {
        "status": "success",
        "project": PROJECT_NAME,
        "query": query,
        "query_entities": query_entities,
        "vector_hits": vector_hits,
        "graph_hits": graph_hits,
        "hybrid_hits": hybrid_hits,
        "answer": generated["answer"],
        "citations_used": generated["citations_used"],
        "source_check": source_check,
        "policy_check": policy_check,
    }


def retrieve(query: str) -> dict:
    """
    大组长总控台：混合检索的总编排器。
    不管底层逻辑以后怎么换，这里的 5 步固定流程（实体->向量->图谱->融合->组装）作为工程契约，绝对不能破！
    """
    query_text = (query or "").strip()
    mode = _resolve_mode()

    if mode == MOCK_MODE:
        # 标准双路召回流水线：
        knowledge_base = _load_demo_knowledge_base()
        query_entities = extract_query_entities(query_text)
        vector_hits = retrieve_vector(query_text, query_entities)
        graph_hits = retrieve_graph(query_entities)
        hybrid_hits = fuse_results(vector_hits, graph_hits, knowledge_base)
    else:
        query_entities = []
        vector_hits, graph_hits, hybrid_hits = [], [], []

    generated = generate_answer(query_text, hybrid_hits)
    source_check = check_answer_sources(
        generated["answer"],
        generated["citations_used"],
    )
    policy_check = check_policy_risk(
        generated["answer"],
        generated["citations_used"],
        source_check,
    )

    return _build_response(
        query=query_text,
        query_entities=query_entities,
        vector_hits=vector_hits,
        graph_hits=graph_hits,
        hybrid_hits=hybrid_hits,
        generated=generated,
        source_check=source_check,
        policy_check=policy_check,
    )
