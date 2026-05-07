# Tasks

## Proposal

- [x] Create V1.5.1 OpenSpec change for BM25 + vector hybrid retrieval.
- [x] Confirm BM25 fallback, `VectorStoreAdapter`, and RAG Lab retrieval-only API exist.

## Apply

- [x] Add `RetrieverStrategy` with BM25, vector, and hybrid implementations.
- [x] Add experimental retrieval strategy parameter to retrieval-only request models.
- [x] Preserve default `/ask`, naive/mix, calc, report, and session behavior.
- [x] Add hybrid merge metadata on chunks and retrieval metadata.
- [x] Add RAG Lab strategy selector and source retriever display.
- [x] Add backend tests for BM25, vector, hybrid dedupe, and vector-unavailable fallback.
- [x] Add retrieval-only API compatibility tests.
- [x] Run `openspec validate bm25-vector-hybrid-retriever --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
- [x] Commit locally without push or PR.
