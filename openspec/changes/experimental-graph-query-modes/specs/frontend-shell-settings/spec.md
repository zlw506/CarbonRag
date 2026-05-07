## MODIFIED Requirements

### Requirement: RAG Lab exposes experimental graph query mode selection
CarbonRag SHALL let RAG Lab users select experimental graph modes and inspect graph fallback metadata.

#### Scenario: Graph mode selector is visible
- **WHEN** a user opens RAG Lab
- **THEN** the page offers `off`, `graph_local`, `graph_global`, and `graph_hybrid`
- **AND** it labels graph retrieval as experimental and not affecting default `/ask`

#### Scenario: Graph fallback reason is present
- **WHEN** retrieval metadata includes `graph_fallback_reason`
- **THEN** RAG Lab displays the fallback reason without crashing when graph fields are empty
