# RAG-Pro Adoption Authorization

## Decision

CarbonRag V1.6.x RAG development uses `RAG-Pro` as the primary implementation spine.

`RAG-Pro` is a #2 / tbx2835066135 team member project and has been authorized for CarbonRag internal development use. During the RAG hardening phase, CarbonRag may directly migrate or rewrite RAG-Pro core structures and logic, including knowledge base models, document lifecycle, chunking strategy, Milvus/BGE/Rerank integration, test QA, and knowledge workbench flows.

## Boundaries

CarbonRag must preserve its own:

- auth and user isolation
- session and AskPage flow
- file parsing and citation boundary
- report and carbon accounting modules
- OpenSpec, GitNexus, Mattermost, and GitHub collaboration rules

Do not commit ignored `3rdparty/` source trees or ZIP archives into CarbonRag.

## Reference Roles

- `RAG-Pro`: main RAG knowledge-base product spine to migrate and adapt.
- `RMA-MUN/LangChain-RAG-FastAPI-Service`: algorithm reference for LangChain, HyDE, Chroma, and rerank patterns only.
- `ragPdfSystem`: future enterprise blueprint for async processing, object storage, OCR, evaluation, and GraphRAG.

## V1.6.x Acceptance Principle

RAG is accepted only when it is uploadable, parseable, chunkable, indexable, searchable, answerable, citable, and measurable. A page, facade, or fallback that only appears to work is not enough.
