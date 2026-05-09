## Why

CarbonRag already lets users upload files and attach knowledge items to a session, but the Ask workbench still behaves as if uploaded files are mostly display artifacts. Users need a session-scoped file reading path: upload business documents, parse them once, chunk them, ask questions against selected files, and receive file citations.

## What Changes

- Extend file metadata and parse result persistence for uploaded session files.
- Add a Docling-first parser pipeline with deterministic fallbacks for common office, text, CSV, HTML, PDF, and PPTX files.
- Keep uploaded file chunks inside the existing `knowledge_items / knowledge_chunks` retrieval path instead of creating a separate RAG system.
- Add `session_file_search` as an ask runtime tool that searches selected parsed uploads through `attached_file_ids`.
- Improve AskPage attachment chips, drag/drop upload, parse status polling, summary display, and private upload citation display.

## Non-Goals

- No vendor-native file upload as the main path.
- No full-file prompt injection.
- No per-question reparsing.
- No changes to #2 LightRAG core or #3 carbon factor page.
- No OCR guarantee when Docling/OCR providers are unavailable.

## Impact

- Modules: M2 Conversation / Session / Memory, M3 Frontend Chat UX, M5 Knowledge / File / RAG, M1 AI Runtime tools.
- API additions: `GET /api/v1/files/{file_id}` and expanded file response metadata.
- Database additions: `file_parse_results` and extended `files` metadata columns.
