## MODIFIED Requirements

### Requirement: Sessions support early automatic titles and user controls

CarbonRag SHALL generate an initial session title after the first user message is saved and before the assistant response is completed. CarbonRag SHALL refine the title after the second user message is saved, then stop automatic title intervention for that session. Users SHALL be able to rename, pin, unpin, and delete their own sessions.

#### Scenario: First user message starts a title

- **WHEN** a user sends the first message in a new session
- **THEN** CarbonRag creates a short provisional title before the assistant answer completes

#### Scenario: Second user message refines a title

- **WHEN** a user sends the second message in a session
- **THEN** CarbonRag may refine the title using the first valid exchange and the second user message

#### Scenario: Later messages do not auto-rename

- **WHEN** a user sends the third or later message
- **THEN** CarbonRag does not automatically change the session title

#### Scenario: User controls own session

- **WHEN** a user requests rename, pin, unpin, or delete for a session they own
- **THEN** CarbonRag applies the change only to that user's session
