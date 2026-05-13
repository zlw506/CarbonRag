## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose a KnowledgeBase -> Document -> Chunk -> Retrieval -> Answer spine as the primary RAG path.

#### Scenario: Document pipeline supports quick and acceptance modes

- **WHEN** a user triggers document pipeline execution without specifying a mode
- **THEN** CarbonRag runs quick mode: parse, chunk, index, and search smoke
- **AND** does not run eval smoke or LLM generation by default
- **AND** the response includes `pipeline_mode="quick"` and `timing_trace`

#### Scenario: Acceptance pipeline runs explicit evaluation

- **WHEN** a user triggers document pipeline execution with `pipeline_mode="acceptance"`
- **THEN** CarbonRag runs parse, chunk, index, search smoke, and eval smoke in order
- **AND** the response reports eval pass/fail or an `eval_not_configured` warning

#### Scenario: RAG runtime timing is visible

- **WHEN** a user runs pipeline, search, test QA, or answer
- **THEN** CarbonRag returns timing fields for DB chunk loading, embedding, Milvus client/search/insert, sparse retrieval, RRF, rerank, LLM, total time, candidate counts, Milvus client initialization count, and sparse cache state
- **AND** the frontend can display which runtime stage is slow without relying only on backend logs

#### Scenario: Warm Milvus and sparse paths avoid repeated setup

- **WHEN** two searches run against the same Milvus URI and unchanged KB chunks
- **THEN** the second search reuses the Milvus client
- **AND** the sparse corpus cache can be reused for the unchanged KB
- **AND** trace data exposes the reuse through `milvus_client_init_count` and `sparse_cache_hit`
