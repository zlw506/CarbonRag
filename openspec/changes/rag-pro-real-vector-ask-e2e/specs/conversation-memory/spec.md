## MODIFIED Requirements

### Requirement: Ask carries selected RAG context

Ask requests SHALL support an optional RAG knowledge base and retrieval mode without breaking existing session memory behavior.

#### Scenario: User selects KB before asking

- **WHEN** AskPage sends `kb_id` and `rag_mode`
- **THEN** the runtime payload preserves those fields for RAG tool execution and response metadata.
