## Purpose
Defines personal and shared knowledge libraries, file ingestion, knowledge tasks, private retrieval, and mixed retrieval.

## Requirements

### Requirement: Private knowledge is indexed before retrieval
CarbonRag SHALL retrieve private and mixed scope evidence from indexed knowledge chunks attached to the current session.

#### Scenario: Private ask searches attached knowledge
- **WHEN** a user asks with private_sample scope
- **THEN** only attached, enabled, indexed knowledge items are searched

### Requirement: Uploads enter the knowledge task flow
CarbonRag SHALL create knowledge items and ingest tasks for supported user uploads.

#### Scenario: User uploads a file
- **WHEN** upload succeeds
- **THEN** a personal knowledge item and ingest task are created
