## MODIFIED Requirements

### Requirement: Protected workbench routes require authentication

CarbonRag SHALL prevent unauthenticated access to workbench pages.

#### Scenario: Anonymous user opens protected page

- **WHEN** no valid auth cookie exists
- **THEN** the frontend routes the user to the login flow

#### Scenario: AskPage renders assistant answers with compact structure

- **WHEN** an assistant answer contains Markdown heading markers
- **THEN** AskPage renders them as compact section labels without visible `#` markers
- **AND** heading typography remains close enough to body text to avoid disruptive visual jumps

#### Scenario: AskPage renders answer tables

- **WHEN** an assistant answer contains Markdown table syntax
- **THEN** AskPage renders it as a readable table
- **AND** table cells remain legible in both light and dark themes
