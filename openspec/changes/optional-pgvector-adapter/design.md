## Scope

This change adds a pgvector adapter boundary and fallback-safe service selection. It does not add a full vector indexing workflow, managed migration runner, or non-Postgres vector database.

## Adapter Strategy

- `CurrentVectorStoreAdapter` remains the default backend.
- `PgVectorStoreAdapter` is constructed only when `RAG_VECTOR_BACKEND=pgvector`.
- The adapter does not connect during construction.
- `healthcheck()` attempts a lightweight connection/query and reports degraded health instead of raising.
- Public adapter methods return safe result objects with error metadata instead of crashing application startup.

## Retrieval Strategy

- With `RAG_VECTOR_BACKEND=current`, the existing vector retriever and BM25 fallback behavior remain unchanged.
- With `RAG_VECTOR_BACKEND=pgvector` and vector retrieval enabled, the RAG service queries pgvector using the embedding provider.
- If pgvector is unavailable, errors, or has no hits, the service falls back to `CurrentVectorStoreAdapter`.
- Retrieval-only metadata continues to expose existing fields and adds `vector_hit_count`.

## SQL Strategy

- Add `scripts/sql/init_pgvector.sql` as a minimal manual bootstrap script.
- The SQL creates the pgvector extension and a `rag_embeddings` table.
- The table stores chunk text, metadata, source fields, model name, and vector embedding.
- This does not replace the existing runtime database bootstrap or force local development onto Postgres.

## Non-Goals

- No Qdrant, Milvus, Weaviate, GraphRAG, Neo4j, or heavy indexing workflow.
- No automatic production migration runner.
- No removal of BM25 fallback or current adapter.
