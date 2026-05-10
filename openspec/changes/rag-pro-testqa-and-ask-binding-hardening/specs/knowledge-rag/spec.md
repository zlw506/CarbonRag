## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose a KnowledgeBase -> Document -> Chunk -> Retrieval -> Answer spine as the primary RAG path.

#### Scenario: AskPage uses the selected knowledge base

- **WHEN** a user asks from AskPage with `kb_id` and `rag_mode`
- **THEN** the session endpoint passes both values into `ChatRequest.payload`
- **AND** the AI Runtime RAG tool arguments include the same selected knowledge base and retrieval mode
- **AND** the retrieval trace records the selected `kb_id`

#### Scenario: Knowledge base isolation is required

- **WHEN** two private knowledge bases contain different documents
- **AND** the user selects one knowledge base for Ask or Test QA
- **THEN** RAG retrieval returns citations only from the selected knowledge base

### Requirement: RAG Test QA distinguishes retrieval from grounded generation

KnowledgeBaseWorkbench Test QA SHALL distinguish retrieval-only diagnostics from generated grounded answers.

#### Scenario: Test QA has retrieved evidence

- **WHEN** `/api/v1/rag/test-qa` retrieves relevant chunks
- **THEN** CarbonRag builds a grounded prompt from those chunks
- **AND** calls the configured chat provider
- **AND** returns `answer_mode=llm_grounded`, provider metadata, selected chunks, citations, evidence quality, confidence, and retrieval trace

#### Scenario: Test QA has no evidence

- **WHEN** `/api/v1/rag/test-qa` retrieves no chunks
- **THEN** CarbonRag returns `answer_mode=no_hits`
- **AND** does not call the chat provider
- **AND** marks the result as not grounded instead of generating an unsupported answer

#### Scenario: Test QA provider fails

- **WHEN** retrieval succeeds but the chat provider is unavailable
- **THEN** CarbonRag returns provider error details with the retrieval trace
- **AND** does not present snippet stitching as a successful LLM answer

### Requirement: Legacy RAG Lab is not the acceptance path

CarbonRag SHALL keep legacy RAG experiments separate from the RAG-Pro acceptance path.

#### Scenario: User navigation is rendered

- **WHEN** a non-admin user opens the application navigation
- **THEN** the legacy RAG Lab entry is not shown
- **AND** the formal RAG entry remains KnowledgeBaseWorkbench and AskPage
