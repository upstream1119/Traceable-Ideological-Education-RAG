# 《中国共产党思想政治教育史》文本清洗第一批

> 本 README 记录第一批 20 条 sample 的验收状态。当前 `data/processed/text_chunks_sizheng_v1.jsonl` 已在第二批扩展到 196 条，扩展说明见 `team_deliverables/lizhuoyang/2026-06-sizheng-v1-batch02/README.md`。

## 1. 本批范围

- 原始 PDF：`data/raw/中国共产党思想政治教育史 .pdf`
- 正文提取：`data/raw/MinerU_中国共产党思想政治教育史 __20260517120100.json`
- 章节：第一章“中国共产党成立与思想政治教育的历史开端”第一节“马克思主义的最初传入与广泛传播”
- PDF 物理页：21-33
- 输出：`data/processed/text_chunks_sizheng_v1.jsonl`
- 实际条数：20
- ID：`chunk_sizheng_v1_001` 至 `chunk_sizheng_v1_020`

这是第一批连续章节 sample，尚未扩展到全书。等待人工验收后再继续下一批。

## 2. 清洗与切片方法

生成逻辑位于 `src/etl/build_sizheng_chunks_v1.py`。

1. 固定读取上述 MinerU JSON，避免同目录其他 MinerU 版本影响重跑结果。
2. 每页优先读取 `para_blocks`；仅在缺失时回退到 `preproc_blocks`，不同时拼接两套 block。
3. 删除脚注序号、异常空格和换行，修正能够由上下文确认的 OCR 字符错误，不改写正文。
4. 按章、节、小标题、人物和论点边界切片，不使用滑动窗口。
5. 跨页句段合并，正文按原始阅读顺序连接。
6. `entities` 只保留当前知识点直接相关的人物、文献、事件和关键理论；`tags` 使用 3 个公共标签和 3 个区分性标签。

正文长度为 279-710 字。以下三条因语义完整性保留在建议区间外：

- `chunk_sizheng_v1_011`：710 字。陈独秀段落在 PDF 28 页仅续接一句，合并后才能保持句段完整。
- `chunk_sizheng_v1_014`：279 字。该段完整表达“传播运动形成并转入社会思潮论战”的章节过渡。
- `chunk_sizheng_v1_018`：286 字。该段完整表达社会主义问题论战中改良主义一方的主张。

## 3. 页码口径

`citation.page` 只表示 PDF 阅读器中的 1-based 物理页码，换算规则为：

```text
citation.page = MinerU page_idx + 1
```

跨页 chunk 填正文开头所在的 PDF 页，不填结束页。本文件当前已核验的书本印刷页码偏移为“PDF 物理页码 - 14”，因此本批 PDF 21-33 页对应书本印刷 7-19 页；书本页码只用于人工查阅，不写入 `citation.page`。

本批所有页码均能由正文开头在对应 MinerU 页命中确认，没有 `page: null` 条目。

跨页 chunk：

| ID | 起始 PDF 页 | 跨至 PDF 页 | 说明 |
|---|---:|---:|---|
| `chunk_sizheng_v1_007` | 24 | 25 | 留日学生接触社会主义及早期传播局限 |
| `chunk_sizheng_v1_011` | 27 | 28 | 陈独秀传播马克思主义并推动建党 |
| `chunk_sizheng_v1_019` | 32 | 33 | 社会主义问题论战的批判与结论 |

## 4. 去重结果

- 总行数：20
- 唯一 ID：20
- 唯一正文：20
- 新批内部完全重复：0
- 与 `text_chunks_demo.jsonl` 完全重复：0
- 相似度不低于 0.9 的候选：0
- 新批内部最高相似度：约 0.134
- 与 demo 最高相似度：约 0.810，为“问题”与“主义”之争的相邻知识点，不是重复正文

## 5. 文件变更与项目影响

新增或更新：

- `src/etl/build_sizheng_chunks_v1.py`
- `data/processed/text_chunks_sizheng_v1.jsonl`
- `tests/test_sizheng_chunks_v1.py`
- `tests/test_demo_retrieval_quality.py`：修正将具体文献实体 `《宣传工作决议案》` 误判为宽泛“宣传工作”元数据的问题，并增加张闻天题 Top1 为 `chunk_szzjys_demo_025` 的断言
- `team_deliverables/lizhuoyang/2026-06-sizheng-v1-batch01/README.md`

未修改 `data/processed/text_chunks_demo.jsonl`。新 JSONL 当前是独立数据文件；除非主项目后续显式接入该文件，否则不会改变现有 demo 检索行为。

## 6. 验证

执行：

```powershell
python validate_jsonl.py data/processed/text_chunks_sizheng_v1.jsonl
python -m unittest tests.test_sizheng_chunks_v1
python -m unittest tests.test_validate_jsonl
python -m unittest tests.test_demo_retrieval_quality
```

验证结果：

- JSONL 结构校验通过，共 20 条。
- 新批质量测试通过，共 8 项。
- 基础 JSONL 测试通过。
- demo 核心检索质量测试通过。
