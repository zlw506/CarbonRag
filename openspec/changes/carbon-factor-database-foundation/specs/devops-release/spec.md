## ADDED Requirements

### Requirement: Carbon factor database works in local and cloud runtime modes
CarbonRag SHALL initialize and validate the carbon factor database schema in both SQLite local-dev and PostgreSQL cloud-stable runtime modes.

#### Scenario: Local development starts
- **WHEN** the backend starts without `DATABASE_URL`
- **THEN** SQLite runtime initialization includes carbon factor source, record, alias, and import job tables

#### Scenario: Cloud runtime starts
- **WHEN** the backend starts with PostgreSQL runtime configuration
- **THEN** PostgreSQL runtime initialization includes equivalent carbon factor tables and indexes

### Requirement: Factor seed and import workflows are reproducible
CarbonRag SHALL document and test carbon factor seed/import workflows so cloud and local environments do not diverge silently.

#### Scenario: Release verification runs
- **WHEN** release verification is executed
- **THEN** it validates factor DB schema bootstrap, seed import idempotency, search API behavior, and calc integration in the configured runtime mode
