## MODIFIED Requirements

### Requirement: RAG Lab displays optional graph candidate metadata
CarbonRag SHALL display graph candidate metadata in RAG Lab when retrieval-only responses include it.

#### Scenario: Graph metadata is present
- **WHEN** retrieval-only metadata includes graph entities, relations, or candidates
- **THEN** RAG Lab displays them as experimental graph metadata

#### Scenario: Graph metadata is missing
- **WHEN** retrieval-only metadata omits graph fields or returns empty graph fields
- **THEN** RAG Lab remains stable and does not crash
