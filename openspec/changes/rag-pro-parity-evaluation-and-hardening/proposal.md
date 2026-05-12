# Change: rag-pro-parity-evaluation-and-hardening

## Why

CarbonRag V1.6.x already has a RAG-Pro-style knowledge base spine, but it still needs direct KB upload, RAG-Pro parity fields, grounded answer consistency, and measurable acceptance metrics. Without a fixed eval fixture and metrics, the team cannot distinguish real RAG progress from UI and trace appearance.

## What Changes

- Add RAG-Pro adoption authorization and freeze RAG-Pro as the main implementation spine.
- Extend KnowledgeBase, Document, and Chunk metadata to include RAG-Pro parity fields.
- Add direct upload into a selected KB and expose document status for parse/chunk/index progress.
- Align `/rag/answer` and `/rag/test-qa` around grounded LLM answers with retrieval trace and citations.
- Add `rag_pro_search` and `rag_pro_answer` as official AI Runtime tools while keeping old names compatible.
- Add RAG eval runs/cases, a Qingmu 2025Q1 fixture, gold questions, and acceptance metrics.

## Out Of Scope

- No knowledge graph UI.
- No ragPdfSystem Celery/RabbitMQ/MinIO migration.
- No carbon accounting business expansion.
- No submission of ignored third-party source trees.
