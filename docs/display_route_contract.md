# Display Route V1 接口契约

## 1. 目标与边界

`display_route` 用于把 `/retrieve` 的检索、生成和审查结果路由到证据卡片、时空地图或数字人入口。V1 使用确定性规则，不代表意图分类模型已经训练完成。

前端只消费后端路由结果，不自行判断意图、推断学段或根据实体猜测时空资产。`final_decision` 的输出控制优先级始终高于 `display_route`。

## 2. 请求字段

```json
{
  "query": "请面向高中生介绍党的一大",
  "target_grade": "senior_high"
}
```

`target_grade` 为可选字段，允许值为：

- `primary`
- `junior_high`
- `senior_high`
- `university`

未传入时，后端只在 Query 明确出现学段信息时进行识别，否则返回 `null`。

## 3. 响应结构

```json
"display_route": {
  "intent_type": "knowledge_qa",
  "target_grade": null,
  "presentation_mode": "evidence_cards",
  "timeline_ids": [],
  "landmark_ids": [],
  "narrative_character": null
}
```

字段定义：

| 字段 | 类型 | V1 取值或约束 |
| --- | --- | --- |
| `intent_type` | string | `knowledge_qa`、`spatiotemporal`、`character_narrative`、`unknown` |
| `target_grade` | string / null | 四个正式学段枚举或 `null` |
| `presentation_mode` | string | `evidence_cards`、`timeline_map`、`digital_human` |
| `timeline_ids` | array[string] | 只返回正式时间线数据中存在的 ID |
| `landmark_ids` | array[string] | 只返回正式 GeoJSON 中存在的 ID |
| `narrative_character` | string / null | V1 只返回一个叙事主题人物 |

## 4. 路由规则

V1 内容意图只区分知识问答、时空展示和人物叙事。高风险人工复核不是内容意图，由 `policy_check` 和 `final_decision` 控制。

人物叙事提示优先于时空提示；无法识别叙事人物时保留 `character_narrative`，但安全回退到 `evidence_cards`。空 Query 返回 `unknown + evidence_cards`。

`timeline_ids` 和 `landmark_ids` 只在 `timeline_map` 模式下返回。没有可靠映射时返回空数组，不强行补充节点。`proposed_timeline_*` 不属于 V1 正式接口资产。

## 5. 输出控制

| `final_decision.status` | 展示规则 |
| --- | --- |
| `approved` | 允许显示正式回答；根据 `presentation_mode` 渲染对应展示，满足人物条件时可开放 TTS/数字人入口 |
| `needs_review` | 只显示证据、citation、风险和复核原因，禁止正式播报 |
| `blocked` | 禁止正式回答和播报，只显示阻断或复核信息 |

## 6. 标准联调样例

普通知识问答：

```json
{
  "intent_type": "knowledge_qa",
  "target_grade": null,
  "presentation_mode": "evidence_cards",
  "timeline_ids": [],
  "landmark_ids": [],
  "narrative_character": null
}
```

党的一大时空展示：

```json
{
  "intent_type": "spatiotemporal",
  "target_grade": null,
  "presentation_mode": "timeline_map",
  "timeline_ids": ["timeline_sizheng_1921_foundation_001"],
  "landmark_ids": ["landmark_1921_jiaxing_nanhu_001"],
  "narrative_character": null
}
```

张闻天人物叙事：

```json
{
  "intent_type": "character_narrative",
  "target_grade": "senior_high",
  "presentation_mode": "digital_human",
  "timeline_ids": [],
  "landmark_ids": [],
  "narrative_character": "张闻天"
}
```

## 7. 兼容性约定

V1 只在 `/retrieve` 顶层新增 `display_route`。原有 `hybrid_hits`、`citations_used`、`source_check`、`policy_check`、`agent_trace` 和 `final_decision` 均保持不变。
