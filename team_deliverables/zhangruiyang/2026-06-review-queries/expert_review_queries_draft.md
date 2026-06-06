# Expert Review Queries — Draft (2026-06)

本文件包含第一版专家审查问题草案（共 12 条），每题包含必要的验收字段（query、expected_entities、expected_citation_keywords、expected_answer_points、risk_focus、test_focus、expected_chunk_ids、validation_status）。

以下为 JSON 结构化表示（仅包含 expert_* 条目，便于工程化导入与校验）：

```json
[
  {
    "id": "expert_001",
    "type": "expert_review",
    "category": "思政史",
    "query": "张闻天起草的宣传鼓动工作提纲强调了什么？",
    "expected_entities": ["张闻天", "中共中央宣传部", "宣传鼓动工作提纲"],
    "expected_citation_keywords": ["中国共产党思想政治教育史"],
    "expected_answer_points": [
      "宣传与鼓动的定义及区别",
      "党内教育与群众教育的分工",
      "宣传鼓动任务是宣传马列主义和党的纲领",
      "用群众熟悉的事实与切身问题进行解释"
    ],
    "risk_focus": ["是否脱离抗日战争时期语境", "是否泛化为当代宣传工作"],
    "test_focus": ["retrieval", "citation", "policy_check", "generation"],
    "expected_chunk_ids": ["chunk_szzjys_demo_025"],
    "validation_status": "available"
  },
  {
    "id": "expert_002",
    "type": "expert_review",
    "category": "思政史",
    "query": "三湾改编对人民军队建设有哪些具体影响？",
    "expected_entities": ["三湾改编", "人民军队"],
    "expected_citation_keywords": ["三湾改编", "人民军队初创时期"],
    "expected_answer_points": [
      "支部建连，强化党对军队的领导",
      "实行官兵平等并整肃军风",
      "用思想作风整顿提高部队凝聚力"
    ],
    "risk_focus": ["是否把当时军事组织原则当今化解释", "是否夸大暴力或鼓动内容"],
    "test_focus": ["retrieval", "generation", "historical_context", "policy_check"],
    "expected_chunk_ids": ["chunk_szzjys_demo_012"],
    "validation_status": "available"
  }
  // 其余条目已写入 tests/demo_queries_sizheng_history.json
]
```

备注：完整 JSON 已同步写入 `tests/demo_queries_sizheng_history.json`，本文件以示例形式保留便于人工审阅。可根据需要将全部条目以表格或 CSV 导出。