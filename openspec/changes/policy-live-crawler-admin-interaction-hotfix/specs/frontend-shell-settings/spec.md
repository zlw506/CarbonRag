## ADDED Requirements

### Requirement: Admin UI exposes usable live policy crawler controls
CarbonRag SHALL make the live policy crawler operational from the Admin page for administrators.

#### Scenario: Admin sees official crawler sources
- **WHEN** an admin opens the Admin page
- **THEN** the page shows the approved official sources and allowlist domains
- **AND** each enabled source has a manual crawl action

#### Scenario: Admin runs a source
- **WHEN** an admin clicks run on an official source
- **THEN** the UI calls the crawler run API
- **AND** refreshes crawler status, source state, recent runs, and candidates
- **AND** displays success, failure, unavailable, zero-match, auto-published, and indexed states clearly

#### Scenario: Admin sees auto-ingested policy records
- **WHEN** crawl candidates exist
- **THEN** the Admin page shows concrete policy title, URL, source, summary, content length, matched keywords, and indexing result
- **AND** the UI explains that official double-carbon policy/standard matches auto-update `public_policy_web`
- **AND** the page does not require a separate review action before indexing
