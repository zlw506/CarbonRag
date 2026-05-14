# Tasks: universal-file-preview-drawer

## 1. Backend

- [x] Add unified preview schemas and service.
- [x] Add `GET /api/v1/file-previews/{source_type}/{source_id}`.
- [x] Add `GET /api/v1/file-previews/{source_type}/{source_id}/raw`.
- [x] Support `session_file`, `rag_document`, `crawler_candidate`, and `knowledge_item`.
- [x] Enforce owner/admin, KB, and admin-only crawler candidate permissions.
- [x] Resolve raw files only from registered paths inside allowed runtime directories.

## 2. Frontend

- [x] Add `FilePreviewDrawer`.
- [x] Add `filePreview` service and types.
- [x] Wire AskPage attachment chips and citations.
- [x] Wire KnowledgeBaseWorkbench document preview.
- [x] Wire Admin policy crawler candidate preview.

## 3. Docs and Validation

- [x] Add architecture document.
- [ ] `openspec validate universal-file-preview-drawer --strict`
- [ ] `openspec validate --all`
- [ ] Targeted backend pytest.
- [ ] Frontend typecheck/build.
- [ ] `git diff --check`
