# 思政知识库 Chunk 入库标准 v1

> 适用范围：教材、课件、论文、政策文献、党史材料等进入项目知识库前的清洗、切分、溯源和验收。
> 当前阶段：6 月三智能体闭环与政治红线审查阶段。

## 1. 入库目标

知识库扩充不是单纯追求数量，而是保证每条 chunk 都能支撑后续检索、生成、溯源审查和政治红线审查。

每条 chunk 必须满足：

- 可追溯：能定位来源文档、章节、PDF 页码，或明确说明页码暂缺原因。
- 可检索：具备清晰的 `topic`、`entities` 和 `tags`。
- 可审查：能支撑回答中的核心结论，方便后续 `source_check` 和 `policy_check` 检查。
- 可复现：能通过 JSONL 校验，并能被当前 `/retrieve` 链路读取或后续索引脚本处理。

## 2. 文件分层

```text
data/raw/          // 原始资料索引或小样本；大型 PDF 不直接进仓库
data/interim/      // OCR、MinerU、人工清洗中间结果
data/processed/    // 系统正式读取的 chunks
data/graph/        // triples、图结构、GraphSim 数据
```

当前稳定 Demo 数据为：

```text
data/processed/text_chunks_demo.jsonl
```

当前思政史扩库批次为：

```text
data/processed/text_chunks_sizheng_v1.jsonl
data/processed/text_chunks_sizheng_v2.jsonl
```

后续扩库建议继续新建版本文件，不要直接覆盖稳定 Demo 文件或已合并批次，例如：

```text
data/processed/text_chunks_sizheng_v3.jsonl
```

## 3. 每条 chunk 必填字段

每行 JSONL 必须至少包含：

```json
{
  "id": "chunk_szzjys_v1_001",
  "source": "中国共产党思想政治教育史",
  "source_type": "textbook",
  "title": "马克思学说在中国的最初传入",
  "text": "清洗后的正文片段。",
  "chunk_type": "textbook_chunk",
  "topic": "马克思主义传播",
  "entities": ["马克思主义", "中国共产党"],
  "tags": ["思想政治教育史", "理论传播"],
  "citation": {
    "doc": "中国共产党思想政治教育史",
    "section": "第一章 / 第一节 / 一、马克思学说在中国的最初传入",
    "page": 25
  }
}
```

## 4. 字段填写规则

### `id`

- 必须全局唯一。
- 建议格式：`chunk_资料缩写_版本_序号`。
- 示例：`chunk_szzjys_v1_001`。

### `source`

- 写资料名称，不写临时备注。
- 示例：`中国共产党思想政治教育史`。

### `source_type`

当前允许：

- `event_doc`：党史大事记、事件资料。
- `textbook`：教材。
- `courseware`：课件。
- `paper`：论文。
- `policy_doc`：政策文件、规范文件。
- `letter`：书信、家书。
- `landmark`：地标资料。
- `exam`：题库、考试材料。

### `chunk_type`

当前允许：

- `event`
- `textbook_chunk`
- `courseware_chunk`
- `paper_chunk`
- `policy_chunk`
- `narrative`
- `qa`
- `landmark`

### `text`

- 必须是清洗后的正文。
- 不允许保留页眉页脚、目录噪声、乱码、重复段落。
- 单条 chunk 应表达一个相对完整知识点。
- 不要切得过碎，也不要把多个无关知识点强塞进一条。

### `topic`

- 写最主要的知识主题。
- 示例：`马克思主义传播`、`抗日战争时期干部教育`、`新式整军运动`。

### `entities`

- 写能帮助检索和图谱扩展的实体。
- 不要随意堆词。
- 优先包括人物、组织、事件、地点、理论概念。

### `tags`

- 写辅助检索标签。
- 可以包括：时期、资料类型、教学主题、审查重点。

### `citation`

- `citation.doc` 必填：来源文献全文名。
- `citation.section` 必填：章节路径或最小可定位章节。
- `citation.page` 能确认时填写整数。
- `citation.page` 暂时无法确认时填写 `null`，并在交付说明中说明原因。
- 不允许为了字段完整而编造页码。

当前默认 `page` 为 PDF 页码；如果后续要用于论文、正式教材引用或教师审查，需要建立 PDF 页码与书本页码映射表。

## 5. 入库流程

```text
原始资料
  -> OCR / MinerU / 人工清洗
  -> 初步 chunk 切分
  -> 人工抽查 citation
  -> JSONL 校验
  -> 检索命中测试
  -> FAISS 冒烟实验（如进入向量检索评估）
  -> 负责人审核
  -> 合并 main
```

## 6. 验收命令

校验 JSONL：

```powershell
python src/utils/validate_jsonl.py data/processed/text_chunks_sizheng_v1.jsonl
```

回归测试：

```powershell
python -m pytest tests/test_retrieve.py -q
```

如涉及生成智能体和审查链路，也需要运行：

```powershell
python -m pytest tests/test_generator.py -q
```

如涉及向量检索评估，需要运行 FAISS 冒烟实验：

```powershell
D:\anaconda\envs\dachuang_2026\python.exe -X utf8 scripts\run_embedding_faiss_smoke_test.py --limit 10 --top-k 5
```

验收记录至少应包含：

- `summary.md` 路径。
- `results.jsonl` 路径。
- Chunk 数量。
- Embedding 模型和向量维度。
- Recall@1 / Recall@3 / Recall@5。
- MRR。
- 未命中或 Top-1 排序错误的问题说明。

注意：FAISS 重建会调用外部 Embedding API 并产生 token 消费。若 chunk 数据、Embedding 模型和向量维度均未变化，应优先使用 `--reuse-index-dir` 复用已有索引。

## 7. 每批交付必须说明

每批新增 chunks 至少附带说明：

- 本批资料来源。
- 本批条数。
- 清洗工具或方法。
- `citation.page` 是 PDF 页码还是书本页码。
- 哪些页码暂时无法确认。
- 是否通过 `validate_jsonl.py`。
- 推荐用于测试的 query。
- 是否会影响当前 Demo 稳定文件。

## 8. 当前扩库目标

第一轮目标：

- 基于《中国共产党思想政治教育史》和赵老师课件扩展到 100-200 条高质量 chunks。
- 当前已完成并合并 `text_chunks_sizheng_v1.jsonl` 与 `text_chunks_sizheng_v2.jsonl`，共 245 条思政史 chunks。
- 每批先交 30-50 条小批次，通过后再继续扩展。
- 每批必须附带 `team_deliverables/成员/时间-任务/README.md`，说明来源、页码口径、清洗方法和已知缺口。

第二轮目标：

- 在第一轮验收稳定后扩展到 500 条左右。
- 同步补充 GraphSim triples、展示问题和专家审查样例。

暂不建议一次性全量入库，避免低质量 chunk 污染检索、生成和审查结果。
