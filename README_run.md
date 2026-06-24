# 多智能体赋能的跨模态零幻觉交互式思政教育系统 - 开发指南

## ⚙️ 1. 环境准备（当前：Windows 本地试运行）
确保你已经安装 Conda，并在 PowerShell 执行：
```powershell
conda activate dachuang
pip install fastapi uvicorn faiss-cpu networkx pyyaml
```

## 🛠️ 2. 执行纪律：先 Sample，后全量
为了保证数据质量，严禁跳过质检步骤！提交任何数据样本（Sample）或全量数据前，必须在本地运行质检脚本：

```powershell
# 示例：校验你清洗出来的 events.jsonl
python src/utils/validate_jsonl.py data/processed/events.jsonl
```

注意：只有终端打印出 ✅ 质检通过！，才允许将数据提交给组长验收。如果报错，请对照 configs/schema.yaml 自行修改。

## 🌐 3. 本地接口预览（Mock 环境）
当你需要调试后端接口时，启动 FastAPI 服务：

```powershell
uvicorn src.api.main:app --reload
```

服务启动后，可以在浏览器访问 http://127.0.0.1:8000/docs 查看自动生成的 API 文档。
后续迁移到实验室 WSL2 时，命令基本不变，仅终端环境切换。

## 🧪 4. FAISS 向量检索冒烟实验

确认 `.env.local` 中已经配置 `DASHSCOPE_API_KEY` 后，可以运行：

```powershell
D:\anaconda\envs\dachuang_2026\python.exe -X utf8 scripts\run_embedding_faiss_smoke_test.py --limit 10 --top-k 5
```

默认索引语料：

```text
data/processed/text_chunks_sizheng_v1.jsonl
data/processed/text_chunks_sizheng_v2.jsonl
```

输出目录：

```text
outputs/vector_experiments/2026-06-faiss-smoke/
```

主要输出：

- `index.faiss`
- `metadata.json`
- `results.jsonl`
- `summary.md`

注意：该命令会调用阿里云百炼 `text-embedding-v4`，会产生少量 API token 消费。除非正在做负责人验收或正式实验记录，组员不要重复重建索引；若 chunk 数据、模型和维度未变化，应优先使用 `--reuse-index-dir` 复用已有索引。

## 5. 可选启用 FAISS 后端

默认 `/retrieve` 仍使用轻量文本召回，保证组员本地能稳定运行。负责人验收真实 FAISS 链路时，可以临时启用：

```powershell
$env:DACHUANG_RETRIEVE_MODE="mock"
$env:DACHUANG_LOCAL_MOCK_ACK="1"
$env:DACHUANG_VECTOR_BACKEND="faiss"
$env:DACHUANG_FAISS_INDEX_DIR="outputs\vector_experiments\2026-06-faiss-smoke\20260623_213511"
uvicorn src.api.main:app --reload
```

启用后，`retrieve_vector()` 会优先读取：

```text
DACHUANG_FAISS_INDEX_DIR/index.faiss
DACHUANG_FAISS_INDEX_DIR/metadata.json
```

如果索引目录不存在、API key 缺失、Embedding 调用失败或维度不匹配，系统会自动回退到原来的轻量召回，不会破坏 `/retrieve` 返回契约。

## 6. 后端对比实验：轻量检索 vs FAISS

在不改变默认 `/retrieve` 行为的前提下，可以运行 10 题小样本对比：

```powershell
D:\anaconda\envs\dachuang_2026\python.exe -X utf8 scripts\run_retrieve_backend_comparison.py `
  --faiss-index-dir outputs\vector_experiments\2026-06-faiss-smoke\20260623_213511 `
  --limit 10
```

输出位于：

```text
outputs/retrieve_experiments/2026-06-backend-comparison/
```

说明：

- lightweight 组不调用 embedding。
- FAISS 组只调用 query embedding，不重建索引。
- 脚本强制 `DACHUANG_GENERATOR_MODE=template`，不调用 LLM。
- 结果用于判断 FAISS 是否具备进入默认检索链路的条件。
