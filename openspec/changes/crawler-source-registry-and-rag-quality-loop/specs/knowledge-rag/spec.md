## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose the crawler-to-RAG update path as a reviewed, auditable source registry rather than an uncontrolled auto-publish crawler.

#### Scenario: Admin imports recommended dual-carbon official sources

- **WHEN** an admin imports recommended crawler sources
- **THEN** CarbonRag stores at least twelve official source definitions
- **AND** no more than five are enabled by default
- **AND** each source carries category, region, parser profile, priority, and review metadata.

#### Scenario: Source dry-run previews candidates without publishing

- **WHEN** an admin dry-runs a crawler source
- **THEN** CarbonRag returns candidate previews, matched keywords, quality scores, skip reasons, markdown preview, and target RAG KB
- **AND** it does not create candidate DB rows
- **AND** it does not publish anything to RAG.

#### Scenario: Low-quality crawler candidate is blocked from RAG publish

- **WHEN** a crawler candidate has `candidate_quality_score` below 60
- **AND** an admin calls publish-to-RAG
- **THEN** CarbonRag rejects the publish request with an explicit reason.
