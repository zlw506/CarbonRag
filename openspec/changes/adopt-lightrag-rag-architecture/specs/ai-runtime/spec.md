## ADDED Requirements

### Requirement: Embeddings are resolved through AI runtime providers
CarbonRag SHALL route embedding calls used by the RAG engine through AI runtime provider abstractions and configured runtime settings.

#### Scenario: RAG indexing needs embeddings
- **WHEN** the RAG engine needs embeddings for document chunks
- **THEN** CarbonRag resolves the active embedding provider through AI runtime boundaries instead of calling an external API directly from M5

#### Scenario: Embedding provider is unavailable
- **WHEN** no embedding provider is configured or available
- **THEN** CarbonRag reports provider unavailability to the RAG engine so retrieval can use its configured fallback path

### Requirement: Reranking is an optional AI runtime responsibility
CarbonRag SHALL treat reranking as an optional provider-backed runtime capability used after initial retrieval.

#### Scenario: Reranker is enabled
- **WHEN** retrieval requests reranking and a rerank provider is configured
- **THEN** CarbonRag calls the rerank provider through AI runtime abstractions and records rerank metadata

#### Scenario: Reranker is disabled
- **WHEN** retrieval requests reranking but no rerank provider is configured
- **THEN** CarbonRag returns the original retrieval ranking with metadata explaining that rerank was skipped

### Requirement: Retrieval-only execution avoids chat completion
CarbonRag SHALL support retrieval-only RAG execution without invoking the chat completion provider.

#### Scenario: Retrieval data is requested for debugging or tests
- **WHEN** a caller requests retrieval-only RAG data
- **THEN** CarbonRag returns evidence data without calling the chat model
