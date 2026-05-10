## MODIFIED Requirements

### Requirement: RAG-Pro remains the main RAG migration spine

CarbonRag SHALL allow direct migration or rewriting of RAG-Pro core structure and logic during the RAG development phase while preserving CarbonRag governance and product boundaries.

#### Scenario: RAG-Pro logic is ported

- **WHEN** a contributor ports RAG-Pro knowledge base, document, chunk, vector, retrieval, rerank, or test-QA logic
- **THEN** they may rewrite it into CarbonRag-owned code but SHALL NOT commit ignored `3rdparty` source trees

#### Scenario: CarbonRag boundaries are affected

- **WHEN** RAG-Pro migration touches auth, session, AskPage, report, OpenSpec, GitNexus, or Mattermost workflows
- **THEN** the contributor preserves CarbonRag's existing boundaries unless #1 explicitly approves a change
