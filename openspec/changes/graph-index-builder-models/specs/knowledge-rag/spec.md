## MODIFIED Requirements

### Requirement: Graph index metadata is experimental and disabled from default ask
CarbonRag SHALL provide graph index models and graph candidate metadata as an experimental retrieval-only capability without changing default ask behavior.

#### Scenario: Graph models can be created
- **WHEN** graph entities, relations, and community summaries are constructed from chunk evidence
- **THEN** they include source chunk ids, confidence, and metadata fields

#### Scenario: Graph builder handles empty input
- **WHEN** graph index build receives no chunks
- **THEN** it returns a successful empty result without raising

#### Scenario: Graph candidates map back to chunks
- **WHEN** graph index build extracts entities or relations from a chunk
- **THEN** graph candidates can be looked up by that chunk id

#### Scenario: Default ask is unchanged
- **WHEN** normal ask/session flows run
- **THEN** graph metadata does not alter default retrieval, answer generation, calc, report, or session behavior
