# Change: rag-pro-usability-and-pipeline-hardening

## Why

CarbonRag V1.6.x already has a RAG-Pro-style spine, KnowledgeBaseWorkbench, AskPage `kb_id/rag_mode` binding, Milvus/BGE/RRF/rerank trace, and eval endpoints. The remaining risk is usability and acceptance ambiguity: users must manually run parse/chunk/index, legacy `/rag/retrieve` can still be mistaken for the formal RAG path, and AskPage does not make enough proof visible when RAG is degraded or missing citations.

## What Changes

- Add one-click document pipeline endpoints for `parse -> chunk -> index -> search smoke -> eval smoke`.
- Add batch pipeline execution for documents that are not indexed or previously failed.
- Make KnowledgeBaseWorkbench recommend "一键入库验收" while keeping manual parse/chunk/index as advanced operations.
- Keep `/rag/retrieve` as admin-only legacy diagnostics and remove it from the RAG-Pro acceptance route.
- Keep `rag_pro_search` and `rag_pro_answer` as formal tool names; legacy `langchain_rag_*` names remain only for compatibility.
- Add an AskPage RAG proof panel showing KB, mode, provider, vector runtime, hit counts, rerank state, citations, selected chunks, and warnings.
- Upgrade eval visibility into an acceptance gate rather than a hidden diagnostic.

## Out Of Scope

- No new retrieval algorithm.
- No knowledge graph UI.
- No carbon accounting changes.
- No Celery/RabbitMQ/MinIO async pipeline in this round.
