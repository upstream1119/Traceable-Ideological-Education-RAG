from src.retriever.section_reranker import rerank_hits_by_query_terms


def test_section_reranker_prefers_specific_long_march_section():
    query = "长征中红军如何通过政治动员鼓舞士气？"
    hits = [
        {
            "id": "anti_encirclement",
            "title": "进行政治动员鼓舞士气",
            "text": "政治动员服务于反围剿斗争。",
            "citation": {
                "section": (
                    "第二章 / 第三节 红军反围剿斗争和长征中的思想政治教育"
                    " / 一、思想政治教育为反围剿斗争服务"
                )
            },
            "vector_score": 0.787204,
        },
        {
            "id": "long_march",
            "title": "深入开展政治动员，激发官兵革命斗志",
            "text": "红军长征中的思想政治教育重视政治动员。",
            "citation": {
                "section": (
                    "第二章 / 第三节 红军反围剿斗争和长征中的思想政治教育"
                    " / 三、红军长征中的思想政治教育"
                )
            },
            "vector_score": 0.763164,
        },
    ]

    reranked = rerank_hits_by_query_terms(query, hits)

    assert reranked[0]["id"] == "long_march"
    assert reranked[0]["base_vector_score"] == 0.763164
    assert reranked[0]["rerank_boost"] > 0
