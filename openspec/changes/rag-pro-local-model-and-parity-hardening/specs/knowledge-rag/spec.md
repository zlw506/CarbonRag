## MODIFIED Requirements

### Requirement: RAG-Pro local model parity is verifiable
CarbonRag SHALL provide a terminal-first local model setup path for the RAG-Pro spine using BGE-M3, bge-reranker, and Milvus Lite/Milvus.

#### Scenario: Developer prepares local RAG models
- **WHEN** a developer runs the RAG model download script
- **THEN** `BAAI/bge-m3` and `BAAI/bge-reranker-v2-m3` are downloaded to ignored `data/outputs` model cache paths
- **AND** no model files are written into tracked source directories

#### Scenario: Developer runs local RAG smoke
- **WHEN** the local model smoke script runs on a supported platform
- **THEN** BGE-M3 returns 1024-dimensional dense vectors and non-empty sparse weights
- **AND** Milvus Lite/Milvus indexes and retrieves at least one chunk
- **AND** the response trace identifies the real vector backend

#### Scenario: Local model dependency is unavailable
- **WHEN** BGE-M3, bge-reranker, FlagEmbedding, pymilvus, or Milvus Lite is unavailable
- **THEN** CarbonRag reports degraded or failed status instead of reporting RAG success
