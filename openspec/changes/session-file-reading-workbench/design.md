## Design

### Data Flow

1. User uploads a file in AskPage.
2. Backend validates extension, MIME, size, session quota, and user storage quota.
3. Backend stores the file as `<file_id>.<safe_ext>` and records original filename only as display metadata.
4. Upload creates or refreshes a personal `knowledge_item`.
5. The knowledge task runner parses the file through `FileParserRegistry`.
6. Parser output is persisted to `file_parse_results`.
7. Chunks are written to existing `knowledge_chunks` with file locator metadata.
8. Ask requests pass selected `attached_file_ids`.
9. `session_file_search` maps selected file ids to indexed upload knowledge items and retrieves relevant chunks.
10. Runtime citations return `source_type=private_upload` with file locator fields.

### Parser Policy

`DoclingParserProvider` is preferred when available. If Docling is absent or fails on text-like formats, fallback parsers handle `txt`, `md`, `csv`, `html`, `pdf`, `docx`, `xlsx`, and `pptx`. Images and scanned PDFs require Docling/OCR support; otherwise the task is marked failed rather than pretending content was read.

### Retrieval Boundary

The new tool does not replace public/private/mixed retrieval. It is additive and only searches selected indexed uploads from the current session and current user. This keeps #2 LightRAG work separate while making parsed upload chunks reusable later.

### Security

Uploads use allowlisted extensions, MIME checks, generated server filenames, file-size limits, session-file limits, user-space limits, and owner/session checks. Executables, scripts, archives, macro Office files, and legacy binary Office files are rejected.
