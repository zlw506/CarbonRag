# Design: RAG-Pro Usability and Pipeline Hardening

## One-Click Pipeline

The V1.6.24 pipeline is synchronous by design. It runs the same underlying RAG-Pro spine operations already exposed as manual actions:

1. Parse the document if it is not parsed.
2. Chunk the document if it is not chunked or has no chunks.
3. Index the chunks if the document is not indexed or indexed chunk count is incomplete.
4. Run a search smoke query generated from the first non-empty chunk or document title.
5. Run the default eval smoke only when `backend/tests/fixtures/rag/gold_questions.json` is available.

The response always reports `failed_stage`, `error_message`, and `warnings` so the workbench can explain exactly where the pipeline stopped.

## Acceptance Path

The formal RAG-Pro acceptance route is:

- `KnowledgeBaseWorkbench`
- `AskPage`
- `/api/v1/rag/search`
- `/api/v1/rag/answer`
- `/api/v1/rag/test-qa`
- `/api/v1/rag/eval/run`

`/api/v1/rag/retrieve` remains available only for admin legacy diagnostics. It is not an acceptance path.

## AskPage Proof

AskPage renders an expandable proof panel per answer. The panel is deliberately operational rather than decorative: degraded runtime, `memory_dev`, zero dense hits, zero citations, and missing rerank under `hybrid_rerank` are surfaced as explicit risks.

## Eval Gate

Eval remains lightweight in this round, but it becomes a product gate. A pipeline can complete technical stages while still reporting eval warnings or failure. That distinction prevents "indexed" from being confused with "RAG accepted".
