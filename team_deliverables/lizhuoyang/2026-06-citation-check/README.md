# 2026-06 Citation Check 交付说明

## 本次范围

- 复核 `data/processed/text_chunks_demo.jsonl` 40 条 demo chunk 的 `citation.page`、`source`、`title`、`section`。
- 明确页码口径：`citation.page` 统一表示 PDF 阅读器中的物理页码，不是书本印刷页码。
- 生成最小页码映射表，覆盖 40 条 chunk。
- 优先抽查核心演示题相关 chunk：张闻天、干部教育、马克思主义传入、党的一大、长征政治动员。
- 补充并修正 40 条 chunk 的 `entities`、`tags`、`topic`，方便后续 GraphSim 和检索。
- 根据核心题检索回退反馈，恢复 `chunk_szzjys_demo_025` 的“宣传工作”实体，并收窄高频泛化实体/标签。
- 新增 `data/processed/text_chunks_sizheng_v1.jsonl` 20 条扩库 sample，用于后续知识库扩展验收；当前尚未达到 100-200 条第一轮扩库目标。

## 文件清单

- `citation_page_check.md`：页码口径、抽查结论、核心演示题 chunk 清单。
- `page_mapping_draft.csv`：40 条 chunk 的 PDF 页码、书本页码、确认状态和备注。
- `scripts/enrich_demo_chunks.py`：本次 JSONL 结构化字段修正和 CSV 生成脚本。

关联正式数据：

- `data/processed/text_chunks_sizheng_v1.jsonl`：20 条第一批扩库 sample，已随本次分支提交；该文件属于系统后续可能读取的数据资产，不放入 `team_deliverables/`。

## 已修改正式数据

- `data/processed/text_chunks_demo.jsonl`

修改内容：

- 将 3 条跨页 chunk 的 `citation.page` 改为 chunk 正文起始所在 PDF 页：
  - `chunk_szzjys_demo_004`：30 -> 29
  - `chunk_szzjys_demo_012`：75 -> 74
  - `chunk_szzjys_demo_034`：174 -> 173
- 逐条补充或修正 `entities`、`tags`、`topic`。
- 去掉公共 tag 中的“思想政治教育史”，过滤 exact 的“中国共产党”“思想政治教育”“马克思主义”等高频泛化实体；保留更具体的事件、文献、组织和主题词。
- 未修改 `id`、`text`、`source`、`title`、`citation.doc`、`citation.section`。

## 页码口径

`citation.page` 为 PDF 物理页码，1-based。MinerU JSON 中的 `page_idx` 是 0-based，所以：

`citation.page = page_idx + 1`

本教材正文区间的书本印刷页码与 PDF 页码关系为：

`书本页码 = PDF 页码 - 14`

该偏移由 PDF 第 16 页页脚为书本第 2 页、PDF 第 25 页页脚为书本第 11 页、PDF 第 200 页页脚为书本第 186 页确认。

## 新资料清洗状态

本次已新增 `data/processed/text_chunks_sizheng_v1.jsonl` 20 条扩库 sample，作为第一批知识库扩展示例；当前尚未达到 100-200 条第一轮扩库目标，也不是全量知识库。

后续继续扩展资料时，仍按每批 10-20 条 sample 提交，并在交付说明中写清来源、清洗方式、页码口径和未确认项。
