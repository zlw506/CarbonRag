## ADDED Requirements

### Requirement: Carbon calculations can be created from parsed report evidence
CarbonRag SHALL convert supported carbon activity quantities extracted from selected parsed reports into structured activity items and calculate emissions through the existing factor-driven carbon engine.

#### Scenario: Report contains supported activity quantities
- **WHEN** selected report chunks contain supported activity quantities such as purchased electricity, natural gas, diesel, gasoline, LPG, or coal
- **THEN** CarbonRag creates corresponding activity items with file evidence metadata
- **AND** calculates emissions using the existing carbon factor registry
- **AND** returns factor snapshots, formula traces, source summary, and warnings

