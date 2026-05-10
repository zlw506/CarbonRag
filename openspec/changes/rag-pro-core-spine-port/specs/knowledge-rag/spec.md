## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose a KnowledgeBase -> Document -> Chunk -> Retrieval -> Answer spine as the primary RAG path.

#### Scenario: User creates and tests a knowledge base

- **WHEN** a user creates a knowledge base and indexes documents
- **THEN** CarbonRag stores document status, chunks, retrieval trace, citations, and test QA results under that knowledge base.

### Requirement: RAG search returns transparent hybrid retrieval trace

RAG search SHALL return dense, sparse, RRF, rerank, backend, degradation, and citation metadata.

#### Scenario: Vector backend is unavailable

- **WHEN** vector search cannot use a real backend
- **THEN** the response marks `degraded=true` and includes an explicit warning instead of pretending vector search succeeded.

