# 《中国共产党思想政治教育史》扩充批次 100-200 条

## 1. 本批范围

- 原始 PDF：`data/raw/中国共产党思想政治教育史 .pdf`
- 正文提取：`data/raw/MinerU_中国共产党思想政治教育史 __20260517120100.json`
- 输出文件：`data/processed/text_chunks_sizheng_v1.jsonl`
- 当前总条数：196
- ID 范围：`chunk_sizheng_v1_001` 至 `chunk_sizheng_v1_196`
- PDF 物理页：21-150
- 覆盖章节：
  - 第一章 中国共产党成立与思想政治教育的历史开端：75 条
  - 第二章 土地革命时期思想政治教育的艰辛探索：57 条
  - 第三章 抗日战争时期思想政治教育的日趋成熟：64 条

本次是在已验收的前 20 条基础上继续扩充。前 20 条保留 `batch01` 标签；新增 176 条使用 `batch02` 标签。

## 2. 清洗与切片方法

正式生成逻辑位于 `src/etl/build_sizheng_chunks_v1.py`。

1. 固定读取 `MinerU_中国共产党思想政治教育史 __20260517120100.json`，不使用同目录其他 MinerU 版本。
2. 继续优先读取 `para_blocks`；只有缺失时才回退到 `preproc_blocks`。
3. 保留前 20 条人工精调 specs，避免已验收的 citation 和核心题元数据回退。
4. 从 PDF 34 页起按 MinerU 标题块自动维护章、节、小标题路径。
5. 对被 MinerU 误标为正文的短编号标题进行标题化处理。
6. 跳过 `思考题` 和 list 块，不进入知识库正文。
7. 短段在同一章节路径内合并，长段按句号、问号、叹号、分号等自然边界拆分。
8. 自动新增 chunk 少于 200 字的候选不保留，避免过碎。
9. `entities` 和 `tags` 只从正文和章节路径可确认的信息中提取，避免堆叠宽泛关键词。

长度统计：

- 最短：201 字
- 最长：801 字
- 平均：约 449.9 字
- 中位数：444 字
- 少于 300 字：44 条
- 多于 700 字：14 条

超出 300-700 字建议区间的条目主要是章节过渡、完整枚举段或跨页完整知识点，未为凑长度截断原文。

## 3. 页码口径

`citation.page` 继续使用 PDF 阅读器中的 1-based 物理页码：

```text
citation.page = MinerU page_idx + 1
```

跨页 chunk 填正文开头所在 PDF 页，不填结束页。本批没有 `page: null` 条目。

当前 PDF 已核验区间仍使用：

```text
书本印刷页码 = PDF 物理页码 - 14
```

该书本页码只用于人工查阅，不写入 JSONL 的 `citation.page`。

真实跨页 chunk 共 34 条：

| ID | 起始 PDF 页 | 结束 PDF 页 | 标题 |
|---|---:|---:|---|
| `chunk_sizheng_v1_007` | 24 | 25 | 留日学生接触社会主义及早期传播的历史局限 |
| `chunk_sizheng_v1_011` | 27 | 28 | 陈独秀传播马克思主义并推动建党 |
| `chunk_sizheng_v1_019` | 32 | 33 | 马克思主义者对社会主义改良论的批判 |
| `chunk_sizheng_v1_058` | 57 | 58 | 对农民思想政治教育重要性的认识 |
| `chunk_sizheng_v1_061` | 60 | 61 | 实事求是和群众路线原则 |
| `chunk_sizheng_v1_067` | 63 | 64 | 组织领导农民协会，普及革命思想（3） |
| `chunk_sizheng_v1_070` | 66 | 67 | 恽代英的军队政治工作思想 |
| `chunk_sizheng_v1_077` | 72 | 73 | 南昌起义与赣南整训 |
| `chunk_sizheng_v1_078` | 73 | 74 | 南昌起义与赣南整训（2） |
| `chunk_sizheng_v1_079` | 74 | 75 | 秋收起义和三湾改编 |
| `chunk_sizheng_v1_087` | 78 | 79 | 宣传工作要扩大群众基础 |
| `chunk_sizheng_v1_091` | 81 | 82 | 政治工作与军事工作相结合的原则 |
| `chunk_sizheng_v1_092` | 82 | 83 | 身教与言教相结合，身教重于言教的原则 |
| `chunk_sizheng_v1_099` | 86 | 87 | 政治工作是红军的生命线原则的提出 |
| `chunk_sizheng_v1_100` | 87 | 88 | 政治工作是红军的生命线原则的内涵和意义 |
| `chunk_sizheng_v1_108` | 92 | 93 | 颁布政治工作条例 |
| `chunk_sizheng_v1_111` | 94 | 95 | 传达贯彻遵义会议精神 |
| `chunk_sizheng_v1_127` | 102 | 103 | 团结教育杨虎城和西北军 |
| `chunk_sizheng_v1_128` | 103 | 104 | 促进西安事变和平解决 |
| `chunk_sizheng_v1_144` | 114 | 115 | 建设高素质的思想政治教育队伍 |
| `chunk_sizheng_v1_147` | 116 | 117 | 建设高素质的思想政治教育队伍（4） |
| `chunk_sizheng_v1_148` | 117 | 118 | 抗日战争时期党的干部教育 |
| `chunk_sizheng_v1_149` | 118 | 119 | 抗日战争时期党的干部教育（2） |
| `chunk_sizheng_v1_151` | 119 | 120 | 抗日战争时期党的干部教育（4） |
| `chunk_sizheng_v1_155` | 122 | 123 | 党内教育的伟大创举——整风运动 |
| `chunk_sizheng_v1_156` | 123 | 124 | 党内教育的伟大创举——整风运动（2） |
| `chunk_sizheng_v1_158` | 124 | 125 | 贯彻了唯物辩证法的认识方法和工作方法 |
| `chunk_sizheng_v1_169` | 132 | 133 | 关于思想政治教育的任务与基本原则 |
| `chunk_sizheng_v1_170` | 133 | 134 | 关于思想政治教育的作风与方法 |
| `chunk_sizheng_v1_172` | 134 | 135 | 党的七大的思想政治教育理论 |
| `chunk_sizheng_v1_175` | 137 | 138 | 马克思主义中国化与大众化的有效推进 |
| `chunk_sizheng_v1_179` | 139 | 140 | 知识分子的思想政治教育与《在延安文艺座谈会上的讲话》 |
| `chunk_sizheng_v1_193` | 148 | 149 | 国统区思想政治教育的广泛开展（2） |
| `chunk_sizheng_v1_194` | 149 | 150 | 国统区思想政治教育的广泛开展（3） |

## 4. 去重结果

- 总行数：196
- 唯一 ID：196
- 唯一正文：196
- 新文件内部完全重复：0
- 与 `text_chunks_demo.jsonl` 完全重复：0
- 相似度不低于 0.9 的候选：0
- 新文件内部最高相似度：约 0.316
- 与 demo 最高相似度：约 0.863，来自 `chunk_sizheng_v1_166` 与 `chunk_szzjys_demo_025`，主题均涉及张闻天宣传鼓动工作提纲，但正文不重复

## 5. 文件变更与项目影响

新增或更新：

- `src/etl/build_sizheng_chunks_v1.py`
- `data/processed/text_chunks_sizheng_v1.jsonl`
- `tests/test_sizheng_chunks_v1.py`
- `docs/superpowers/plans/2026-06-17-sizheng-v1-expand-100-200.md`
- `team_deliverables/lizhuoyang/2026-06-sizheng-v1-batch02/README.md`

未修改 `data/processed/text_chunks_demo.jsonl`。旧 demo 哈希保持：

```text
140E81525BB5A4BF45991BC9FE87AB8A22AC88A5DA0A35BFBA09D1CCD80A537F
```

除非主项目显式接入 `text_chunks_sizheng_v1.jsonl`，否则现有 demo 检索行为不受影响。

## 6. 验证

执行：

```powershell
python src/etl/build_sizheng_chunks_v1.py
python validate_jsonl.py data/processed/text_chunks_sizheng_v1.jsonl
python -m unittest tests.test_sizheng_chunks_v1
python -m unittest discover -s tests
```

结果：

- 生成器输出 196 条。
- JSONL 结构校验通过。
- 新文件质量测试通过，共 8 项。
- 全测试集通过，共 13 项。
