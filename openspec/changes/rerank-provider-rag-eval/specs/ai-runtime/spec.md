## MODIFIED Requirements

### Requirement: Reranking is an optional AI runtime responsibility
CarbonRag SHALL treat reranking as an optional provider-backed runtime capability used after initial retrieval.

#### Scenario: No-op reranker is default
- **WHEN** no rerank model is configured
- **THEN** CarbonRag uses a no-op rerank provider that preserves candidate order
- **AND** reports metadata explaining that no model rerank was applied

#### Scenario: Fake reranker is used in tests or local evaluation
- **WHEN** tests or local evaluation need deterministic reranking
- **THEN** CarbonRag can use a fake rerank provider without requiring network access or a large model

#### Scenario: Ask defaults remain unchanged
- **WHEN** users call normal ask/session flows without enabling rerank
- **THEN** CarbonRag preserves the existing default behavior
