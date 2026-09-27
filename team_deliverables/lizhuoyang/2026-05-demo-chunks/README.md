# 李卓阳 2026-05 Demo Chunk 阶段交付说明

## 1. 本阶段任务

本阶段交付用于阶段汇报展示的教材 chunk 样例与检查说明，重点展示《中国共产党思想政治教育史》教材内容清洗、切片和结构化字段整理结果。

本阶段不修改后端业务代码，不调整正式数据读取路径，也不改变主项目运行逻辑。

## 2. 本目录包含

- `data/text_chunks_demo.jsonl`：汇报展示用 demo chunk 副本，共 40 条，字段包含 `id`、`source`、`title`、`text`、`entities`、`citation` 等。
- `docs/jxds_text_layer_check.md`：阶段性文本层检查记录，用于说明教材文本层和后续处理可行性。
- `scripts/`：预留辅助脚本目录。本次整理没有新增可执行辅助脚本。

## 3. 与主项目的关系

本目录中的文件主要用于阶段交付、汇报展示和材料归档，不直接参与后端运行。

系统可能读取的数据文件仍保留在正式数据目录：

- `data/processed/text_chunks_demo.jsonl`
- `data/processed/text_chunks.jsonl`
- `data/processed/events.jsonl`
- `data/processed/exam_qa.jsonl`
- `data/processed/letters.jsonl`

## 4. 影响范围

- 未修改 `src/` 下的后端业务代码。
- 未移动 `data/processed/` 下的正式数据文件。
- 未向 `docs/` 根目录散放汇报素材。
- 将阶段性检查说明从 `outputs/` 归档到本阶段交付目录。
