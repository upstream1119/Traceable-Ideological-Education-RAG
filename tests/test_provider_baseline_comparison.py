from types import SimpleNamespace

from scripts import run_provider_baseline_comparison as comparison


def test_load_queries_respects_limit(tmp_path):
    path = tmp_path / "queries.json"
    path.write_text(
        '[{"id":"q1","query":"问题1"},{"id":"q2","query":"问题2"}]',
        encoding="utf-8",
    )

    queries = comparison._load_queries(path, limit=1)

    assert queries == [{"id": "q1", "query": "问题1"}]


def test_compact_direct_result_marks_source_as_not_applicable():
    query_item = {"id": "q1", "query": "问题1"}
    provider_result = SimpleNamespace(
        text="普通模型回答",
        status="success",
    )

    row = comparison._compact_direct_result(
        "deepseek",
        query_item,
        provider_result,
    )

    assert row["run_type"] == "direct_baseline"
    assert row["provider"] == "deepseek"
    assert row["provider_status"] == "success"
    assert row["used_fallback"] is None
    assert row["citation_count"] == 0
    assert row["source_status"] == "not_applicable_no_retrieval"
    assert row["policy_status"] == "not_checked"
    assert row["final_decision"] == "not_applicable"


def test_compact_kg_rag_result_keeps_citation_and_review_status():
    query_item = {"id": "q1", "query": "问题1"}
    response = {
        "provider_status": "success",
        "used_fallback": False,
        "answer": "仅依据当前检索到的证据，回答正文。[1]",
        "citations_used": [{"id": "chunk_001"}],
        "source_check": {"status": "pass"},
        "policy_check": {"status": "pass"},
        "final_decision": {"status": "approved"},
    }

    row = comparison._compact_kg_rag_result("qwen", query_item, response)

    assert row["run_type"] == "kg_rag"
    assert row["provider"] == "qwen"
    assert row["provider_status"] == "success"
    assert row["used_fallback"] is False
    assert row["citation_count"] == 1
    assert row["source_status"] == "pass"
    assert row["policy_status"] == "pass"
    assert row["final_decision"] == "approved"


def test_summarize_group_counts_baseline_and_kg_rag_separately():
    rows = [
        {
            "run_type": "direct_baseline",
            "provider": "qwen",
            "provider_status": "success",
            "used_fallback": None,
            "source_status": "not_applicable_no_retrieval",
            "policy_status": "not_checked",
            "final_decision": "not_applicable",
            "citation_count": 0,
            "answer_length": 20,
        },
        {
            "run_type": "kg_rag",
            "provider": "qwen",
            "provider_status": "success",
            "used_fallback": False,
            "source_status": "pass",
            "policy_status": "pass",
            "final_decision": "approved",
            "citation_count": 2,
            "answer_length": 120,
        },
        {
            "run_type": "kg_rag",
            "provider": "qwen",
            "provider_status": "success",
            "used_fallback": False,
            "source_status": "pass",
            "policy_status": "warning",
            "final_decision": "needs_review",
            "citation_count": 2,
            "answer_length": 140,
        },
    ]

    direct = comparison._summarize_group(rows, "qwen", "direct_baseline")
    kg_rag = comparison._summarize_group(rows, "qwen", "kg_rag")

    assert direct["count"] == 1
    assert direct["success"] == 1
    assert direct["no_fallback"] == 0
    assert direct["answer_too_short"] == 1
    assert direct["source_pass"] == 0
    assert direct["needs_review"] == 0
    assert kg_rag["count"] == 2
    assert kg_rag["success"] == 2
    assert kg_rag["no_fallback"] == 2
    assert kg_rag["source_pass"] == 2
    assert kg_rag["policy_pass"] == 1
    assert kg_rag["approved"] == 1
    assert kg_rag["needs_review"] == 1
    assert kg_rag["answer_too_short"] == 0
