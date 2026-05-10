# Change: rag-pro-milvus-runtime-profile-hardening

## Why

CarbonRag V1.6.x has a RAG-Pro-style knowledge base spine, but the default Windows delivery path still points to `milvus_lite` with a local `.db` URI. Native Windows cannot install `milvus-lite`, so contributors can hit a platform blocker even when BGE-M3 models are present.

## What Changes

- Switch the default Windows RAG vector runtime to Docker Milvus Standalone at `http://127.0.0.1:19530`.
- Add explicit runtime profiles for Windows Docker, WSL/Linux/macOS Milvus Lite, and memory development fallback.
- Add Windows scripts to start, stop, and smoke-test Docker Milvus Standalone.
- Report the real vector runtime in health, stats, search, index, and Ask trace instead of labeling Docker Milvus as `milvus_lite`.
- Document offline model package placement, Docker disk-space risk, and native Windows Milvus Lite limitations.

## Out Of Scope

- No ragPdfSystem Celery/RabbitMQ/MinIO migration.
- No knowledge graph UI.
- No third RAG facade.
