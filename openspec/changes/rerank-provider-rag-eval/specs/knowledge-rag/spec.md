## MODIFIED Requirements

### Requirement: Retrieval evaluation has a fixed baseline dataset
CarbonRag SHALL provide a fixed retrieval evaluation dataset for comparing BM25, vector, hybrid, and hybrid+rerank retrieval.

#### Scenario: Evaluation dataset is present
- **WHEN** developers run the RAG eval script
- **THEN** the dataset includes at least 10 public-policy cases and 5 private-sample cases
- **AND** each case contains expected document ids or expected keywords

#### Scenario: Evaluation emits retrieval metrics
- **WHEN** the RAG eval script completes
- **THEN** it reports total cases, hit-at-1, hit-at-3, hit-at-5, citation count, zero-hit count, fallback count, and average latency

#### Scenario: Empty evaluation dataset is handled clearly
- **WHEN** the RAG eval script receives an empty dataset
- **THEN** it returns a clear empty-dataset result instead of failing with an unclear exception
