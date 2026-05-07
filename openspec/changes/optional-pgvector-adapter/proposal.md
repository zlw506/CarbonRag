## Why

CarbonRag already has a `VectorStoreAdapter` boundary and a current BM25-backed adapter. V1.5.0 should add a pgvector MVP for small and medium private deployments while keeping the existing current/BM25 retrieval path as the default and safe fallback.

## What Changes

- Add `PgVectorStoreAdapter` behind the existing `VectorStoreAdapter` contract.
- Add `RAG_VECTOR_BACKEND=current|pgvector`, defaulting to `current`.
- Add a minimal pgvector SQL initialization file under `scripts/sql/init_pgvector.sql`.
- Route pgvector search only when explicitly configured and vector retrieval is enabled.
- Fall back to `CurrentVectorStoreAdapter` when pgvector is unavailable, returns no hits, or raises an error.
- Add vector metadata for backend, health, adapter name, vector hit count, fallback status, and fallback reason.
- Add tests that use fake/mock pgvector behavior without requiring a real Postgres or pgvector service in CI.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add an optional pgvector vector store adapter and fallback-safe retrieval metadata.
- `devops-release`: Document the optional pgvector SQL bootstrap and disabled-by-default environment switch.

## Impact

- Affected modules: M5 primary, M7 env/template and SQL bootstrap.
- Apply-stage areas: `backend/app/rag/vector_store.py`, `backend/app/rag/service.py`, `backend/app/rag/schemas.py`, `backend/app/core/config.py`, `.env.example`, frontend RAG types/page, tests, and `scripts/sql/init_pgvector.sql`.
- No default retrieval change, `/ask` change, RAG Lab breakage, retrieval-only response removal, Qdrant, Milvus, Weaviate, GraphRAG, or mandatory Postgres switch is proposed.
