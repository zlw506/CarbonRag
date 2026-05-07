## Scope

This change only introduces a provider boundary and default implementation around the existing parser.

## Current Flow

- File upload endpoint stores the file and calls `KnowledgeService.sync_uploaded_files()`.
- `KnowledgeTaskRunner` claims queued ingest tasks.
- `KnowledgeService.process_task()` currently calls `app.knowledge.parsers.parse_document()`.
- The parsed text is chunked by `chunk_knowledge_text()` and stored in `KnowledgeStore`.

## Provider Shape

- Keep the provider synchronous because the existing parser and ingest flow are synchronous.
- `DefaultParserProvider.supports()` accepts either the V1.4 signature (`file_path`, `content_type`) or the existing internal keyword style (`name`, `mime_type`).
- `DefaultParserProvider.parse()` returns a RAG `ParsedDocument`.
- Failed parses return a `ParsedDocument` with `parse_success=false`, `parse_error`, empty text, and score `0` for provider-level inspection.

## Non-Goals

- Do not route the existing ingest task through the provider in this change; that would alter failure semantics and is reserved for a later apply step.
- Do not add Docling, MinerU, OCR, or external parsing services.
