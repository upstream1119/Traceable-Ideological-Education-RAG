import json
import os
from functools import lru_cache
from pathlib import Path

from src.generator.evidence_generator import generate_answer
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
}


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


def _score_graph_hit(query_entities: list[str], item: dict) -> float:
    score = 0.0
    entities = item.get("entities", [])
    related_entities = item.get("related_entities", entities)

    overlap = sum(1 for entity in query_entities if entity in entities)
    score += overlap * 0.45
    related_overlap = sum(1 for entity in query_entities if entity in related_entities)
    score += related_overlap * 0.15
    if overlap > 0 and related_entities:
        score += 0.2
    return min(score, 0.99)


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
    scored_hits = []
    for item in _load_demo_knowledge_base():
        score = _score_graph_hit(query_entities, item)
        if score <= 0:
            continue
        scored_hits.append(
            {
                "id": item["id"],
                "related_entities": item.get("related_entities", item.get("entities", [])),
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
