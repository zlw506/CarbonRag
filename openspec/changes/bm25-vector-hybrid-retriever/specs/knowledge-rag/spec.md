## MODIFIED Requirements

### Requirement: Retrieval-only can use experimental retriever strategies
CarbonRag SHALL allow retrieval-only callers to request explicit experimental retriever strategies without changing default `/ask` behavior.

#### Scenario: BM25-only strategy is requested
- **WHEN** retrieval-only receives `retrieval_strategy=bm25_only`
- **THEN** CarbonRag searches the current BM25-backed retrieval path
- **AND** returns the existing `chunks`, `references`, and `metadata` fields

#### Scenario: Vector-only strategy is requested
- **WHEN** retrieval-only receives `retrieval_strategy=vector_only`
- **THEN** CarbonRag queries the configured vector adapter when available
- **AND** records vector backend health and hit count in metadata

#### Scenario: Hybrid strategy merges duplicate chunks
- **WHEN** retrieval-only receives `retrieval_strategy=bm25_vector_hybrid`
- **AND** the same `chunk_id` is returned by BM25 and vector retrieval
- **THEN** CarbonRag returns that chunk once
- **AND** records BM25 score, vector score, merged score, and source retrievers for that chunk

#### Scenario: Hybrid strategy degrades when vector is unavailable
- **WHEN** hybrid retrieval is requested and the vector adapter is unavailable
- **THEN** CarbonRag returns BM25 hits when BM25 has matches
- **AND** metadata records fallback status and fallback reason

#### Scenario: Default ask remains unchanged
- **WHEN** users call the normal ask/session flows without an experimental retrieval strategy
- **THEN** CarbonRag preserves the existing naive/mix behavior and BM25 fallback semantics
