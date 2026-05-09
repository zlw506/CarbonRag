## MODIFIED Requirements

### Requirement: Uploads enter the knowledge task flow
CarbonRag SHALL create knowledge items and ingest tasks for supported user uploads.

#### Scenario: User uploads a supported file
- **WHEN** upload succeeds for an allowed file type
- **THEN** a personal knowledge item and ingest task are created
- **AND** the file is stored under a generated server filename
- **AND** file parse metadata is recorded separately from the original display filename

#### Scenario: Uploaded file is parsed
- **WHEN** the upload ingest task processes a supported file
- **THEN** CarbonRag persists extracted text or markdown, parser metadata, summary, chunk count, and file locator metadata
- **AND** generated chunks remain compatible with existing `knowledge_chunks` retrieval

#### Scenario: Uploaded file cannot be parsed
- **WHEN** Docling and fallback parsers cannot extract readable content
- **THEN** the file parse status becomes failed with an explicit error
- **AND** the file is not used as ask evidence

### Requirement: Private upload citations carry file locator metadata
CarbonRag SHALL preserve upload file locator metadata from chunking through retrieval, runtime formatting, API responses, and frontend citation display.

#### Scenario: Upload chunk is cited
- **WHEN** ask returns a `private_upload` citation
- **THEN** the citation may include `file_id`, `page_number`, `sheet_name`, `slide_number`, and `section_title`
