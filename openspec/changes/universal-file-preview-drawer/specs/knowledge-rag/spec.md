## ADDED Requirements

### Requirement: Universal File Preview

CarbonRag SHALL provide a unified file preview API for session uploads, RAG-Pro KB documents, crawler candidates, and legacy knowledge items.

#### Scenario: Preview a RAG document by logical ID

- **WHEN** an authenticated user requests `GET /api/v1/file-previews/rag_document/{doc_id}?kb_id={kb_id}`
- **THEN** the API returns parsed markdown/text, chunks, metadata, and raw preview availability for a document visible in that KB
- **AND** the response does not expose a server filesystem path as a required client input.

#### Scenario: Preview a crawler candidate as admin

- **WHEN** an admin requests `GET /api/v1/file-previews/crawler_candidate/{candidate_id}`
- **THEN** the API returns raw/cleaned/markdown artifact preview data and crawler metadata
- **AND** a non-admin user receives a forbidden response.

#### Scenario: Raw file access is bounded

- **WHEN** a user requests `/raw`
- **THEN** the server resolves the file from a registered logical source and rejects missing or out-of-bound paths.
