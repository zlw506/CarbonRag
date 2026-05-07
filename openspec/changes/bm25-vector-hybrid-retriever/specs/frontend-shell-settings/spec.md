## MODIFIED Requirements

### Requirement: RAG Lab exposes retriever strategy observability
CarbonRag SHALL let RAG Lab users select and inspect experimental retriever strategies.

#### Scenario: User selects a retriever strategy
- **WHEN** a user runs RAG Lab retrieval
- **THEN** the request includes one of `bm25_only`, `vector_only`, or `bm25_vector_hybrid`

#### Scenario: Hybrid result displays source retrievers
- **WHEN** retrieval results include source retriever metadata
- **THEN** RAG Lab displays whether each chunk came from BM25, vector, or both
- **AND** displays merged score metadata when present
