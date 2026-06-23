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

