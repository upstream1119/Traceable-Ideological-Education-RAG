# GraphSim / 力导向图字段冻结说明

状态：P0 负责人批准前仅冻结数据契约与联调样例，不启动展示开发；TTS 后置。

## 1. 数据版本

- 当前合入基线：`main@b823040`；本说明随 `zhangbohan` 分支更新。
- 运行时检索事实集为 308 条正式 chunk：v1/v2 共 245 条，v3/v4/v5 新增 63 条。运行时由 `src/retriever/hybrid_retriever.py` 的 `FORMAL_CHUNKS_PATHS` 加载 v1—v5。
- 现有图谱 100 条三元组的证据引用范围仍是 v1/v2 的 245 条子集：
  - `data/processed/text_chunks_sizheng_v1.jsonl`，SHA-256 `b857cfcc1ab8f459642269a88e4a11a16731d59db0b4448a9d11cfee745775f4`
  - `data/processed/text_chunks_sizheng_v2.jsonl`，SHA-256 `0f920e5db28867030294f01f712864fba4f8a4237d5347248c47e3942291a93c`
- 图谱输入：`data/graph/triples_demo.jsonl`，100 条，SHA-256 `331d2d5755dd1f836b4bf47cb31f236f1053e412d89b6e9c7c79a4cd9cd69524`。文件名保留历史命名，但其中 100 条边均已通过正式 chunk 引用校验；它不是地图/时间轴 Demo 资产。
- 力导向图产物：`data/graph/force_graph.json`，147 节点、100 边；由 `python src/utils/build_force_graph.py` 重建。

## 2. 力导向图冻结字段

节点字段固定为：

| 字段 | 类型 | 约束 |
|---|---|---|
| `id` | string | 非空、全局唯一；当前与实体规范名相同 |
| `label` | string | 非空展示名 |
| `type` | enum | `person / organization / event / place / document / time / concept` |
| `source_chunk_ids` | string[] | 非空；每项必须定位到上述正式 chunk |
| `degree` | integer | 非负；按当前 100 条有向边的两端计数 |

边字段固定为：

| 字段 | 类型 | 约束 |
|---|---|---|
| `id` | string | 非空、全局唯一 |
| `source` / `target` | string | 必须引用现有节点 `id` |
| `relation` | string | 非空、来自正式三元组 |
| `source_chunk_ids` | string[] | 非空且均能定位正式 chunk |
| `directed` | boolean | 当前正式产物恒为 `true` |
| `display_label` | string | 当前等于 `relation` |

当前产物已验证节点 ID 唯一、边 ID 唯一、端点全部有效。类型数量：`concept 66 / organization 44 / document 14 / event 9 / person 7 / time 4 / place 3`。

## 3. GraphSim 路径与逐边证据

路径字段为 `from / to / hops / path / relations / path_text / source_chunk_ids / edges`。其中：

- `path` 为有序节点数组；`relations[i]` 描述 `path[i] -> path[i+1]`。
- `hops` 必须是非布尔正整数，且 `hops == path.length - 1 == relations.length == edges.length`。
- `from / to` 必须分别等于 `path` 的首节点和尾节点。
- `edges[i]` 固定包含 `source / target / relation / source_chunk_ids / original_direction`。
- `original_direction=true` 表示按正式三元组方向行走；反向检索扩展时为 `false`，此时关系展示为“关联”，不得反写原关系。
- 每条边的 `source_chunk_ids` 用作键，在两份正式 JSONL 中按顶层 `id` 精确查找；命中对象的 `text` 是正文，`citation.doc / section / page` 是引用信息。
- 路径总 `source_chunk_ids` 必须严格等于逐边 `source_chunk_ids` 按路径顺序合并后的去重列表。

当前正式检索入口 `retrieve_graph()` 内部固定调用 `_load_demo_edge_lookup()` 并传给 `find_entity_paths()`，因此它返回的有效 `graph_paths` 保证带 `edges[].source_chunk_ids`。但底层通用函数 `find_entity_paths(..., edge_lookup=None)` 仍允许省略该参数；故接口保证限定为正式 `retrieve_graph()`/融合检索响应，不扩展到任意直接调用底层函数。测试会对正式入口重新运行并校验逐边证据。

## 4. 异常数据口径

以下定义为契约拒绝项，是待约定并已加入验证测试的边界，不代表当前产物已发生这些故障：

- 重复节点 ID 或重复边 ID；
- 节点 `label` 不是非空字符串；
- 边端点未出现在节点集合；
- `source_chunk_ids` 为空、非数组、包含空串或非字符串；
- 证据 ID 无法在 245 条正式 chunk 中精确定位；
- `hops` 与节点、关系或逐边数组长度不一致；
- `hops` 是布尔值、非整数或非正数；`from/to` 与路径首尾不一致；
- 路径总 `source_chunk_ids` 与逐边证据的顺序去重结果不一致；
- 力导向边的 `directed` 或路径边的 `original_direction` 不是布尔值；
- 路径逐边端点/关系与路径节点/关系序列不一致。

验证实现：`src/graph/schema_validation.py`；测试：`tests/test_graph_contract.py`。

## 5. 可复现联调样例

本轮样例不使用既有“张闻天→提纲→系统化、规范化”记录。新样例保存在 `reports/graphsim_integration_samples.json`：

- 1 跳：毛泽东 →（命名）→ 新式整军运动，证据 `chunk_sizheng_v2_022`；
- 2 跳：中国人民解放军 →（开展）→ 新式整军运动 →（提高）→ 干部战士的政治觉悟，证据依次为 `chunk_sizheng_v2_034`、`chunk_sizheng_v2_023`；
- 空路径：未知实体与不存在事件，`query_entities=[]`、Top-3 和路径均为空。

样例沿用正式响应层级 `graph_hits[].graph_paths[].edges[].source_chunk_ids`，并额外附上解析后的 `evidence_chunks[].text/citation`，供严欣浩直接联调。

复跑命令：`python scripts/export_graphsim_integration_samples.py`。

## 6. 地图 / 时间轴验收状态

当前仓库只有 `data/processed/landmarks_demo.jsonl` 和 `data/processed/timeline_demo_sizheng.json`。两者元数据明确写明 Demo、近似坐标、正式前需复核，部分 citation 仍为待正式来源归档/待页码复核。因此当前状态为：**未形成正式地图/时间轴资产，引用未完成正式验收，坐标未完成逐点验收**。不得以文件存在或路由能返回 ID 代替验收。

后续正式验收至少需要：逐条权威来源、可定位 citation、坐标系与经纬度、点位精度说明、复核人/日期、资产版本与验收记录。
