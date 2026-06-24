# Web 沙盘数据接口说明

## 1. 数据来源

当前 6 月说明基于仓库中已有的 Demo 数据：

- `data/processed/text_chunks_sizheng_v1.jsonl`（196 条）
- `data/processed/text_chunks_sizheng_v2.jsonl`（49 条）
- `data/processed/landmarks_demo.geojson`
- `data/processed/landmarks_demo.jsonl`
- `data/processed/timeline_demo_sizheng.json`
- `/retrieve` 返回的 `hybrid_hits`、`citations_used`、`source_check`、`policy_check`、`agent_trace`、`final_decision`

v1 与 v2 当前合计 245 条 chunks。这些数据用于 Web/XR 展示层规划，不代表正式史料库已完成。正式展示或论文使用前，需要继续复核来源、页码和坐标精度。

### 1.1 当前检索后端

- 默认 `/retrieve` 使用轻量检索。
- FAISS 是已完成工程冒烟验证的可选向量后端，不是默认链路。
- 负责人可通过 `DACHUANG_VECTOR_BACKEND=faiss` 和有效的 `DACHUANG_FAISS_INDEX_DIR` 启用。
- FAISS 未配置、索引目录不存在、API Key 缺失、Embedding 失败或向量维度不匹配时，后端自动回退轻量检索。
- 两种后端保持相同的 `/retrieve` 返回契约，因此展示层不应依赖某一种检索后端的内部实现。
- 当前 FAISS 结果属于工程验收，不作为正式论文实验结论。

## 2. 地标 GeoJSON 字段说明

`landmarks_demo.geojson` 是地图落点优先读取的数据。

顶层字段：

- `type`：固定为 `FeatureCollection`。
- `name`：数据集名称，当前为 `landmarks_demo`。
- `crs_note`：坐标口径说明。当前坐标统一使用 WGS84，且为 Demo 近似点位。
- `features`：地标点列表。

每个 `Feature` 字段：

- `type`：固定为 `Feature`。
- `geometry.type`：当前为 `Point`。
- `geometry.coordinates`：坐标数组，顺序为 `[lng, lat]`。
- `properties.id`：地标稳定 ID，用于前端选中、高亮和联动。
- `properties.name`：地标名称，例如“嘉兴南湖”“遵义”“延安”。
- `properties.category`：地标类别，当前为“红色地标”。
- `properties.coord_sys`：坐标系，当前为 `WGS84`。
- `properties.precision`：坐标精度说明，例如 `landmark_demo`、`city_demo`、`region_demo`。
- `properties.coordinate_note`：点位说明和复核要求。
- `properties.time_display`：适合展示在地图弹窗或时间线旁的时间文本。
- `properties.source_basis`：该地标被选为展示节点的依据。
- `properties.entities`：与该地标相关的实体列表，用于和 `/retrieve` 结果匹配。

前端读取建议：

```text
正式前端不应直接假设可访问仓库内的 data/processed 路径。
推荐方式一：由 FastAPI 提供数据读取接口。
推荐方式二：构建前端时把静态文件复制到 public/data/ 后读取。
读取后：
  -> 渲染地图点
  -> 使用 properties.id 作为 key
  -> 使用 properties.entities 匹配 KG-RAG 返回实体
```

## 3. 地标 JSONL 字段说明

`landmarks_demo.jsonl` 适合逐行读取或作为后续转换脚本的数据源。它比 GeoJSON 更适合保留 citation 和文字说明。

主要字段：

- `id`：与 GeoJSON 中的 `properties.id` 对齐。
- `name`：地标名称。
- `category`：地标类别。
- `location`：地理信息，包含 `lng`、`lat`、`coord_sys`、`precision`、`coordinate_note`。
- `time`：地标关联时间，包含 `start`、`end`、`display`。
- `summary`：展示层简短说明。
- `entities`：用于和 query entity、hybrid hit、timeline event 匹配。
- `tags`：主题标签。
- `citation`：来源说明。

`citation` 字段：

- `doc`：来源文件或来源类型。
- `section`：对应章节、主题或展示节点。
- `page`：页码。当前地标数据多为 `null`，因为地标素材来自公开资料、Demo 需求和待复核资料，尚不能定位到正式页码。
- `source_basis`：为什么该地标能支撑展示的说明。
- `verification_status`：当前验证状态，例如 `source_explained_page_pending` 或 `demo_verified`。

## 4. 时间线 JSON 字段说明

`timeline_demo_sizheng.json` 是 Web 时间线优先读取的数据。

顶层字段：

- `metadata.name`：数据集名称。
- `metadata.version`：数据版本。
- `metadata.owner`：当前维护人。
- `metadata.purpose`：用途说明。
- `metadata.scope`：数据边界。当前说明其只服务 Demo 和未来沙盘说明，不作为正式史料库入库数据。
- `metadata.source_note`：来源说明和页码复核要求。
- `metadata.coordinate_note`：坐标口径说明。
- `events`：时间线事件列表。

每个事件字段：

- `id`：事件稳定 ID，用于前端选中和联动。
- `title`：事件标题。
- `time.start`：开始时间，可为年份或日期。
- `time.end`：结束时间，没有结束时间时为 `null`。
- `time.display`：前端展示用时间文本。
- `location.name`：地点名称。
- `location.lng` / `location.lat`：WGS84 近似坐标。
- `location.coord_sys`：坐标系。
- `location.precision`：点位精度说明。
- `summary`：事件摘要。
- `entities`：相关实体。
- `related_landmarks`：可映射到地图点的地标名称。
- `tags`：主题标签。
- `visual_role`：展示角色，当前为 `timeline_node`。
- `citation`：来源说明。

时间线 citation 字段：

- `doc`：来源资料。
- `section`：相关章节。
- `page`：当前多为 `null`，原因是页码与原书章节仍需在正式清洗材料后复核。
- `verification_status`：例如 `needs_source_page` 或 `demo_verified`。

## 5. /retrieve 结果到展示层的映射

当前 `/retrieve` 的重点返回字段：

- `query_entities`：用户问题抽取出的实体。
- `vector_hits`：语义检索候选。
- `graph_hits`：图谱关系候选。
- `hybrid_hits`：融合后的证据候选。
- `citations_used`：生成回答实际使用的 citation。
- `source_check`：溯源审查结果。
- `policy_check`：政治红线规则初筛结果。
- `agent_trace`：三智能体流程轨迹，用于展示检索、生成、溯源审查、政治红线审查各阶段状态。
- `final_decision`：最终输出控制结果，前端必须优先读取它，而不是只看 `answer` 是否存在。

`agent_trace` 适合展示的字段：

- `agent`：阶段标识，例如 `retrieval_stage`、`generator`、`source_reviewer`、`policy_reviewer`。
- `role`：面向老师和前端展示的阶段名称。
- `status`：该阶段状态。
- `summary`：该阶段的简要统计或风险摘要。

`final_decision` 适合展示的字段：

- `status`：最终状态，当前包括 `approved`、`needs_review`、`blocked`。
- `can_output`：是否允许前端直接输出正式回答。
- `review_required`：是否需要人工复核。
- `reason`：最终决策原因。

`final_decision.status` 控制规则：

- `approved`：允许展示正式回答，并允许 TTS 或数字人播报。
- `needs_review`：不直接播报，只显示“待人工复核”和复核原因。
- `blocked`：禁止播报，展示阻断原因。

`hybrid_hits` 中适合展示的字段：

- `id`
- `source`
- `title`
- `text`
- `citation`
- `vector_score`
- `graph_score`
- `hybrid_score`
- `related_entities`
- `graph_paths`

最新 chunks 到展示节点的映射记录在 `spatiotemporal_mapping_notes.md`。映射节点至少包含：

- `display_id`：展示节点稳定 ID。
- `display_type`：地图时间线、纯时间线、人物卡片或事件卡片。
- `source_chunk_ids`：真实 `chunk_sizheng_v1_xxx` 或 `chunk_sizheng_v2_xxx`。
- `time`、`location`、`people`、`entities`：时空与人物信息。
- `citation`：逐条保留源 chunk 的 `doc`、`section`、`page`。
- `target_landmark_id`、`target_timeline_id`：映射到已有节点或 proposed 节点。
- `mapping_basis`：映射依据。
- `verification_status`：`verified`、`partial` 或 `needs_review`。

映射规则草案：

```text
hybrid_hit.related_entities
  -> 匹配 landmark.properties.entities
  -> 匹配 timeline_event.entities
  -> 高亮地图点和时间线事件

hybrid_hit.citation
  -> 渲染 citation 卡片
  -> 显示 doc、section、page、verification_status
  -> page 为 null 时显示“页码待复核”，不编造页码

hybrid_hit.graph_paths
  -> 渲染“为什么召回这条证据”的关系解释

source_chunk_ids
  -> 追溯到最新 245 条 chunks
  -> 提取人物、时间、地点和 citation
  -> 形成地图 / 时间线 / 人物卡片 / 事件卡片
```

映射限制：

- chunk 的结构化 `time` 或 `location` 为空时，只能使用正文中明确出现且可核对的信息。
- 无可靠地点的主题不得为了地图展示强行补坐标。
- 现有地标使用正式 `landmark_...` ID；尚未进入正式时间线的新节点使用 `proposed_timeline_...` ID。
- 多个 chunks 的 citation 不同时，应逐条保留，不能合并成虚构 citation。

## 6. 地图点、时间线和 citation 卡片联动

推荐交互：

1. 用户在搜索框输入问题。
2. 前端调用 `/retrieve`。
3. 后端按默认轻量检索或负责人启用的可选 FAISS 产生稳定响应。
4. 右侧展示 `hybrid_hits`、citation 卡片、`agent_trace` 和 `final_decision`。
5. 前端先读取 `final_decision.status`，决定回答和数字人播报是否可输出。
6. 前端用 `query_entities`、`related_entities`、`entities` 和映射表做节点匹配。
7. 匹配到的地图点高亮。
8. 匹配到的时间线事件高亮。
9. 用户点击地图点时，时间线跳转到相关事件，citation 区筛选相关证据。
10. 用户点击时间线事件时，地图定位到对应地点，citation 区展示相关证据。
11. 用户点击 citation 卡片时，地图点和时间线事件反向高亮。

## 7. 缺失信息和后续补齐

当前仍需补齐：

- 地标坐标需要正式点位复核。
- `citation.page` 需要明确 PDF 页码和书本页码口径。
- 部分地标、时间线事件目前只有来源依据说明，没有正式页码。
- 未来如正式进入 Web 前端，应通过 FastAPI 接口读取数据，或将静态文件复制到前端 `public/data/` 后读取，避免浏览器直接读取仓库内的 `data/processed/` 路径。
- 未来如进入 XR/数字人展示，应继续保证讲解内容基于 `citations_used`、`agent_trace` 和 `final_decision`，不要脱离证据自由生成。
