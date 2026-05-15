## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL only publish crawler candidates into the RAG-Pro KB when the candidate has a non-empty extracted正文 artifact and a successful quick-pipeline index.

#### Scenario: gov.cn policy page produces reliable artifacts

- **WHEN** an admin crawler processes a gov.cn policy detail page
- **THEN** CarbonRag writes raw, cleaned text, markdown, and extraction diagnostics artifacts
- **AND** the cleaned text and markdown contain the policy title, document number, publication date, and正文.

#### Scenario: Empty extraction is blocked from RAG publish

- **WHEN** a crawler candidate has missing or too-short markdown/cleaned artifacts
- **AND** an admin calls publish-to-RAG
- **THEN** CarbonRag rejects the request with an explicit extraction failure reason
- **AND** the candidate is not marked as published.

#### Scenario: Admin can inspect crawler artifacts

- **WHEN** an admin opens a crawler candidate preview
- **THEN** CarbonRag exposes artifact existence, sizes, markdown preview, cleaned text preview, raw excerpt, estimated chunks, and extraction errors.
