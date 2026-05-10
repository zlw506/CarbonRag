## ADDED Requirements

### Requirement: Live policy crawler is testable against official allowlist sources
CarbonRag SHALL support a real Scrapy-backed manual crawl path for approved official policy domains.

#### Scenario: Approved official domains are enforced
- **WHEN** policy live crawler sources are seeded or requested
- **THEN** the accepted allowlist is `gov.cn`, `ndrc.gov.cn`, `mee.gov.cn`, `miit.gov.cn`, `fgw.beijing.gov.cn`, and `beijing.gov.cn`
- **AND** non-allowlisted URLs are rejected before network access

#### Scenario: Manual crawl uses real Scrapy when available
- **WHEN** the backend Python environment can import Scrapy and an admin manually runs a source
- **THEN** CarbonRag runs the Scrapy provider with safe limits
- **AND** records run status, errors, document count, and candidate count
- **AND** resulting documents enter `pending_review` candidates only

#### Scenario: Scrapy unavailable is explicit
- **WHEN** the backend Python environment cannot import Scrapy
- **THEN** the crawler status and run error clearly identify Scrapy as unavailable
- **AND** startup, `/ask`, RAG Lab, calc, report, and session flows continue to work
