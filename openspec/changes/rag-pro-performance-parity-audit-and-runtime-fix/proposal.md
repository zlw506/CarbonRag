# Change: rag-pro-performance-parity-audit-and-runtime-fix

## Why

CarbonRag V1.6.24 has a RAG-Pro-style knowledge base spine and one-click ingestion, but performance symptoms are still hard to diagnose. The main risk is no longer missing UI: the runtime path can still spend unobserved time in Milvus client creation, embedding, sparse scanning, rerank, eval, or LLM generation.

## What Changes

- Add a V1.6.29 performance gap audit against `3rdparty/RAG-Pro/RAG-Pro`.
- Make Milvus client usage reusable per URI and report `milvus_client_init_count`.
- Add `RagTimingTrace` to pipeline, search, answer, and test QA responses.
- Split one-click ingestion into `quick` and `acceptance` modes; quick mode does not run eval or LLM work.
- Cache sparse retrieval corpus per KB/chunk watermark and expose cache hit timing.
- Add profile scripts that write reproducible JSON traces under `logs/rag/`.
- Update KnowledgeBaseWorkbench labels so the default action is fast ingestion, while acceptance scoring is explicit.

## Out Of Scope

- No new retrieval algorithm.
- No knowledge graph UI.
- No carbon accounting changes.
- No Celery/RabbitMQ/MinIO async pipeline in this round.
