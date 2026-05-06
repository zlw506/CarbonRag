## Purpose
Defines carbon calculation, report generation, report editing, and feedback persistence.

## Requirements

### Requirement: Carbon calculations are persisted per user
CarbonRag SHALL calculate supported activity emissions and persist results under the authenticated user.

#### Scenario: User submits valid activity data
- **WHEN** electricity, natural gas, or diesel activity data is submitted
- **THEN** the backend returns total emissions, breakdown, factor citations, and trace id

### Requirement: Reports are session linked
CarbonRag SHALL create, store, reopen, and edit reports under a session owned by the current user.

#### Scenario: User creates report from session evidence
- **WHEN** valid session sources are selected
- **THEN** a report is generated and stored with citations and source metadata
