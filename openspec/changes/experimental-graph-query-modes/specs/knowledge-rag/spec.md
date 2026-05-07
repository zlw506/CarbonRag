## MODIFIED Requirements

### Requirement: Graph query modes are experimental retrieval-only capabilities
CarbonRag SHALL support experimental graph query modes without changing default ask behavior.

#### Scenario: Graph local mode returns entity candidates
- **WHEN** retrieval-only requests `graph_mode=graph_local`
- **THEN** CarbonRag returns graph candidates related to query-matched entities

#### Scenario: Graph global mode returns relation candidates
- **WHEN** retrieval-only requests `graph_mode=graph_global`
- **THEN** CarbonRag returns graph candidates related to relations or community-style summaries

#### Scenario: Graph hybrid mode deduplicates candidates
- **WHEN** retrieval-only requests `graph_mode=graph_hybrid`
- **THEN** CarbonRag combines local, global, and retrieved chunk candidates without duplicate candidate ids

#### Scenario: Graph unavailable falls back
- **WHEN** graph mode is requested but graph storage or extraction is unavailable
- **THEN** CarbonRag preserves existing retrieval results
- **AND** metadata records `graph_fallback_reason`

#### Scenario: Default ask remains unchanged
- **WHEN** normal ask/session flows run
- **THEN** graph query modes are not enabled by default
