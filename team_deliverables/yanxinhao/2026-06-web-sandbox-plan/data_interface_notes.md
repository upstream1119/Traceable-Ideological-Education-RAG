# Web 沙盘数据接口说明

## 1. 数据来源

当前 6 月说明基于仓库中已有的 Demo 数据：

- `data/processed/landmarks_demo.geojson`
- `data/processed/landmarks_demo.jsonl`
- `data/processed/timeline_demo_sizheng.json`
- `/retrieve` 返回的 `hybrid_hits`、`citations_used`、`source_check`、`policy_check`

这些数据用于 Web/XR 展示层规划，不代表正式史料库已完成。正式展示或论文使用前，需要继续复核来源、页码和坐标精度。

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
fetch('/data/processed/landmarks_demo.geojson')
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
```

## 6. 地图点、时间线和 citation 卡片联动

推荐交互：

1. 用户在搜索框输入问题。
2. 前端调用 `/retrieve`。
3. 右侧展示 `hybrid_hits` 和 citation 卡片。
4. 前端用 `query_entities`、`related_entities`、`entities` 做轻量匹配。
5. 匹配到的地图点高亮。
6. 匹配到的时间线事件高亮。
7. 用户点击地图点时，时间线跳转到相关事件，citation 区筛选相关证据。
8. 用户点击时间线事件时，地图定位到对应地点，citation 区展示相关证据。
9. 用户点击 citation 卡片时，地图点和时间线事件反向高亮。

## 7. 缺失信息和后续补齐

当前仍需补齐：

- 地标坐标需要正式点位复核。
- `citation.page` 需要明确 PDF 页码和书本页码口径。
- 部分地标、时间线事件目前只有来源依据说明，没有正式页码。
- 未来如正式进入 Web 前端，应确认静态数据文件的服务路径，避免浏览器直接读取本地文件。
- 未来如进入 XR/数字人展示，应继续保证讲解内容基于 `citations_used`，不要脱离证据自由生成。
