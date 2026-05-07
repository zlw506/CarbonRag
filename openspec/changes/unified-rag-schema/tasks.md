# Tasks

## Proposal

- [x] Create V1.3.2 OpenSpec change for unified RAG schema.
- [x] Confirm scope is schema/type/adapter only.

## Apply

- [x] Extend existing RAG contract models instead of duplicating type definitions.
- [x] Add adapter helpers for public/private `RetrievedChunk` to `ChunkRecord`.
- [x] Add adapter helpers for RAG evidence references to `CitationRef`.
- [x] Add retrieval result to `RetrievalTrace` adapter.
- [x] Attach richer retrieval trace data to retrieval-only metadata without removing existing fields.
- [x] Add backend tests for public chunk, private chunk, reference, retrieval trace, retrieval-only response compatibility, and `/ask` regression.
- [x] Run `openspec validate unified-rag-schema --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build to guard RAG Lab compatibility.
