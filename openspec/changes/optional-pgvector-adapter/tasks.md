# Tasks

## Proposal

- [x] Create V1.5.0 OpenSpec change for optional pgvector adapter.
- [x] Confirm `VectorStoreAdapter`, `CurrentVectorStoreAdapter`, and BM25 fallback exist.

## Apply

- [x] Add `RAG_VECTOR_BACKEND=current` config and env template entry.
- [x] Add `PgVectorStoreAdapter` implementing healthcheck, upsert, search, and delete.
- [x] Add minimal SQL bootstrap for pgvector.
- [x] Add vector backend factory/selection without changing default current behavior.
- [x] Route explicitly configured pgvector retrieval with current/BM25 fallback on unavailable/error/no-hit.
- [x] Add `vector_hit_count` retrieval metadata and RAG Lab display/type support.
- [x] Export pgvector adapter without removing current/fake/disabled adapters.
- [x] Add adapter and fallback tests using fake/mock pgvector behavior.
- [x] Run `openspec validate optional-pgvector-adapter --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
- [x] Commit locally without push or PR.
