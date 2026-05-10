## MODIFIED Requirements

### Requirement: DevOps documents RAG vector runtime profiles

CarbonRag SHALL provide reproducible local runtime profiles for Windows Docker Milvus, WSL/Linux/macOS Milvus Lite, and development-only memory fallback.

#### Scenario: Windows developer starts the RAG vector runtime

- **WHEN** a Windows developer follows the RAG runtime runbook
- **THEN** they can start Docker Milvus Standalone, smoke-test port `19530`, and avoid native Windows `milvus-lite` installation

#### Scenario: Docker disk space is constrained

- **WHEN** Docker image or volume storage would fill the system drive
- **THEN** the runbook warns the developer to move Docker Desktop/WSL storage to a larger disk before pulling Milvus images
