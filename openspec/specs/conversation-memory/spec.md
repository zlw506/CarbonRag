## Purpose
Defines authenticated user sessions, ask and ask stream behavior, title generation, session memory state, and context compaction.

## Requirements

### Requirement: Sessions isolate user conversation state
CarbonRag SHALL store sessions, messages, ask results, and memory state under the authenticated user owner.

#### Scenario: User reads session list
- **WHEN** a user requests sessions
- **THEN** only sessions owned by that user are returned

### Requirement: Ask context uses session memory
CarbonRag SHALL assemble ask context from session summary, recent messages, grounding results, and the current question.

#### Scenario: Long session continues after compaction
- **WHEN** a session exceeds the estimated context budget
- **THEN** older conversation content is represented by a session summary while recent turns remain available
