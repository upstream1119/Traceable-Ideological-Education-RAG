# 面向思政教育的可溯源多智能体跨模态交互系统

本项目是国家级大学生创新创业训练计划项目，面向思政教育场景，探索将 KG-RAG、多智能体协同、Citation 溯源、政治安全审查与跨模态交互展示结合起来，构建一个可解释、可审查、可扩展的智能教学辅助系统。

系统最终目标不是普通问答机器人，而是围绕思政历史事件、人物、地点、文本材料和思想脉络，提供证据化检索、生成审查、溯源展示与交互式学习支持。

项目按一年周期分阶段开发。当前仓库优先建设可溯源 KG-RAG 后端、稳定 API 契约和检索验证链路，为后续多智能体审查、跨模态展示和时空沙盘交互层提供基础。

## 1. 项目愿景

思政教育材料通常具有时间跨度长、人物事件多、叙事链条复杂、表达口径要求高等特点。普通大模型容易在没有明确证据的情况下生成看似合理但来源不明的回答，这不适合用于教学辅助场景。

本项目希望构建一个以“证据、审查、交互”为核心的智能系统：

- 用 KG-RAG 组织思政历史材料、人物、地点、事件和思想脉络。
- 用多智能体工作流拆分检索、生成、溯源审查和政治安全审查。
- 用 Citation 溯源让回答可追踪、可检查、可复核。
- 用时间线、地图、事件卡片、数字人或 XR 沙盘等方式提升交互式学习体验。

## 2. 为什么需要这个系统

思政教育不是普通开放域聊天任务。系统需要解决的问题包括：

- 材料分散：历史事件、人物关系、文献片段和地理信息需要结构化组织。
- 口径敏感：回答必须保持来源可追溯、表达可审查，不能随意扩展。
- 学习体验单一：传统文本阅读难以展示时间、空间和事件之间的关系。
- 大模型风险：生成内容可能出现无来源结论、事实混淆或表达不稳。

因此，本项目强调“先检索证据，再生成回答，再审查输出”，而不是让模型直接自由发挥。

## 3. 总体架构

目标系统架构如下：

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

核心模块说明：

- Intent Router：识别用户问题意图，判断需要文本检索、图谱推理还是跨模态展示。
- Hybrid Retriever：结合关键词、向量检索和结构化字段返回候选证据。
- Knowledge Graph Reasoner：围绕人物、事件、地点、时间线和思想脉络进行结构化关联。
- Generation Agent：基于证据片段生成教学辅助回答。
- Citation Auditor：检查回答是否有可追溯来源。
- Political Safety Auditor：检查输出表达是否符合思政教育场景的安全边界。
- Cross-modal Interaction Layer：承接时间线、地图、事件卡片、数字人或 XR 沙盘等交互展示。

## 4. 核心能力

规划中的系统能力包括：

- KG-RAG 思政历史知识检索。
- 多智能体生成与审查工作流。
- Citation-grounded answer generation。
- 政治安全与表达一致性审查。
- 基于时间、地点、人物和事件的结构化展示。
- 面向教学演示的跨模态交互层。
- 后续 XR 时空沙盘、数字人讲解和沉浸式课堂扩展。

## 5. 当前开发状态

当前仓库处于基础设施建设阶段，已经完成：

- FastAPI 最小接口。
- `/health` 和 `/retrieve`。
- `/retrieve` 返回结构固定。
- `configs/schema.yaml` 初版数据 Schema。
- `src/retriever/hybrid_retriever.py` 混合检索骨架。
- `data/processed/text_chunks_demo.jsonl` 读取支持。
- 思政史展示问题集初版和自动验收脚本。
- `team_deliverables/` 阶段性交付物管理目录。

正在推进或后续计划包括：

- 正式 FAISS 向量库。
- 正式 NetworkX 知识图谱。
- GraphSim 图谱相似度。
- 生成智能体、溯源审查智能体、政治红线审查智能体联调。
- 时间线 / 地图 / 事件卡片等交互式前端。
- XR 时空沙盘与数字人展示层。

## 6. 目录分工

```text
src/                   核心后端代码
configs/               Schema 与接口契约配置
data/                  系统运行会读取的数据
tests/                 自动化测试与正式验收集
team_deliverables/     非核心阶段交付物、汇报素材、草稿和说明文档
outputs/               本地运行产物
README_run.md          本地运行说明
README_architecture.md 检索中枢架构说明
docs/knowledge_base_ingestion_standard.md 思政知识库 chunk 入库标准
```

目录原则：

- 正式代码不放 `team_deliverables/`。
- 系统运行会读取的数据不放 `team_deliverables/`。
- 成员说明文档、汇报素材、草稿、交付记录和辅助绘图脚本可以放 `team_deliverables/`。
- 正式代码应在成员个人分支开发，经负责人审核和测试后合并到 `main` 的正式目录。

## 7. 快速启动

建议使用项目虚拟环境：

```powershell
conda activate dachuang_2026
uvicorn src.api.main:app --reload
```

启动后访问：

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

## 8. API 契约

`/retrieve` 当前返回：

- `status`
- `project`
- `query`
- `query_entities`
- `citations`
- `answer`
- `debug`

接口契约会随着图谱推理、生成智能体和审查智能体接入继续扩展，但会优先保证前端与后端协作时的结构稳定。

## 9. 路线图

| 阶段 | 目标 |
| --- | --- |
| Phase 1 | 建立 KG-RAG 后端、schema、检索接口和验收问题集 |
| Phase 2 | 接入正式向量库与知识图谱，增强实体、事件和时间线关联 |
| Phase 3 | 接入生成智能体、Citation 审查智能体和政治安全审查智能体 |
| Phase 4 | 构建时间线、地图、事件卡片等交互式展示层 |
| Phase 5 | 扩展 XR 时空沙盘、数字人讲解和课堂演示流程 |

## 10. 安全与使用边界

- 本系统用于思政教育辅助、教学展示和知识检索，不替代教师判断。
- 生成内容必须经过 Citation 溯源和安全审查后再用于正式展示。
- 对缺乏来源支撑的问题，系统应优先提示证据不足，而不是生成无来源结论。
- 政治安全审查模块属于系统核心环节，不能被前端展示效果替代。
