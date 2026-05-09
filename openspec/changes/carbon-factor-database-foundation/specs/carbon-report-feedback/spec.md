## ADDED Requirements

### Requirement: Carbon factors are queryable from a maintained runtime database
CarbonRag SHALL provide a maintained carbon factor database backed by runtime storage in both SQLite and PostgreSQL modes.

#### Scenario: User searches carbon factors
- **WHEN** an authenticated user searches by keyword, category, industry, region, year, source type, quality, or unit
- **THEN** CarbonRag returns matching enabled factors with values, units, source summaries, quality labels, pagination metadata, and factor ids

#### Scenario: User opens factor detail
- **WHEN** an authenticated user opens a factor id
- **THEN** CarbonRag returns the full factor record, aliases, source metadata, applicability fields, units, quality, version, and citation information

### Requirement: Carbon factor imports are source governed
CarbonRag SHALL import carbon factors only with explicit source, publisher, status, and license or rights metadata.

#### Scenario: CarbonStop public CCDB data is imported
- **WHEN** CarbonRag imports the public CarbonStop CCDB factor rows visible through the normal website page/gateway
- **THEN** CarbonRag writes factors with values, units, category, year, institution, original source, CarbonStop CCDB attribution, and raw row snapshots

#### Scenario: Admin imports a factor file
- **WHEN** an administrator submits a JSON or CSV factor import
- **THEN** CarbonRag creates an import job, validates required source metadata, writes accepted factors, rejects invalid rows, and records a summary

#### Scenario: Non-public factor data is requested as a seed
- **WHEN** a data source is login-only, paid, private, rate-limited beyond normal public use, or lacks source metadata
- **THEN** CarbonRag does not import it as seed data and records the source as blocked or pending authorization

### Requirement: Carbon calculations resolve runtime database factors first
CarbonRag SHALL resolve enabled runtime database factors before falling back to curated seed files or demo factors.

#### Scenario: Runtime factor matches activity item
- **WHEN** a calculation activity item matches an enabled runtime factor by explicit factor id or normalized activity fields
- **THEN** CarbonRag uses the runtime factor and persists a snapshot containing factor id, value, units, source, quality, and version

#### Scenario: No runtime factor matches
- **WHEN** no enabled runtime factor matches the activity item
- **THEN** CarbonRag falls back to the existing seed registry or demo fallback and preserves the existing warning behavior

### Requirement: Factor database preserves public CCDB attribution
CarbonRag SHALL use CarbonStop CCDB public fields as a benchmark source only with explicit attribution and raw-source traceability.

#### Scenario: A CarbonStop public row is shown in CarbonRag
- **WHEN** a user opens a factor imported from CarbonStop CCDB public data
- **THEN** the response shows CarbonStop CCDB attribution, original institution/source fields, year, unit, value, and a metadata snapshot for traceability
