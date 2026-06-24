# Traceable Ideological Education RAG

[中文说明](./README.zh-CN.md)

Traceable KG-RAG system for ideological education with citation grounding, multi-agent review, political safety checking, and cross-modal learning interaction.

This repository is part of a National College Student Innovation and Entrepreneurship Training Program project. The current focus is to build a traceable retrieval backend, stable API contract, and evidence-grounded response workflow for ideological education materials.

> Status: backend-first prototype with real FAISS smoke validation. Current implementation focuses on retrieval API, schema stability, citation structure, generation scaffolding, source checking, policy checking, and demo validation. The FAISS path can now be enabled for `/retrieve` through `DACHUANG_VECTOR_BACKEND=faiss`, while the default path remains the stable lightweight retriever. Full cross-modal interaction, digital-human presentation, and XR sandbox workflows are planned stages.

## What It Does

Current implemented capabilities:

- Provides a FastAPI backend.
- Exposes `/health` and `/retrieve` APIs.
- Returns a stable retrieval response structure.
- Reads processed ideological education text chunks.
- Validates a 245-chunk ideological education corpus through a Qwen `text-embedding-v4` + FAISS smoke workflow.
- Provides an optional FAISS vector backend for `retrieve_vector`.
- Uses a schema-driven API contract.
- Includes graph storage, evidence generation, source checking, and policy checking modules.
- Maintains demo questions and basic acceptance tests.
- Keeps project deliverables separated from core code.

Planned capabilities:

- Promote the optional FAISS backend to the default vector path after chunk IDs and GraphSim triples are fully aligned.
- Stronger hybrid retrieval with keyword, vector, structured fields, and reranking.
- Knowledge graph reasoning for people, events, places, timelines, and ideological concepts.
- Multi-agent review workflow for generation, citation auditing, and political safety review.
- Timeline, map, event-card, digital-human, or XR-based learning interaction.

## Why This Project Exists

Ideological education materials usually involve long historical timelines, complex relationships between people and events, and strict requirements for source-grounded expression. A normal open-domain chatbot may generate plausible but unsupported answers, which is not suitable for teaching support.

This project follows a retrieval-first and audit-first workflow:

```text
retrieve evidence -> generate answer -> check citations -> review safety boundary -> display to learners
```

## Architecture

Target architecture:

```text
User Query
    |
    v
Intent Router
    |
    v
Hybrid Retriever
    |
    v
Knowledge Graph Reasoner
    |
    v
Generation Agent
    |
    v
Citation Auditor
    |
    v
Political Safety Auditor
    |
    v
Cross-modal Interaction Layer
```

The current repository implements the backend foundation first. Some downstream modules are present as scaffolding or planned integration points, not as a completed production system.

## Tech Stack

- Backend: FastAPI, Python
- Retrieval: hybrid retriever scaffold, FAISS-ready dependency
- Graph module: NetworkX-ready graph store
- Schema and config: YAML, JSON
- Validation and tests: pytest, JSONL validation utilities

## Current Repository Scope

```text
src/                   Core backend code
configs/               Schema and API contract
data/                  Runtime demo data
tests/                 Acceptance and module tests
docs/                  Knowledge-base ingestion notes
team_deliverables/     Reports, presentation materials, drafts, and team notes
outputs/               Local outputs
README_run.md          Local running guide
README_architecture.md Retrieval architecture notes
```

Core code should stay outside `team_deliverables/`. Runtime data should stay inside `data/`. Presentation drafts and team materials can stay in `team_deliverables/`.

## Current Retrieval Experiment

The latest local FAISS smoke test uses:

- `data/processed/text_chunks_sizheng_v1.jsonl`
- `data/processed/text_chunks_sizheng_v2.jsonl`
- `text-embedding-v4`
- 1024-dimensional embeddings
- `IndexFlatIP` with L2 normalization

The 2026-06-23 smoke run on 245 chunks and 10 demo questions reported:

| Metric | Value |
|---|---:|
| Recall@1 | 1.0000 |
| Recall@3 | 1.0000 |
| Recall@5 | 1.0000 |
| MRR | 1.0000 |

This is an engineering smoke-test result, not a formal paper experiment. The score includes the smoke script's lightweight section-aware rerank for near-neighbor sections. The validated FAISS path can be enabled through `DACHUANG_VECTOR_BACKEND=faiss` and `DACHUANG_FAISS_INDEX_DIR`, while `/retrieve` keeps the same stable response contract.

## Quick Start

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the API:

```powershell
uvicorn src.api.main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

Retrieve API:

```text
POST /retrieve
```

Example request:

```json
{
  "query": "延安时期思想政治教育有什么特点？"
}
```

Run tests:

```powershell
python -m pytest tests -q
```

## API Contract

The current `/retrieve` response includes:

- `status`
- `project`
- `query`
- `query_entities`
- `citations`
- `answer`
- `debug`

The response structure will evolve as graph reasoning, generation agents, and auditing agents are added. Backward compatibility should be considered when frontend integration begins.

## Roadmap

| Phase | Goal |
| --- | --- |
| Phase 1 | Build KG-RAG backend, schema, retrieval API, and validation questions |
| Phase 2 | Add stronger vector retrieval and knowledge graph modules |
| Phase 3 | Integrate generation, citation auditing, and political safety auditing agents |
| Phase 4 | Build timeline, map, and event-card interaction layers |
| Phase 5 | Explore XR sandbox, digital-human explanation, and classroom demo workflow |

## Safety and Use Boundary

This system is designed for ideological education support, teaching demonstration, and source-grounded knowledge retrieval. It does not replace teachers, official teaching materials, or final human review.

Generated content should be used only after citation checking and safety review. When evidence is missing, mismatched, or insufficient, the system should report insufficient evidence rather than produce unsupported claims.
