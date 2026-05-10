## ADDED Requirements

### Requirement: Live policy crawler is testable against official allowlist sources
CarbonRag SHALL support a real Scrapy-backed manual crawl path for approved official policy domains.

#### Scenario: Approved official domains are enforced
- **WHEN** policy live crawler sources are seeded or requested
- **THEN** the accepted allowlist is `gov.cn`, `ndrc.gov.cn`, `mee.gov.cn`, `miit.gov.cn`, `fgw.beijing.gov.cn`, and `beijing.gov.cn`
- **AND** non-allowlisted URLs are rejected before network access

#### Scenario: Official crawl auto-updates the knowledge base
- **WHEN** the backend Python environment can import Scrapy and a source runs manually or by schedule
- **THEN** CarbonRag runs the Scrapy provider with safe limits
- **AND** records run status, errors, document count, candidate count, auto-published count, indexed count, and skipped topic count
- **AND** resulting documents that match double-carbon policy or technical-standard topics are auto-published to `public_policy_web`
- **AND** each published candidate immediately enters `crawl_ingest` / `policy_ingest` indexing
- **AND** candidate rows remain available as audit records with source URL, title, summary, matched keywords, and indexing status

#### Scenario: Scrapy unavailable is explicit
- **WHEN** the backend Python environment cannot import Scrapy
- **THEN** the crawler status and run error clearly identify Scrapy as unavailable
- **AND** startup, `/ask`, RAG Lab, calc, report, and session flows continue to work
