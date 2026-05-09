# Session File Reading Architecture

V1.5.1 adds session-scoped file reading to the Ask workbench. The goal is not to create a second RAG stack. Uploaded files flow through the existing knowledge item and chunk model, then ask uses selected `attached_file_ids` to search only parsed and indexed session uploads.

## Boundaries

- Owner: #1 chat/workbench line.
- Does not modify #2 LightRAG core.
- Does not modify #3 carbon factor page.
- Does not send raw full files to model providers.
- Does not reparse files on every ask.

## Runtime Flow

1. AskPage uploads one or more files through `POST /api/v1/files`.
2. Backend validates file extension, MIME, size, session quota, and user quota.
3. File is stored as `<file_id>.<safe_ext>`.
4. `files` records upload metadata and parse state.
5. Upload creates a personal `knowledge_item`.
6. Knowledge task runner parses the file and writes `file_parse_results`.
7. Parsed text is chunked into `knowledge_chunks` with file locator metadata.
8. AskPage polls file status and only sends ready `attached_file_ids`.
9. `session_file_search` retrieves selected `private_upload` chunks.
10. Runtime citations include file name and optional page, sheet, slide, or section locator.

## Data Ownership

Files are owned by `owner_user_id` and bound to one session. Cross-user access returns `404` or empty evidence. A file that is uploaded but not parsed/indexed is visible as an attachment but cannot be injected into ask context.

## Citation Shape

`private_upload` citations may include:

- `file_id`
- `page_number`
- `sheet_name`
- `slide_number`
- `section_title`

The frontend should render these as compact labels such as `电费账单.pdf · p.2`.
