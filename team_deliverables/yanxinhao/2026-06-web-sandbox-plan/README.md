# 严欣浩 2026-06 Web 时空沙盘规划交付

## 1. 本阶段定位

本目录用于 6 月第一版 Web 时空沙盘规划说明，重点是把当前 KG-RAG 证据链如何承接到地图、时间线、citation 卡片和未来 XR/数字人展示层讲清楚。

本阶段不开发完整 Three.js/XR 沙盘，不实现正式数字人，也不修改 `src/`、`tests/`、`data/processed/` 等正式运行目录。

6 月任务边界：

- 维护地标、时间轴和空间数据口径。
- 说明后续 Web 前端如何读取 `landmarks_demo.geojson` 和 `timeline_demo_sizheng.json`。
- 设计 KG-RAG 证据结果到地图点、时间线事件、人物/事件卡片和 citation 卡片的映射方式。
- 更新面向老师的系统架构说明，区分当前已完成、6 月开发重点和未来 XR/数字人展示层。
- 形成暑假个人电脑 Web 原型开发计划。

## 2. 当前已完成基础

当前仓库已具备以下展示层前置基础：

- `data/processed/landmarks_demo.geojson`：6 个红色地标 GeoJSON 点位。
- `data/processed/landmarks_demo.jsonl`：与地标对应的逐行 JSON 数据，包含 `citation.source_basis`。
- `data/processed/timeline_demo_sizheng.json`：5 条思想政治教育史时间线事件。
- `/retrieve`：当前核心检索接口，可返回 `vector_hits`、`graph_hits`、`hybrid_hits`、`answer`、`citations_used`、`source_check`、`policy_check`、`agent_trace` 和 `final_decision`。
- `hybrid_hits`：保留 `citation`、`vector_score`、`graph_score`、`hybrid_score`，可作为 citation 卡片的数据来源。

这些内容只能说明“可溯源证据检索底座”和“展示层承接方案”，不能表述为完整 XR 系统或完整零幻觉系统已经完成。

## 3. 6 月交付文件

- `data_interface_notes.md`
  - 说明地标、时间线和 citation 卡片字段。
  - 说明 Web 沙盘如何读取现有数据。
  - 说明证据到地图点、时间线事件和人物/事件卡片的映射草案。

- `web_sandbox_wireframe.md`
  - 给出 Web 沙盘页面区域草图。
  - 说明地图点、时间线、citation 卡片之间的交互联动。
  - 说明当前系统架构图应如何区分已完成、6 月重点和未来展示层。

- `figures/`
  - 预留 6 月新增图和草图的统一存放目录。
  - 后续如生成新图，应放在本目录，不散放到 `docs/` 或 `scripts/` 根目录。

## 4. KG-RAG 到展示层的承接关系

展示层不替代 KG-RAG 主链路，而是读取 KG-RAG 的可溯源结果并进行可视化表达。

推荐链路：

```text
用户提问
  -> /retrieve
  -> query_entities
  -> vector_hits + graph_hits
  -> hybrid_hits + citation
  -> source_check + policy_check
  -> agent_trace + final_decision
  -> Web 地图点 / 时间线事件 / citation 卡片 / 回答与数字人播报控制
```

前端展示时应遵守两个原则：

- citation 卡片展示的是证据来源、章节、页码或页码缺失原因，不补造来源。
- 数字人讲解只能基于 `answer`、`citations_used`、`agent_trace` 和 `final_decision` 组织表达，不能脱离 KG-RAG 证据自由生成。
- 前端必须以 `final_decision.status` 控制输出：`approved` 才允许直接展示回答并播报；`needs_review` 只显示待人工复核；`blocked` 禁止数字人播报并显示阻断原因。

## 5. 暑假 Web 原型计划

暑假建议先做轻量 Web 原型，不直接重投入复杂 Three.js/XR。

推荐技术路线：

- 前端框架：React + Vite + TypeScript。
- 地图展示：先用 Leaflet 读取 GeoJSON。
- 时间线展示：先用普通 React 组件渲染 JSON 事件。
- 检索联动：通过 FastAPI `/retrieve` 获取 `hybrid_hits`、`citations_used`、`agent_trace` 和 `final_decision`。
- 状态联动：用前端状态保存当前选中的地标、事件和 citation。

建议先做 3 个页面或视图：

1. Web 沙盘首页：地图点 + 时间线 + 地标详情。
2. KG-RAG 检索页：问题输入 + hybrid hits + citation 卡片。
3. 证据联动页：点击 citation 后高亮相关地图点和时间线事件。

## 6. 算力与开发边界

- 个人电脑适合：Web 原型、数据读取、页面草图、轻量交互联动、接口调试。
- 实验室 4090D 适合：三智能体闭环集成、小模型推理、Embedding 批处理、TTS/数字人 demo 测试。
- 云 GPU 适合：暑假实验室断电时的短期训练、远程复现和跨组协作补充。
- 当前不适合：大模型从零训练、70B 级全量微调、复杂 3D 场景云端实时渲染、高并发实时数字人。

## 7. 后续提交说明

本目录是阶段性交付物，不影响系统运行。后续如果真正进入正式 Web 原型，应另行确认是否新增正式前端目录，并通过 PR 说明是否影响 `src/`、`tests/`、`data/processed/` 或接口契约。
