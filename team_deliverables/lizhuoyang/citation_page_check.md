# Citation Page Check

## 结论

`data/processed/text_chunks_demo.jsonl` 中的 `citation.page` 已明确为 PDF 物理页码，1-based，不是书本印刷页码。

本次复核后，40 条 chunk 均可回查到《中国共产党思想政治教育史》PDF/MinerU OCR 页。正文区间内书本印刷页码与 PDF 页码的稳定关系为：

`书本页码 = PDF 页码 - 14`

其中 38 条可直接看到页脚书本页码；2 条为章节或正文首页未印页码，已在 `page_mapping_draft.csv` 中标为“推定”，并写明推定原因。

## 检查依据

- 正式 demo 数据：`data/processed/text_chunks_demo.jsonl`
- 原始 PDF：`data/raw/中国共产党思想政治教育史 .pdf`
- OCR/版面抽取：`data/raw/MinerU_中国共产党思想政治教育史 __20260517120100.json`
- 复核方法：
  - 解析 40 条 JSONL。
  - 用 MinerU `page_idx` 对齐 PDF 页，`PDF 页码 = page_idx + 1`。
  - 用 chunk 正文开头和所在页 OCR 文本做命中检查。
  - 用 MinerU `discarded_blocks` 中的 `page_number` 抽取书本印刷页码。

## 页码修正

以下 3 条原页码指向跨页 chunk 的后半页，本次统一改为 chunk 正文起始所在 PDF 页：

| chunk_id | 原 PDF 页码 | 修正后 PDF 页码 | 修正后书本页码 | 说明 |
|---|---:|---:|---:|---|
| `chunk_szzjys_demo_004` | 30 | 29 | 15 | 正文开头“列宁指出……”在 PDF 29 页，后文延续至 PDF 30 页。 |
| `chunk_szzjys_demo_012` | 75 | 74 | 60 | 正文开头“第二，支部建连……”在 PDF 74 页，后文延续至 PDF 75 页。 |
| `chunk_szzjys_demo_034` | 174 | 173 | 159 | 正文开头“从 1946 年 7 月……”在 PDF 173 页，后文延续至 PDF 174 页。 |

## 字段复核

- `source` 与 `citation.doc`：40 条均为《中国共产党思想政治教育史》，与原始 PDF 一致。
- `title`：40 条均保留当前 chunk 的内容标题或节内小标题；有些标题不一定出现在 `citation.page` 当页，因为正文 chunk 可能截取自标题之后的段落。
- `citation.section`：40 条均表示章节路径，用于内容层级定位；它不是页内页眉，也不要求与页眉完全一致。
- `citation.page`：修正后表示 chunk 正文起始所在 PDF 页。

## 核心演示题优先抽查

| 主题 | chunk_id | PDF 页码 | 书本页码 | 状态 | 备注 |
|---|---|---:|---:|---|---|
| 马克思主义传入 | `chunk_szzjys_demo_003` | 25 | 11 | 已确认 | 正文命中“马克思学说在中国的最初传入”。 |
| 马克思主义传播论战 | `chunk_szzjys_demo_004` | 29 | 15 | 已确认 | 已改为跨页正文起始页。 |
| 共产主义小组宣传马克思主义 | `chunk_szzjys_demo_005` | 34 | 20 | 已确认 | 命中上海共产主义小组、陈独秀、李大钊等内容。 |
| 党的一大 | `chunk_szzjys_demo_006` | 39 | 25 | 已确认 | 命中《中国共产党第一个纲领》和思想政治教育基本原则。 |
| 长征政治动员 | `chunk_szzjys_demo_015` | 88 | 74 | 已确认 | 命中反“围剿”和长征中的思想政治教育概述。 |
| 长征政治攻势 | `chunk_szzjys_demo_016` | 92 | 78 | 已确认 | 命中政治攻势、俘虏教育、瓦解敌军。 |
| 长征部队动员 | `chunk_szzjys_demo_017` | 96 | 82 | 已确认 | 命中连队支部、党员模范作用和阶级友爱教育。 |
| 干部教育/张闻天 | `chunk_szzjys_demo_022` | 117 | 103 | 已确认 | 命中干部教育部、张闻天、李维汉、延安干部学校。 |
| 抗日军政大学 | `chunk_szzjys_demo_023` | 121 | 107 | 已确认 | 命中抗大组织纪律教育。 |
| 张闻天宣传鼓动提纲 | `chunk_szzjys_demo_025` | 130 | 116 | 已确认 | 命中张闻天起草《党的宣传鼓动工作提纲》。 |

## 结构化字段修正

40 条 chunk 已逐条补强：

- `topic` 从统一的“思想政治教育史”改为更细的阶段主题，如“马克思主义传播与建党初期思想政治教育”“抗日战争时期思想政治教育”等。
- `entities` 增加人物、组织、会议、文献、事件和关键概念。
- `tags` 保留 demo 标识，同时增加可检索主题词，如“党的一大”“干部教育”“张闻天”“长征”“新式整军运动”等。

## 未确定项

没有发现需要将 `citation.page` 置为 `null` 的 chunk。

需要注意的是：`page_mapping_draft.csv` 中 `chunk_szzjys_demo_001` 和 `chunk_szzjys_demo_029` 的书本页码为连续页码推定，因为对应 PDF 页未印正文页脚；PDF 页码本身已确认。
