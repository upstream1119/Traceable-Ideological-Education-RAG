# Traceable Ideological Education RAG

[English README](./README.md)

面向思政教育的可溯源 KG-RAG 系统，关注 Citation 溯源、多智能体审查、政治安全审查和跨模态学习交互。

本仓库是国家级大学生创新创业训练计划项目的一部分。当前重点是建设可溯源检索后端、稳定 API 契约和面向思政教育材料的证据化回答流程。

> 当前状态：backend-first prototype。当前实现重点包括检索 API、schema 稳定性、citation 结构、生成骨架、来源检查、规则检查和 demo 验证。完整跨模态交互、数字人展示和 XR 沙盘流程属于后续阶段。

## 核心能力

当前已实现能力：

- 提供 FastAPI 后端。
- 暴露 `/health` 和 `/retrieve` API。
- 返回稳定的检索响应结构。
- 读取处理后的思政教育文本 chunks。
- 使用 schema-driven API contract。
- 包含 graph storage、evidence generation、source checking 和 policy checking 模块。
- 维护 demo questions 和基础验收测试。
- 将项目交付物与核心代码分离管理。

规划能力：

- 更强的关键词、向量和结构化字段混合检索。
- 围绕人物、事件、地点、时间线和思政概念的知识图谱推理。
- 面向生成、Citation 审查和政治安全审查的多智能体工作流。
- 时间线、地图、事件卡片、数字人或 XR 学习交互。

## 为什么需要这个项目

思政教育材料通常具有时间跨度长、人物事件关系复杂、表达口径要求高等特点。普通开放域聊天机器人可能在没有明确证据的情况下生成看似合理但来源不明的回答，不适合作为教学辅助系统。

本项目遵循 retrieval-first 和 audit-first 工作流：

```text
retrieve evidence -> generate answer -> check citations -> review safety boundary -> display to learners
```

## 系统架构

目标架构：

```text
User Query
    |
    v
Intent Router
    |
    v
Hybrid Retriever
    |
    v
Knowledge Graph Reasoner
    |
    v
Generation Agent
    |
    v
Citation Auditor
    |
    v
Political Safety Auditor
    |
    v
Cross-modal Interaction Layer
```

当前仓库优先实现后端基础。部分下游模块目前是骨架或计划中的集成点，不代表已经完成生产级系统。

## 技术栈

- 后端：FastAPI, Python
- 检索：hybrid retriever scaffold, FAISS-ready dependency
- 图谱模块：NetworkX-ready graph store
- Schema 与配置：YAML, JSON
- 验证与测试：pytest, JSONL validation utilities

## 当前仓库范围

```text
src/                   核心后端代码
configs/               Schema 与接口契约配置
data/                  系统运行 demo 数据
tests/                 验收和模块测试
docs/                  知识库准入说明
team_deliverables/     报告、汇报材料、草稿和团队说明
outputs/               本地输出
README_run.md          本地运行说明
README_architecture.md 检索架构说明
```

正式代码不放 `team_deliverables/`。系统运行数据应放在 `data/`。汇报素材、草稿和团队交付物可以放在 `team_deliverables/`。

## 快速启动

安装依赖：

```powershell
pip install -r requirements.txt
```

启动 API：

```powershell
uvicorn src.api.main:app --reload
```

打开 API 文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
GET /health
```

检索接口：

```text
POST /retrieve
```

请求示例：

```json
{
  "query": "延安时期思想政治教育有什么特点？"
}
```

运行测试：

```powershell
python -m pytest tests -q
```

## API 契约

当前 `/retrieve` 返回：

- `status`
- `project`
- `query`
- `query_entities`
- `citations`
- `answer`
- `debug`

接口结构会随着图谱推理、生成智能体和审查智能体接入继续扩展。开始前端集成时，应优先考虑向后兼容。

## 路线图

| 阶段 | 目标 |
| --- | --- |
| Phase 1 | 建立 KG-RAG 后端、schema、检索接口和验收问题集 |
| Phase 2 | 接入更强的向量检索和知识图谱模块 |
| Phase 3 | 集成生成、Citation 审查和政治安全审查智能体 |
| Phase 4 | 构建时间线、地图和事件卡片交互层 |
| Phase 5 | 探索 XR 沙盘、数字人讲解和课堂演示流程 |

## 安全与使用边界

本系统用于思政教育辅助、教学展示和有来源支撑的知识检索，不替代教师、官方教学材料或最终人工审核。

生成内容应在 Citation 溯源和安全审查之后再用于正式展示。当证据缺失、不匹配或不足时，系统应提示证据不足，而不是生成无来源结论。
