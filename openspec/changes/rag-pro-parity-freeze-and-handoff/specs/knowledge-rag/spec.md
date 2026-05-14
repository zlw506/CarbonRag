## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose a KnowledgeBase -> Document -> Chunk -> Retrieval -> Answer spine as the primary RAG path.

#### Scenario: RAG-Pro baseline status is frozen

- **WHEN** a teammate reads the project entry documents
- **THEN** CarbonRag states V1.6.33 as the RAG-Pro parity freeze baseline
- **AND** distinguishes the official acceptance path from legacy RAG paths

#### Scenario: Workbench quick and acceptance actions are unambiguous

- **WHEN** a user opens KnowledgeBaseWorkbench
- **THEN** the default quick action is named `快速建立 RAG`
- **AND** it runs parse, chunk, index, and search smoke only
- **AND** the full acceptance action is named `完整验收 RAG`
- **AND** it is the explicit path for eval and optional generation checks

#### Scenario: Warm Milvus search reuses runtime resources

- **WHEN** two searches run against the same Milvus URI
- **THEN** the vector-store adapter is reused for the same backend/runtime URI
- **AND** the second search reports `milvus_client_init_count=0`

#### Scenario: Workbench and AskPage use the same selected KB

- **WHEN** Workbench search, Workbench Test QA, and AskPage answer run the Qingmu acceptance question against the same KB
- **THEN** all three paths use the same `kb_id`
- **AND** all three can cite the same KB evidence containing `217,650 kWh`

#### Scenario: Ownership handoff is explicit

- **WHEN** V1.6.33 is complete
- **THEN** #1 retains ownership of Milvus runtime, BGE embedding, reranker, eval, AskPage KB binding, and isolation
- **AND** #3 can take over visual polish, progress states, citation card display, empty states, and onboarding copy
