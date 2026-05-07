# Tasks

## Proposal

- [x] Create V1.3.3 OpenSpec change for VectorStoreAdapter boundary.
- [x] Confirm scope is wrapping current retrieval only.

## Apply

- [x] Extend the existing VectorStoreAdapter boundary without duplicating it.
- [x] Add `CurrentVectorStoreAdapter` that wraps current public/private/mixed retrieval.
- [x] Add `FakeVectorStoreAdapter` for deterministic tests.
- [x] Route fallback search through the current adapter without changing retrieval results.
- [x] Add vector backend metadata to retrieval-only responses and RAG Lab display.
- [x] Add tests for fake adapter search, current adapter search, healthcheck, retrieval-only compatibility, `/ask` regression, and BM25 fallback preservation.
- [x] Run `openspec validate vector-store-adapter-boundary --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
