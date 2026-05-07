## MODIFIED Requirements

### Requirement: Vector store adapters are disabled-safe
CarbonRag SHALL define a vector store adapter boundary for upsert, search, delete, and healthcheck operations while keeping disabled and current BM25-backed retrieval safe by default.

#### Scenario: Vector store is not configured
- **WHEN** vector indexing or vector search is requested without an enabled vector backend
- **THEN** CarbonRag reports disabled health and preserves BM25 fallback behavior

#### Scenario: Current retrieval is wrapped by an adapter
- **WHEN** retrieval-only execution falls back to the current public, private, or mixed chunk search
- **THEN** CarbonRag can route the search through `CurrentVectorStoreAdapter` without changing the returned chunks, references, or fallback semantics

#### Scenario: Fake vector store is used in tests
- **WHEN** tests use `FakeVectorStoreAdapter`
- **THEN** CarbonRag returns deterministic chunks without requiring embeddings or an external vector service

#### Scenario: Adapter health is observable
- **WHEN** retrieval-only metadata is returned
- **THEN** CarbonRag includes vector backend, adapter name, and health status when available
