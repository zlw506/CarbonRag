## Scope

This change wraps existing retrieval behavior. It does not switch CarbonRag to a real vector backend.

## Adapter Shape

- Keep synchronous methods because current retrievers are synchronous.
- Keep `DisabledVectorStoreAdapter` for unavailable vector storage.
- Add `CurrentVectorStoreAdapter` as a read-through adapter over existing BM25 retrievers.
- Add `FakeVectorStoreAdapter` for tests.

## Runtime Behavior

- `CurrentVectorStoreAdapter.search()` delegates to the same public/private/mixed retrievers currently called by `RagEngineService._fallback_search()`.
- `RagEngineService` can use the adapter for fallback search while preserving `RetrievalResult` output.
- Metadata records adapter name, backend, and health so the RAG Lab can show whether the current adapter is disabled, current/in-memory, or fake in tests.

## Non-Goals

- No pgvector, Qdrant, Milvus, Weaviate, Postgres dependency, deployment change, GraphRAG, or RAG engine rewrite.
