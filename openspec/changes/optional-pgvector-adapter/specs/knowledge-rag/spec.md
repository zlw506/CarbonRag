## MODIFIED Requirements

### Requirement: Vector store adapters are disabled-safe
CarbonRag SHALL define a vector store adapter boundary for upsert, search, delete, and healthcheck operations while keeping disabled and current BM25-backed retrieval safe by default.

#### Scenario: Vector store is not configured
- **WHEN** vector indexing or vector search is requested without an enabled vector backend
- **THEN** CarbonRag reports disabled or current health and preserves BM25 fallback behavior

#### Scenario: Current retrieval remains the default
- **WHEN** `RAG_VECTOR_BACKEND` is unset or set to `current`
- **THEN** CarbonRag uses `CurrentVectorStoreAdapter`
- **AND** it does not connect to pgvector

#### Scenario: pgvector is explicitly configured
- **WHEN** `RAG_VECTOR_BACKEND=pgvector` and vector retrieval is enabled
- **THEN** CarbonRag may query `PgVectorStoreAdapter` for vector hits
- **AND** retrieval-only metadata reports pgvector backend, health, adapter name, and vector hit count

#### Scenario: pgvector is unavailable
- **WHEN** pgvector is configured but the database, extension, table, or query is unavailable
- **THEN** CarbonRag falls back to `CurrentVectorStoreAdapter`
- **AND** metadata records fallback status and reason

#### Scenario: pgvector adapter supports minimal operations
- **WHEN** chunks and embeddings are supplied to `PgVectorStoreAdapter`
- **THEN** it can upsert by `chunk_id`, search top-k by embedding, filter by source type, document id, or visibility, and delete by document id

#### Scenario: Existing flows remain compatible
- **WHEN** optional pgvector support is added
- **THEN** retrieval-only, RAG Lab, and `/ask` default behavior continue to work without requiring Postgres or pgvector
