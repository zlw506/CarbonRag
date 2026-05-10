# Tasks

- [x] Add OpenSpec change for V1.6.10.
- [x] Keep `kb_id` and `rag_mode` wired into `ChatRequest.payload` and add regression tests.
- [x] Add runtime/tool argument regression coverage for selected KB and retrieval mode.
- [x] Upgrade `/api/v1/rag/test-qa` to grounded chat-provider generation with no-hit/provider-error transparency.
- [x] Add two-KB isolation regression coverage.
- [x] Update KnowledgeBaseWorkbench Test QA result display and action labels.
- [x] Make RagLab admin-only and label it as legacy.
- [x] Run OpenSpec, targeted backend, frontend, and GitNexus verification.

Note: full backend pytest was attempted twice in this workspace and timed out; targeted V1.6.10 backend regression tests passed.
