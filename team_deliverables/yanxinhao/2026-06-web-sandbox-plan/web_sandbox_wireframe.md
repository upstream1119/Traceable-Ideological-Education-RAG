# Web 时空沙盘页面草图

## 1. 页面目标

本页面草图用于说明暑假 Web 时空沙盘原型的第一版形态。目标不是完整实现 XR，而是让老师能看懂：

- 用户如何提出问题。
- KG-RAG 如何返回证据。
- 地图点、时间线和 citation 卡片如何联动。
- 未来 XR/数字人如何承接当前证据链。

## 2. 页面区域划分

建议第一版页面采用四区布局：

```text
+------------------------------------------------------------------+
| 顶部：用户问题输入区                                             |
| [请输入思政史问题...] [检索证据]                                  |
+-------------------------------+----------------------------------+
| 左侧：地图 / 时空沙盘主视图    | 右侧：KG-RAG 证据与 citation 区   |
|                               |                                  |
| - 红色地标点                  | - hybrid_hits 列表                |
| - 当前选中地点高亮            | - citation 卡片                   |
| - 地图弹窗显示 summary        | - vector_score / graph_score      |
|                               | - source_check / policy_check     |
|                               | - agent_trace / final_decision    |
+-------------------------------+----------------------------------+
| 底部：历史时间线                                                   |
| 1921 建党 -> 1935 遵义会议 -> 1942 延安整风 -> 抗战时期 -> 1949   |
+------------------------------------------------------------------+
| 预留：数字人讲解区域                                               |
| final_decision approved 后：文本回答 -> TTS -> 字幕/citation       |
+------------------------------------------------------------------+
```

第一版页面可以先用二维地图和普通时间线完成，不需要立即做复杂 3D 场景。

## 3. 核心交互

### 3.1 用户提问触发证据检索

```text
用户输入问题
  -> POST /retrieve
  -> 默认轻量检索 / 负责人可选 FAISS
  -> GraphSim 实体扩展与路径解释
  -> 返回 query_entities、hybrid_hits、citations_used、source_check、policy_check、agent_trace、final_decision
  -> 页面更新地图、时间线、citation 卡片和输出控制状态
```

前端不直接控制检索后端。默认轻量检索和可选 FAISS 均通过 `/retrieve` 提供相同返回结构；FAISS 未配置或发生异常时，由后端回退轻量检索。

### 3.2 地图点联动

地图点来自 `landmarks_demo.geojson`。

点击地图点后：

- 高亮当前地标。
- 显示地标名称、时间、summary、source_basis。
- 在时间线中高亮 `related_landmarks` 或 `entities` 匹配的事件。
- 在 citation 区筛选相关 `hybrid_hits`。

### 3.3 时间线联动

时间线来自 `timeline_demo_sizheng.json`。

点击时间线事件后：

- 高亮当前事件。
- 地图定位到 `location.lng`、`location.lat`。
- 展示事件摘要和 citation 状态。
- citation 区展示与事件 `entities`、`tags`、`related_landmarks` 匹配的证据。

### 3.4 citation 卡片联动

citation 卡片来自 `/retrieve` 的 `hybrid_hits` 和 `citations_used`。

点击 citation 卡片后：

- 显示证据标题、文本片段、来源、章节、页码或页码待复核状态。
- 根据 `related_entities`、`graph_paths` 或 citation 内容匹配地图点和时间线事件。
- 高亮对应地标和时间线节点。
- 如果 `source_check` 或 `policy_check` 提示风险，在卡片上显示“需复核”状态。
- 如果 `final_decision.status` 不是 `approved`，卡片只能作为复核材料，不触发正式回答或数字人播报。

## 4. citation 卡片信息结构

建议卡片字段：

```text
证据标题：hybrid_hit.title
来源文件：hybrid_hit.citation.doc
章节位置：hybrid_hit.citation.section
页码：hybrid_hit.citation.page
证据文本：hybrid_hit.text
融合分：hybrid_hit.hybrid_score
向量分：hybrid_hit.vector_score
图谱分：hybrid_hit.graph_score
相关实体：hybrid_hit.related_entities
图谱路径：hybrid_hit.graph_paths
审查状态：source_check / policy_check
流程轨迹：agent_trace
最终决策：final_decision.status / final_decision.reason
```

显示规则：

- `page` 为数字时，显示“PDF 页码：x”或后续确定的页码口径。
- `page` 为 `null` 时，显示“页码待复核”，并保留 `verification_status`。
- 不能把 `null` 页码改写成确定页码。
- 如果 `policy_check` 给出风险，不直接隐藏证据，而是标记“需要人工复核”。
- `final_decision.status = approved` 时，允许将回答作为正式展示内容。
- `final_decision.status = needs_review` 时，只显示待人工复核，不触发播报。
- `final_decision.status = blocked` 时，禁止播报，并显示 `final_decision.reason`。

## 5. 系统架构图文字版

6 月架构图建议分三层画：

```text
当前已完成链路
用户提问
  -> /retrieve
  -> 默认轻量检索 / 可选 FAISS
  -> GraphSim
  -> hybrid_hits
  -> 生成回答 + citation
  -> source_check
  -> policy_check
  -> agent_trace
  -> final_decision

6 月开发重点
245 条 chunks + hybrid_hits + citation + final_decision
  -> 地图点
  -> 时间线事件
  -> citation 卡片
  -> 回答输出控制
  -> 人物/事件解释卡片
  -> Web 沙盘页面草图

未来展示层
Web 沙盘
  -> 轻量 Three.js / 地图增强
  -> approved 后的 TTS + 字幕 + citation
  -> 轻量数字人讲解
  -> XR 时空沙盘
```

对老师说明时的重点：

- 当前不是普通聊天机器人，而是先找证据再生成回答。
- 默认链路是轻量检索；FAISS 是已验证的可选后端，尚未默认启用。
- 当前 FAISS 指标属于工程冒烟验收，不是正式论文实验结论。
- citation 和审查结果是可信展示的基础。
- `final_decision` 是回答展示和数字人播报的最终控制字段。
- XR/数字人只是展示方式，不能脱离证据链和 `final_decision`。
- 6 月不追求复杂 3D，而是先把数据联动和页面结构设计清楚。

## 6. 暑假个人电脑开发计划

### 第一阶段：数据读取原型

目标：

- 用 React + Vite + TypeScript 搭建前端。
- 用 Leaflet 读取 `landmarks_demo.geojson`。
- 用普通组件读取 `timeline_demo_sizheng.json`。
- 读取 `spatiotemporal_mapping_notes.md` 中冻结的节点设计，后续实现时转换为正式 JSON 或 API 响应。
- 实现地图点和时间线点击高亮。

验收：

- 页面能显示 6 个地标点。
- 页面能显示 5 条时间线事件。
- 点击地图点能定位对应时间线事件。

### 第二阶段：/retrieve 联调

目标：

- 增加问题输入框。
- 调用 FastAPI `/retrieve`。
- 展示 `hybrid_hits`、`citations_used`、`source_check`、`policy_check`、`agent_trace`、`final_decision`。

验收：

- 输入核心问题后，页面能展示 citation 卡片。
- `hybrid_score`、`vector_score`、`graph_score` 能显示。
- 证据不足或政治风险提示能被看见。
- `final_decision.status` 能控制回答是否直接输出。

### 第三阶段：证据到时空展示联动

目标：

- 根据 `query_entities`、`related_entities`、`entities` 匹配地标和事件。
- 点击 citation 卡片时反向高亮地图点和时间线事件。
- 增加“图谱路径解释”区域，显示 `graph_paths`。

验收：

- 至少 3 个核心问题能触发地图/时间线/citation 联动。
- 页面能解释为什么某条证据和某个地标或事件相关。

### 第四阶段：轻量数字人预留

目标：

- 不做高质量实时数字人。
- 先预留一个讲解区域，展示 `answer`、字幕、citation 和 `final_decision`。
- 后续可接 TTS 或轻量口型同步。

验收：

- `final_decision.status = approved` 时，讲解区域允许展示正式回答并触发 TTS/数字人播报。
- `final_decision.status = needs_review` 时，讲解区域只显示待人工复核，不触发播报。
- `final_decision.status = blocked` 时，讲解区域禁止播报，并显示阻断原因。
- 页面明确展示 citation，不让数字人脱离证据自由讲解。

## 7. 风险边界

- 不把当前 Demo 坐标当作正式测绘坐标。
- 不把 `page: null` 写成确定页码。
- 不把规则型 `policy_check` 宣称为已经替代专家审查。
- 不绕过 `final_decision` 直接播放回答。
- 不把 FAISS 表述为当前默认检索，也不把工程冒烟结果表述为论文实验。
- 不把 Web 页面草图宣称为完整 XR 沙盘。
- 不把数字人作为 6 月重算力主线。
- 不在前端或仓库中写入 API Key、模型权重或大文件。
