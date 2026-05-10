## MODIFIED Requirements

### Requirement: Ask runtime uses the unified RAG spine

AI runtime RAG tools SHALL call the unified `backend/app/rag` spine instead of silently falling back to legacy RAG.

#### Scenario: Ask requests RAG evidence

- **WHEN** Ask uses RAG retrieval
- **THEN** the tool result includes retrieval trace and any degradation warnings from the unified spine.

