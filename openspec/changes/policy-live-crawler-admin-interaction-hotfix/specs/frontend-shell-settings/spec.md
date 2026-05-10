## ADDED Requirements

### Requirement: Admin UI exposes usable live policy crawler controls
CarbonRag SHALL make the live policy crawler operational from the Admin page for administrators.

#### Scenario: Admin sees official crawler sources
- **WHEN** an admin opens the Admin page
- **THEN** the page shows the approved official sources and allowlist domains
- **AND** each enabled source has a manual crawl action

#### Scenario: Admin runs a source
- **WHEN** an admin clicks manual crawl on an official source
- **THEN** the UI calls the crawler run API
- **AND** refreshes crawler status, source state, recent runs, and candidates
- **AND** displays success, failure, unavailable, and zero-candidate states clearly

#### Scenario: Admin reviews crawled candidates
- **WHEN** crawl candidates exist
- **THEN** pending candidates can be published or rejected from the Admin page
- **AND** candidates do not enter retrieval until published
