# Change: rag-pro-testqa-and-ask-binding-hardening

## Why

CarbonRag V1.6.x has a RAG-Pro-style spine and AskPage already carries `kb_id` and `rag_mode`, but the project still needs regression coverage proving that the selected KB and retrieval mode reach the runtime/tool layer. The KnowledgeBaseWorkbench Test QA path also still behaves like retrieval snippet stitching, which can be mistaken for mature RAG answer generation.

## What Changes

- Lock the AskPage -> session endpoint -> AI Runtime tool argument path for `kb_id` and `rag_mode`.
- Upgrade `/api/v1/rag/test-qa` to perform retrieval, build a grounded prompt, call the configured chat provider, and return citations, selected chunks, evidence quality, confidence, provider metadata, and retrieval trace.
- Return explicit `no_hits` without calling the model when retrieval produces no evidence.
- Clarify KnowledgeBaseWorkbench actions: retrieval-only test, generated test answer, and formal AskPage conversation.
- Downgrade the legacy RAG Lab to an admin-only experimental entry.

## Out Of Scope

- No new retrieval algorithms.
- No knowledge graph UI.
- No Docker/Milvus runtime expansion.
- No third RAG facade.
