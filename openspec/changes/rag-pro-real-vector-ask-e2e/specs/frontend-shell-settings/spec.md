## MODIFIED Requirements

### Requirement: AskPage exposes RAG selection state

AskPage SHALL allow the user to choose a knowledge base and retrieval mode for the next question.

#### Scenario: User asks with selected RAG settings

- **WHEN** a user selects a knowledge base and retrieval mode
- **THEN** AskPage sends those fields with the ask request and displays returned RAG trace tags.
