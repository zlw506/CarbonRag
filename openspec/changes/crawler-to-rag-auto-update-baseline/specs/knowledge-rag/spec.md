## MODIFIED Requirements

### Requirement: Knowledge/RAG exposes a product-grade knowledge base spine

CarbonRag SHALL expose a KnowledgeBase -> Document -> Chunk -> Retrieval -> Answer spine as the primary RAG path.

#### Scenario: Reviewed crawler candidate publishes to RAG-Pro KB

- **WHEN** an admin reviews a pending official policy crawler candidate
- **AND** calls the publish-to-RAG action
- **THEN** CarbonRag creates or reuses the shared official policy RAG KB
- **AND** creates a `public_policy` RagDocument from the candidate markdown/text artifact
- **AND** runs the quick pipeline
- **AND** records `rag_kb_id`, `rag_doc_id`, pipeline status, indexed chunk count, search smoke result, vector runtime, and errors in candidate metadata

#### Scenario: Legacy crawler publish is not the V1.7 acceptance path

- **WHEN** an admin opens crawler candidate actions
- **THEN** the legacy knowledge publish action remains available as a secondary compatibility path
- **AND** the V1.7 acceptance path is the publish-to-RAG action

#### Scenario: Crawler defaults are manually controlled

- **WHEN** CarbonRag starts with default settings
- **THEN** manual crawler trigger is enabled
- **AND** scheduled crawler runs are disabled
- **AND** crawler auto publish is disabled
