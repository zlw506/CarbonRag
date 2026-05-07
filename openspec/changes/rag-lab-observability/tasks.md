# Tasks

## Proposal

- [x] Create V1.3.1 OpenSpec change for RAG Lab observability.
- [x] Define M5/M7-only scope and non-goals.

## Apply

- [x] Add retrieval-only metadata fields for mode, counts, fallback, and latency.
- [x] Add structured retrieval-only runtime error handling.
- [x] Update RAG Lab types to tolerate missing metadata fields.
- [x] Show backend base URL, retrieval endpoint, request parameters, active retrieval mode, fallback state, zero-hit state, and error details.
- [x] Add backend tests for metadata, zero hits, invalid query, invalid top-k, and fallback state.
- [x] Run `openspec validate rag-lab-observability --strict`.
- [x] Run `openspec validate --all`.
- [x] Run focused backend tests.
- [x] Run frontend typecheck and build.
