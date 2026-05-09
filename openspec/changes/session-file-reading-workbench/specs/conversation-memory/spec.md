## MODIFIED Requirements

### Requirement: Ask can use selected parsed session uploads
CarbonRag SHALL allow ask requests to search selected parsed uploads attached to the current session without changing the request field name `attached_file_ids`.

#### Scenario: User asks with a parsed uploaded file
- **WHEN** an authenticated user asks in a session with `attached_file_ids` containing a file owned by that user and indexed in the current session
- **THEN** the ask runtime searches the file chunks through `session_file_search`
- **AND** the final answer may cite `private_upload` evidence with file locator metadata

#### Scenario: File is not ready
- **WHEN** an uploaded file is not parsed and indexed
- **THEN** it is not injected into ask context
- **AND** the user may still ask against other available evidence

#### Scenario: File belongs to another user
- **WHEN** `attached_file_ids` references a file outside the authenticated user's session ownership
- **THEN** CarbonRag treats it as unavailable and does not expose file existence
