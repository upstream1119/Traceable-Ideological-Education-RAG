# GraphSim 6 月质量说明

本次工作重点不是扩写说明文档，而是把 GraphSim demo 做成可验证的工程闭环：三元组必须能追溯到真实 chunk，核心 query 必须能看到 graph path，`graph_score` 需要体现路径长度、关系类型和无效路径过滤。

## 已复核的数据范围

- 三元组文件：`data/graph/triples_demo.jsonl`
- 文本依据文件：`data/processed/text_chunks_demo.jsonl`
- 校验规则：
  - `head`、`relation`、`tail`、`source_chunk_ids` 四个字段必须存在；
  - `head`、`relation`、`tail` 必须是非空字符串；
  - `source_chunk_ids` 必须是非空字符串列表；
  - 每个 `source_chunk_ids` 必须能在 `text_chunks_demo.jsonl` 找到真实 chunk；
  - 每条 triple 的 `head` 和 `tail` 必须能在对应 chunk 的标题、正文、citation section、entities 或 tags 中找到依据。

## 核心 query 覆盖

| query | GraphSim 路径 | 命中 chunk | 召回价值 |
| --- | --- | --- | --- |
| 张闻天起草的宣传鼓动工作提纲强调了什么？ | 张闻天 --起草--> 党的宣传鼓动工作提纲 | `chunk_szzjys_demo_025` | query 只问人物和文件，GraphSim 可直接连接到提纲所在教材段落。 |
| 抗日战争时期党的干部教育为什么重要？ | 干部教育 --是重要保证--> 抗战胜利 | `chunk_szzjys_demo_022` | 把“抗日战争”和“干部教育”连接到同一段，提升对干部教育制度内容的召回。 |
| 党的一大如何确定思想政治教育的根本目的？ | 党的一大 --确定--> 思想政治教育的根本目的 | `chunk_szzjys_demo_006` | 避免只因“思想政治教育”泛化命中大量段落，优先召回党的一大对应 chunk。 |
| 国民党起义投诚部队为什么要接受人民解放军教育改造？ | 国民党被俘、起义部队 --服从--> 人民解放军的指挥、调动 | `chunk_szzjys_demo_034` | 将 query 中的“起义投诚部队”归一到教材标题中的“国民党被俘、起义部队”，精准命中教育改造段落。 |
| 马克思主义传播为什么成为潮流？ | 马克思主义 --在中国的传播成为--> 滔滔滚滚的潮流 | `chunk_szzjys_demo_003` | 用三元组补足“马克思主义传播”这一核心表达，减少只匹配“马克思主义”的泛化结果。 |
| 三湾改编首创了什么？ | 三湾改编 --首创--> 支部建在连上 | `chunk_szzjys_demo_012` | 直接返回制度创新点，适合图谱问答展示。 |
| 人民解放军的新式整军运动采取了什么方法？ | 新式整军运动 --采取--> 诉苦和三查 | `chunk_szzjys_demo_033` | 通过关系路径定位方法论，不只返回含有“人民解放军”的泛化段落。 |

## graph_score 调整

当前 `retrieve_graph` 的分数由四部分组成：

- 直接实体命中：query entity 出现在 chunk 内容中；
- 扩展实体命中：GraphSim 1-hop 或 2-hop 扩展实体出现在 chunk 内容中；
- 桥接奖励：直接实体和扩展实体同时命中时加小额分；
- 路径分数：由路径长度和关系类型共同决定。

路径分数做了三个约束：

- 1-hop 路径分高于 2-hop 路径；
- `起草`、`成立`、`确定`、`服从`、`采取` 等强语义关系权重高于普通 `关联`；
- 过滤空路径、超过 2-hop 的路径、首尾不匹配的路径、重复节点路径。

这样做的目的，是让 GraphSim 更偏向“短、准、有明确关系”的证据路径，避免所有相关 chunk 都被打到 `0.99` 后无法区分。

## NetworkX 迁移准备

当前 `graph_store.py` 使用的是 adjacency dict：

```python
{
    "张闻天": ["党的宣传鼓动工作提纲", "干部教育部"],
    "党的宣传鼓动工作提纲": ["张闻天", "中央宣传部"]
}
```

迁移到 NetworkX 时，可以保持数据模型不变，只替换底层图结构：

- 节点：`head` 和 `tail` 都作为 graph node；
- 边：每条 triple 作为一条 edge；
- 边属性：保留 `relation`、`source_chunk_ids`；
- 图类型：demo 阶段建议使用 `nx.MultiDiGraph`，因为同一对实体未来可能有多种关系；
- 检索接口：`expand_entities` 可迁移为 `nx.single_source_shortest_path_length`，`find_entity_paths` 可迁移为 `nx.all_simple_paths` 或受限 BFS；
- 兼容策略：先保留当前函数签名，让调用方仍使用 `expand_entities`、`find_entity_paths`，内部再切换到 NetworkX，避免影响 `retrieve_graph`。

## 验证命令

```bash
python -m pytest tests/test_graph_store.py tests/test_retrieve.py
```

