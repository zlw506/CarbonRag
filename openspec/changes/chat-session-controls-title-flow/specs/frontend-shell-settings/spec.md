## MODIFIED Requirements

### Requirement: Session rail exposes basic conversation controls

The frontend shell SHALL expose basic session controls from the session rail without opening a separate settings page.

#### Scenario: User opens a session menu

- **WHEN** a user clicks the session row overflow menu
- **THEN** the menu offers rename, pin or unpin, and delete actions

#### Scenario: Session title updates during streaming start

- **WHEN** the stream start event reports that the session title changed
- **THEN** the session rail refreshes promptly so the new title appears before the answer finishes
