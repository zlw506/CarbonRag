# Design: RAG-Pro parity evaluation and hardening

## Main Spine

`backend/app/rag` remains the formal RAG spine. `backend/app/langchain_rag` stays as a compatibility adapter for tool names and legacy callers.

## Parity Fields

Knowledge bases carry embedding and retrieval defaults. Documents carry file metadata and progress/error stages. Chunks carry keywords, generated questions, token count, parent chunk linkage, and vector ids.

## Direct KB Upload

`POST /api/v1/kb/{kb_id}/documents/upload` stores the uploaded file with a server-generated name, creates a `RagDocument`, and lets users drive parse, chunk, and index from the workbench.

## Grounded Answer

`/rag/answer` and `/rag/test-qa` share the same pattern:

1. Retrieve selected chunks.
2. Build a grounded evidence prompt.
3. Call the configured chat provider.
4. Return answer, answer mode, provider details, selected chunks, citations, evidence quality, confidence, and retrieval trace.

If the provider is unavailable, the API returns `retrieval_only` with trace and citations. If there are no hits, it returns `no_hits` and must not call the provider.

## Evaluation

Eval runs use gold questions against a selected KB. Metrics include Hit@1, Hit@3, Recall@5, Precision@5, MRR, citation coverage, answer mode rate, no-hit count, vector failure count, and cross-KB leak count.
