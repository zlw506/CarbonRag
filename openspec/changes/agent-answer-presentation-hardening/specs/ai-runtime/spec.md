## MODIFIED Requirements

### Requirement: Provider runtime supports configured model access

CarbonRag SHALL route model calls through provider abstractions and user/provider configuration rather than page-level direct API access.

#### Scenario: Ask uses active provider

- **WHEN** an authenticated user sends an ask request
- **THEN** the runtime resolves the active provider before calling the model

#### Scenario: Ask response style is constrained

- **WHEN** Ask mode builds the model system prompt
- **THEN** the prompt instructs the model not to use Markdown `#` headings
- **AND** complex answers are requested with a conclusion-first, evidence-backed, prioritized structure
