## ADDED Requirements

### Requirement: PR version scope matches delivered change scope
CarbonRag SHALL label PR titles, PR bodies, and development logs with a version scope that matches the delivered change-id set and behavioral surface.

#### Scenario: PR contains multiple V1.3.X RAG changes
- **WHEN** a PR bundles multiple V1.3.X RAG OpenSpec changes and implementation areas
- **THEN** the title, body, and development log identify it as the V1.3.X RAG initial baseline
- **AND** they list the concrete change ids and boundaries instead of naming the PR as a narrow patch release
