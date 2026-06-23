# 思政文本清洗 v2 缺口补充说明

## 本批目标

本批用于补当前检索缺口，不继续追求数量扩张。输出文件为：

```text
data/processed/text_chunks_sizheng_v2.jsonl
```

实际生成 49 条，高质量 chunk ID 范围：

```text
chunk_sizheng_v2_001 - chunk_sizheng_v2_049
```

本批不覆盖 `text_chunks_demo.jsonl`，也不覆盖已合并的 `text_chunks_sizheng_v1.jsonl`。

## 输入来源

- PDF 原文：`data/raw/中国共产党思想政治教育史 .pdf`
- MinerU JSON：`data/raw/MinerU_中国共产党思想政治教育史 __20260517120100.json`
- 清洗规则：`team_deliverables/lizhuoyang/2026-06-text-cleaning-jsonl-rules/README.md`

说明：仓库中另有 `20260615145108` 和 `20260615145133` 两个 MinerU JSON，但本批页码与正文核验使用 `20260517120100`。该文件中目标内容的 `page_idx + 1` 与本批 `citation.page` 一致。

## 章节和页码范围

本批覆盖：

- 绪论 / 三、学习研究中国共产党思想政治教育史的目的、意义和方法：PDF 18-19 页。
- 第二章 / 中央《宣传工作决议案》的主要内容 / （三）宣传工作的组织领导：PDF 79 页。
- 第四章 解放战争时期思想政治教育的成功实践：PDF 152-187 页。

第四章重点补充主题包括：

- 新式整军运动。
- 诉苦三查。
- 人民解放军思想政治教育。
- 瓦解敌军工作。
- 教育改造国民党被俘部队。
- 教育改造国民党起义、投诚部队。
- 解放战争时期党的思想政治教育。
- 人民军队政治工作。

## 清洗和切片方式

- 优先使用 MinerU `para_blocks` 提取正文，PDF 用于页码和人工回查。
- 删除目录、页眉页脚、独立页码、脚注序号和版面噪声。
- 对跨页句子和跨页段落做连续拼接，保持原文事实、观点和论证关系。
- 按章节层级和完整知识点切片，不使用滑动窗口。
- 每条 chunk 保持一个中心主题，避免把多个无关问题塞进同一条。
- `entities` 只保留正文可确认且与知识点直接相关的实体；本次已去掉公共 `gap-fill` 标签，并收紧第二章宣传组织条目的泛化宣传词，避免影响张闻天核心题检索。

## 页码口径

`citation.page` 一律填写 PDF 1-based 物理页码，即 MinerU `page_idx + 1`。

跨页 chunk 的 `citation.page` 填正文开头所在 PDF 页，不填结束页。本批所有条目 page 均已确认，没有使用 `null` 页码。

## 核心问题覆盖

目标问题一：

```text
新式整军运动与人民解放军有什么关系？
```

重点证据：

- `chunk_sizheng_v2_021` 新式整军运动的定义和历史地位。
- `chunk_sizheng_v2_022` 诉苦三查推动全军新式整军。
- `chunk_sizheng_v2_023` 新式整军运动的思想政治教育经验。

目标问题二：

```text
人民解放军如何教育改造国民党被俘和起义部队？
```

重点证据：

- `chunk_sizheng_v2_030` 教育改造国民党被俘和起义部队的难题。
- `chunk_sizheng_v2_031` 教育改造国民党部队的思想教育制度。
- `chunk_sizheng_v2_032` 教育改造国民党部队的分类方法。
- `chunk_sizheng_v2_033` 教育改造国民党部队的组织领导。

## 页码不确定情况

无。49 条均有确认的 PDF 物理页码。

## 修改文件

- `data/processed/text_chunks_sizheng_v2.jsonl`
- `team_deliverables/lizhuoyang/2026-06-sizheng-v2-gap-fill/README.md`

未修改 `src/` 核心代码，未修改 demo 数据，未修改 v1 数据。

## 验证命令

```powershell
& "C:\Users\安心\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" validate_jsonl.py data/processed/text_chunks_sizheng_v2.jsonl
& "C:\Users\安心\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_sizheng_chunks_v2
& "C:\Users\安心\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_demo_retrieval_quality
```

交付前需确认三项均通过。

## 验证结果

已通过：

- `validate_jsonl.py data/processed/text_chunks_sizheng_v2.jsonl`：OK，49 rows。
- `python -m unittest tests.test_sizheng_chunks_v2`：OK，7 tests。
- `python -m unittest tests.test_demo_retrieval_quality`：OK，3 tests。
