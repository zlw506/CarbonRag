## Why

CarbonRag currently has working public/private/mixed chunk retrieval through BM25 fallback and an early disabled vector-store boundary. Before pgvector, Qdrant, Milvus, or Weaviate are introduced, V1.3.3 should wrap the current retrieval behavior behind a VectorStoreAdapter-compatible boundary so future vector stores can be swapped in without changing RAG Lab, retrieval-only API, or `/ask` defaults.

## What Changes

- Extend the existing `app.rag.vector_store` boundary instead of creating a duplicate interface.
- Add `CurrentVectorStoreAdapter` that delegates to the current public/private/mixed retrievers and preserves current retrieval results.
- Add `FakeVectorStoreAdapter` for deterministic tests without embeddings or external services.
- Add vector adapter observability metadata to retrieval-only responses and the RAG Lab.
- Keep BM25 fallback behavior, retrieval-only output shape, `/ask`, report, and carbon calculation unchanged.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add an adapter boundary around current chunk retrieval and vector-store health metadata.
- `frontend-shell-settings`: Display vector adapter/backend metadata in the RAG Lab when provided.

## Impact

- Affected modules: M5 primary; M3 only for metadata display.
- Apply-stage areas: `backend/app/rag/vector_store.py`, `backend/app/rag/service.py`, RAG schemas/types, RAG tests, and RAG Lab metadata display.
- No new database, vector backend, deployment, parser, graph, or large dependency is introduced.
