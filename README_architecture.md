# 检索中枢架构说明

## 1. 当前目标

当前阶段的目标不是直接接入真实 Milvus / Neo4j，而是先锁死检索中枢的固定流程、输入输出契约和验收口径，确保团队成员围绕同一条链路协作。

固定流程如下：

`Query -> 实体提取 -> 向量 Top-K -> 图谱 Top-K -> 融合打分 -> 返回带 citation 的候选证据`

## 2. 模块分工

- `src/api/main.py`
  - 负责 HTTP 接口编排
  - 接收 `POST /retrieve`
  - 调用 `src/retriever/hybrid_retriever.py`

- `src/retriever/hybrid_retriever.py`
  - 负责检索中枢逻辑
  - 当前阶段包含：
    - `extract_query_entities`：查询实体提取
    - `retrieve_vector`：向量 Top-K 检索骨架
    - `retrieve_graph`：图谱 Top-K 检索骨架
    - `fuse_results`：融合打分骨架
    - 标准返回体组装

- `configs/schema.yaml`
  - 负责统一数据字段规范
  - 为 ETL、向量索引、图谱构建和接口返回提供共同字段基础

- `tests/demo_queries_sizheng_history.json`
  - 负责当前思政史 Demo 验收问题集合
  - 覆盖绪论、建党、军队政治工作、抗战、解放战争等展示问题

## 3. 当前本地实现说明

为了保证链路先跑通，本地仍保留 `team/mock` 双模式：

- `team`
  - 团队默认模式
  - 返回固定结构，避免默认环境误进入 Demo 命中逻辑

- `mock`
  - 本地 Demo 与联调模式
  - 当前已经从代码内写死 mock 数据升级为读取 `data/processed/text_chunks_demo.jsonl`
  - 用《中国共产党思想政治教育史》Demo chunks 验证：
    - query 实体提取
    - 轻量文本候选召回
    - 轻量 graph_hits 返回
    - 融合排序结果
    - citation.doc / citation.section / citation.page 返回

当前 Demo 版的意义是用真实清洗样本验证接口契约、citation 返回和融合评分结构，而不是替代正式向量库与知识图谱。

当前另有一条真实向量检索实验链路：

- `scripts/run_embedding_faiss_smoke_test.py`
  - 默认读取 `data/processed/text_chunks_sizheng_v1.jsonl` 与 `data/processed/text_chunks_sizheng_v2.jsonl`
  - 使用 `text-embedding-v4` 生成 1024 维向量
  - 使用 FAISS `IndexFlatIP` 与 L2 归一化做余弦相似度检索
  - 输出 `index.faiss`、`metadata.json`、`results.jsonl`、`summary.md`

截至 2026-06-23，245 条思政史 chunks 的 FAISS 冒烟结果为：在章节感知重排后，Recall@1=1.0000，Recall@3=1.0000，Recall@5=1.0000，MRR=1.0000。该结果用于工程验收，不等同于正式论文实验结论。

注意：FAISS 目前已在实验脚本中验证，并已通过 `DACHUANG_VECTOR_BACKEND=faiss` 做成 `/retrieve` 的可选向量后端；默认路径仍保留轻量召回，避免组员本地运行时误消耗 Embedding API。

融合分暂按作战文档口径执行：

`hybrid_score = 0.7 * vector_score + 0.3 * graph_score`

## 4. 返回契约

`/retrieve` 顶层返回固定字段：

- `status`
- `project`
- `query`
- `query_entities`
- `vector_hits`
- `graph_hits`
- `hybrid_hits`
- `answer`
- `citations_used`
- `generator_mode`
- `generator_provider`
- `provider_status`
- `used_fallback`
- `source_check`
- `policy_check`
- `agent_trace`
- `final_decision`

其中：

- `vector_hits` 表示向量侧证据候选
- `graph_hits` 表示 GraphSim / 图谱侧证据候选
- `hybrid_hits` 表示融合后的最终候选
- `answer` 表示基于证据生成的阶段性回答
- `citations_used` 表示回答实际引用的证据
- `source_check` 表示溯源支撑检查结果
- `policy_check` 表示政治红线规则初筛结果
- `agent_trace` 表示检索、生成、审查链路轨迹
- `final_decision` 表示当前回答是否可输出、是否需要人工复核

`hybrid_hits` 当前必须保留：

- `id`
- `source`
- `citation`
- `vector_score`
- `graph_score`
- `hybrid_score`

这是后续可解释性、答辩展示和调参分析的基础。

## 5. 后续迁移路径

后续回到实验室环境时，优先替换 `src/retriever/hybrid_retriever.py` 内部实现，不改 API 契约：

1. 用真实实体识别替换固定词表
2. 在 chunk ID 与 GraphSim triples 对齐后，将可选 FAISS / embedding 链路升级为默认向量召回
3. 用 GraphSim / NetworkX 替换当前轻量 graph_hits
4. 保留统一融合输出结构

这样可以保证前端、测试脚本和团队协作接口不因为底层实现变化而频繁返工。
