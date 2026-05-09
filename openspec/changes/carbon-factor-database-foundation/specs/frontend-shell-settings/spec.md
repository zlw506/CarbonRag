## ADDED Requirements

### Requirement: Workbench exposes a carbon factor database page
CarbonRag SHALL provide a user-facing carbon factor database page for searching, filtering, and inspecting maintained factor records.

#### Scenario: User opens carbon factor database
- **WHEN** an authenticated user opens the factor database page
- **THEN** the page shows a search-first interface, category filters, hot keywords, factor result cards, and a detail drawer

#### Scenario: User reviews factor source
- **WHEN** a user opens a factor result detail
- **THEN** the UI shows the factor value, unit, region, year, source, quality label, version, and citation metadata before advanced maintenance fields

### Requirement: Carbon factor maintenance is separated from normal browsing
CarbonRag SHALL keep factor import and enable/disable controls admin-only and visually separate from normal factor browsing.

#### Scenario: Normal user browses factors
- **WHEN** a normal user opens the factor database page
- **THEN** the user can search and inspect enabled factors but cannot access import or maintenance controls

#### Scenario: Admin opens factor database page
- **WHEN** an administrator opens the factor database page
- **THEN** the UI may show an admin maintenance entry for import jobs and factor enable/disable actions
