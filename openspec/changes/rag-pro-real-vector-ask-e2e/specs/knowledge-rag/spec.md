## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose a KnowledgeBase -> Document -> Chunk -> Retrieval -> Answer spine as the primary RAG path.

#### Scenario: Document indexes into real vector backend

- **WHEN** a user indexes a parsed and chunked document
- **THEN** CarbonRag writes chunk vectors into the configured vector backend and records the vector backend, indexed count, and any warnings on the document status.

### Requirement: RAG search returns transparent hybrid retrieval trace

RAG search SHALL return dense, sparse, RRF, rerank, backend, degradation, and citation metadata.

#### Scenario: AskPage selects a knowledge base

- **WHEN** a user asks from AskPage with `kb_id` and `rag_mode`
- **THEN** CarbonRag searches that knowledge base through the RAG spine and returns retrieval trace metadata with the answer.

#### Scenario: Real vector runtime is unavailable

- **WHEN** Milvus Lite, BGE-M3, or the reranker cannot run
- **THEN** CarbonRag reports failed indexing or degraded search explicitly instead of returning fake vector success.
