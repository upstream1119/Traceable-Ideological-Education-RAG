# 力导向图数据接口（V1）

运行时文件为 `data/graph/force_graph.json`，由以下命令从正式三元组生成：

```powershell
python src/utils/build_force_graph.py
```

## 顶层结构

- `schema_version`: 当前为 `1.0`。
- `directed`: 固定为 `true`。
- `node_type_values`: 前端可用于图例和配色的节点类型枚举。
- `nodes`: 力导向图节点数组。
- `edges`: 力导向图有向边数组。
- `display_paths`: 已核验证据的演示路径。
- `stats`: 节点、边和正式 chunk 数量。

## 节点

```json
{
  "id": "张闻天",
  "label": "张闻天",
  "type": "person",
  "source_chunk_ids": ["chunk_sizheng_v1_148", "chunk_sizheng_v1_166"],
  "degree": 2
}
```

`type` 取值为 `person | organization | event | place | document | time | concept`。

## 边

```json
{
  "id": "edge_072",
  "source": "张闻天",
  "target": "《党的宣传鼓动工作提纲》",
  "relation": "起草",
  "source_chunk_ids": ["chunk_sizheng_v1_166"],
  "directed": true,
  "display_label": "起草"
}
```

前端应直接使用 `source`、`target` 构图，以 `relation` 或 `display_label` 显示边标签；点击节点或边时，用 `source_chunk_ids` 关联证据卡片。

## GraphSim 路径

`find_entity_paths(..., edge_lookup=build_edge_lookup(triples))` 保留原有的 `path`、`relations`、`path_text`，并新增：

- `source_chunk_ids`: 整条路径去重后的证据 chunk。
- `edges`: 每一步的 `source`、`target`、`relation`、`source_chunk_ids` 和 `original_direction`。

反向遍历只用于检索扩展，`original_direction=false`，关系标签固定为“关联”，防止把原始关系倒置表述。

## 演示路径

问题：`张闻天起草的《党的宣传鼓动工作提纲》为什么重要？`

路径：`张闻天 --起草--> 《党的宣传鼓动工作提纲》 --标志着--> 党的宣传教育工作系统化、规范化`

证据：`chunk_sizheng_v1_166`、`chunk_sizheng_v1_167`。`display_paths[0].evidence_chunks` 已内嵌标题、正文和 citation，可直接展示，无需人工抄图。
