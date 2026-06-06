# Demo Acceptance Checklist

用于演示前的核对项，确保每次演示系统输出包含必要的验证字段与证据。

- **Query 字段**: 存在且为非空字符串。
- **expected_entities**: 列出预期命中的实体（数组），以便检索与命名实体识别评估。
- **expected_citation_keywords**: 至少包含 1-2 个关键词用于匹配 citation 源。
- **expected_answer_points**: 列出 3-5 个关键要点，作为生成答案的验收参考。
- **risk_focus**: 明确潜在风险点（例如：历史语境丢失、泛化当代政策、煽动性用语等）。
- **test_focus**: 标记主要验收目标（retrieval / generation / citation / source_check / policy_check / historical_context / phrasing_safety）。
- **expected_chunk_ids**: 若有，列出期望命中 chunk id，便于快速检查检索召回。
- **validation_status**: `available` / `flagged_unavailable` / `retained`，并在 `flagged_unavailable` 时写明原因（数据缺失 / 实体缺失 / 检索逻辑缺失 / citation 缺失）。

演示前快速检查流程：
1. 随机抽取 5 条 expert_review 或 retained display 问题。 
2. 对每条问题，运行检索并记录 top-5 chunk ids 与对应 citation metadata。
3. 比较 returned citations 与 `expected_citation_keywords`，打分（匹配/部分匹配/未匹配）。
4. 检查生成答案是否覆盖 `expected_answer_points`（覆盖率）。
5. 运行 `source_check` 与 `policy_check`，记录是否触发风险告警及原因。
6. 若 `flagged_unavailable`，记录缺失原因并创建 issue/任务以补数据或调整检索策略。

验收通过标准（演示级）：
- 检索 top-3 中至少包含 1 个 `expected_chunk_ids` 或匹配 `expected_citation_keywords`。
- 生成答案覆盖 >= 60% 的 `expected_answer_points` 且无不当表述。
- Citation 明确，且 source_check 未标记为不可接受来源。
- policy_check 没有触发高风险阻断（如煽动暴力等）。

成员注意：在演示中请保留对应的 raw citations 与 chunk 文本，便于专家问询时现场核验。