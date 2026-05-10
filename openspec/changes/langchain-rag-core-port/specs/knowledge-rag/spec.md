## ADDED Requirements

### Requirement: LangChain RAG is the default competition retrieval path

CarbonRag SHALL use a LangChain-based RAG path when `RAG_LANGCHAIN_ENABLED=true`, combining knowledge chunks, BM25 retrieval, vector retrieval, optional HyDE, optional rerank, and structured citations.

#### Scenario: Ask uses LangChain RAG
- **WHEN** a user asks in `public`, `private_sample`, or `mixed` scope and LangChain RAG is enabled
- **THEN** the ask runtime invokes the LangChain RAG search tool before answer generation
- **AND** the response exposes retrieval trace metadata for BM25, vector, HyDE, rerank, and fallback state

### Requirement: RAG documents preserve citation metadata

CarbonRag SHALL map indexed `knowledge_chunks` to metadata-rich LangChain documents.

#### Scenario: Chunk enters LangChain RAG
- **WHEN** a knowledge chunk is converted to a LangChain document
- **THEN** metadata includes `chunk_id`, `knowledge_item_id`, `file_id`, `owner_user_id`, `library_scope`, `source_type`, `title`, page/sheet/slide fields, section title, and source URL where available

### Requirement: Hybrid retrieval combines sparse and vector candidates

CarbonRag SHALL combine BM25 and vector retrieval candidates with query-length-aware weights.

#### Scenario: Hybrid retrieval runs
- **WHEN** a RAG search request is processed
- **THEN** CarbonRag retrieves sparse and vector candidates where available
- **AND** short queries prefer BM25, long queries prefer vector retrieval, and medium queries use balanced weights

### Requirement: Optional RAG steps fail visibly

CarbonRag SHALL report unavailable optional RAG components instead of silently pretending they succeeded.

#### Scenario: Vector store unavailable
- **WHEN** Chroma or vector indexing is unavailable
- **THEN** the retrieval trace records `vector unavailable` or an equivalent fallback reason
- **AND** BM25 retrieval may continue if enabled

#### Scenario: HyDE or rerank fails
- **WHEN** HyDE generation or CrossEncoder rerank fails
- **THEN** CarbonRag falls back to the original query or unreranked hits
- **AND** the retrieval trace includes a warning or fallback reason

### Requirement: RAG APIs expose direct validation points

CarbonRag SHALL expose protected APIs for RAG health, index stats, rebuild, file indexing, search, and answer generation.

#### Scenario: Developer validates RAG
- **WHEN** an authenticated user calls `/api/v1/rag/search`
- **THEN** CarbonRag returns hits with scores, source metadata, and retrieval trace without requiring a chat completion call
