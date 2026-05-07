## ADDED Requirements

### Requirement: Calc-carbon accepts factor-driven activity items
CarbonRag SHALL accept `activity_items[]` as the V2 calc-carbon input while preserving the legacy three-field payload.

#### Scenario: V2 activity items are submitted
- **WHEN** a user submits Scope 1 or Scope 2 activity items
- **THEN** CarbonRag calculates emissions through the factor-driven engine and returns total emissions, breakdown, citations, snapshots, traces, and warnings

#### Scenario: Legacy payload is submitted
- **WHEN** a user submits `electricity_kwh`, `natural_gas_m3`, or `diesel_l`
- **THEN** CarbonRag converts the payload into equivalent activity items and keeps the endpoint response compatible

### Requirement: Carbon calculations persist factor snapshots
CarbonRag SHALL persist the full factor snapshot, unit conversion trace, formula trace, source summary, and warnings for each calculation.

#### Scenario: Calculation is reopened for report generation
- **WHEN** a report reads a stored carbon calculation
- **THEN** the stored result contains the factor values and source metadata used at calculation time

### Requirement: Scope 2 electricity uses official location-based factors first
CarbonRag SHALL prioritize official MEE/NBS electricity factors for purchased electricity location-based calculations.

#### Scenario: CN 2023 electricity is calculated
- **WHEN** a user submits purchased electricity with region `CN` and year `2023`
- **THEN** CarbonRag uses the official national electricity factor `0.5306 kgCO2/kWh`

### Requirement: Demo combustion factors are clearly marked
CarbonRag SHALL mark unverified combustion seed factors as demo and warn that they are not formal audit factors.

#### Scenario: Demo natural gas or diesel factor is used
- **WHEN** no official curated combustion factor is available
- **THEN** CarbonRag may calculate using a demo factor but returns a warning and preserves `source_type=demo`

### Requirement: Market-based green power is reserved
CarbonRag SHALL NOT silently zero certified green power in V1.4.4.

#### Scenario: Market-based electricity fields are supplied
- **WHEN** a user supplies market-based or certified green electricity fields
- **THEN** CarbonRag uses location-based calculation and returns a warning that market-based calculation is reserved
