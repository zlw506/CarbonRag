## MODIFIED Requirements

### Requirement: Carbon calculations are persisted per user
CarbonRag SHALL calculate supported activity emissions and persist results under the authenticated user.

#### Scenario: User submits valid activity data
- **WHEN** electricity, natural gas, or diesel activity data is submitted
- **THEN** the backend returns total emissions, breakdown, factor citations, trace id, inventory id, scope summary, activity count, official factor count, fallback factor count, and warnings

#### Scenario: V2 activity data is submitted
- **WHEN** a user submits `activity_items[]`
- **THEN** CarbonRag persists the inventory metadata, raw request payload, raw activity item payloads, activity evidence fields, calculation lines, factor snapshots, and inventory summary under the authenticated user

#### Scenario: Legacy payload includes zero values
- **WHEN** a legacy three-field payload has one or more zero fields
- **THEN** CarbonRag SHALL NOT create activity items or fallback warnings for zero-valued fields

### Requirement: Carbon calculations persist factor snapshots
CarbonRag SHALL persist the full factor snapshot, unit conversion trace, formula trace, source summary, and warnings for each calculation.

#### Scenario: Calculation is reopened for report generation
- **WHEN** a report reads a stored carbon calculation
- **THEN** the stored result contains the factor values and source metadata used at calculation time

#### Scenario: Factor source is not exact official match
- **WHEN** the registry uses a guidance or demo fallback factor
- **THEN** CarbonRag returns a warning and persists the fallback source type in the factor snapshot

### Requirement: Scope 2 electricity uses official location-based factors first
CarbonRag SHALL prioritize official MEE/NBS electricity factors for purchased electricity location-based calculations.

#### Scenario: CN 2023 electricity is calculated
- **WHEN** a user submits purchased electricity with region `CN` and year `2023`
- **THEN** CarbonRag uses the official national electricity factor `0.5306 kgCO2/kWh`

#### Scenario: Grid-region electricity is calculated
- **WHEN** a user submits purchased electricity with a supported grid-region code and year `2023`
- **THEN** CarbonRag uses the matching official grid-region factor before national fallback

#### Scenario: Province electricity is calculated
- **WHEN** a user submits purchased electricity with a supported province code and year `2023`
- **THEN** CarbonRag uses the matching official province factor before grid-region or national fallback

### Requirement: Combustion guidance factors are clearly marked
CarbonRag SHALL mark public-guidance fuel seed factors as `guidance_default` and warn that they are not formal enterprise audit factors.

#### Scenario: Guidance natural gas or diesel factor is used
- **WHEN** no curated enterprise official combustion factor is available
- **THEN** CarbonRag may calculate using a `guidance_default` factor but returns a warning and preserves `source_type=guidance_default`
