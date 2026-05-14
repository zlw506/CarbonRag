# Change: universal-file-preview-drawer

## Why

CarbonRag now stores uploaded files, RAG-Pro KB documents, crawler candidates, and citations, but users can mostly see snippets rather than the source document. V1.7.2 adds one consistent preview path so users can inspect parsed content, chunks, metadata, and raw files without exposing server storage paths.

## What Changes

- Add a unified file preview API for `session_file`, `rag_document`, `crawler_candidate`, and `knowledge_item`.
- Add a safe raw file endpoint resolved from server-side logical IDs.
- Add a shared frontend `FilePreviewDrawer`.
- Wire preview actions into AskPage attachments/citations, KnowledgeBaseWorkbench documents, and Admin crawler candidates.
- Document path boundaries and permission rules.

## Out Of Scope

- No full Office layout renderer.
- No direct frontend access to `storage_path`.
- No new parser or crawler runtime.
