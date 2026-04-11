# CarbonRag

Current status: `V1.1.8B UX audit remediation in progress`

## Project Positioning
CarbonRag is an SME-oriented carbon policy and enterprise application workbench. The current product line has already moved beyond a single-user prototype:

- session conversation workbench
- grounded ask with `public / private_sample / mixed`
- carbon calculation
- report generation
- feedback persistence
- local-dev and cloud-stable dual environment strategy
- main / release / feature branch discipline

V1.1.0 adds the first manageable private knowledge flow on top of identity and isolation:

- personal knowledge library
- shared knowledge library
- knowledge ingest / rebuild / retry task flow
- admin console for users, feedback, knowledge items, and runtime status

V1.1.3 adds the first memory foundation on top of session workbench and grounded knowledge:

- session compaction with summary preservation
- context usage estimate and summary status
- backend-only `memory_notes` as a guarded long-memory prewire
- clear boundary between session summary and knowledge library content

V1.1.7 is the current chat UX audit and product-feel polish pass:

- focus-mode-first chat shell
- slimmer persistent chrome around the conversation area
- sticky bottom composer with compact chips and secondary controls
- clearer `pending / thinking / streaming / done` assistant message states
- lighter evidence access and compact context diagnostics

## Runtime Modes

### `local-dev`
- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`
- Frontend API base: `http://127.0.0.1:8000/api`
- Runtime database: SQLite fallback
- Purpose: active development, debugging, destructive verification

### `cloud-stable`
- Frontend: Netlify
- Backend: VPS
- Frontend API base: `/api`
- Runtime database: PostgreSQL
- Purpose: stable validation and external demo

These two environments do not share runtime data. Different session history, reports, calculations, and feedback between local and cloud are expected.

## Branch / Release Discipline
- `main`: stable source baseline after accepted releases
- `feature/*`: active development branches
- `release/cloud-stable`: deployment line for Netlify and VPS

`main` is the source baseline that should remain coherent and accepted; `release/cloud-stable` is the branch that actually powers cloud deployment; `feature/*` branches are where new work happens first.

## Authentication and Governance
- Authentication uses `HttpOnly` cookie-based server-side sessions.
- Local account registration is open for normal users.
- Seed admin account: `admin / 123456`
- The seed admin must change password on first login.
- Emergency seed-admin recovery is enabled: if the `admin` account is lost, disabled, or otherwise unavailable, submitting `admin / 123456` on the register page will restore the initial admin account and force password change on next login.
- Roles are limited to `user` and `admin`.

Users can:
- ask questions
- run carbon calculations
- generate reports
- upload files
- manage their own knowledge items
- view only their own history

Admins can additionally:
- view system status
- manage users
- manage shared private knowledge entry visibility and attachability
- view feedback overview
- monitor knowledge items and tasks
- trigger scan / rebuild / retry for private knowledge updates

Admins cannot read ordinary users' session or report body content through normal business APIs.

## Current Public API Surface

### Public
- `GET /healthz`

### Authenticated user APIs
- `GET /api/v1/system/info`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/change-password`
- `GET /api/v1/memory-notes`
- `POST /api/v1/memory-notes`
- `PATCH /api/v1/memory-notes/{memory_note_id}`
- `DELETE /api/v1/memory-notes/{memory_note_id}`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{id}`
- `PATCH /api/v1/sessions/{id}`
- `POST /api/v1/sessions/{id}/ask`
- `POST /api/v1/files`
- `GET /api/v1/knowledge-items`
- `GET /api/v1/knowledge-items/{knowledge_item_id}`
- `GET /api/v1/knowledge-tasks`
- `POST /api/v1/knowledge-tasks/{task_id}/retry`
- `PUT /api/v1/sessions/{id}/knowledge-items`
- `GET /api/v1/me/uploads`
- `GET /api/v1/me/reports`
- `GET /api/v1/me/feedback`
- `GET /api/v1/private-samples`
- `PUT /api/v1/sessions/{id}/attached-files/private-samples`
- `POST /api/v1/calc-carbon`
- `POST /api/v1/feedback`
- `POST /api/v1/reports`
- `POST /api/v1/generate-report` (deprecated alias)
- `GET /api/v1/reports/{report_id}`
- `PATCH /api/v1/reports/{report_id}`
- `GET /api/v1/sessions/{id}/reports`
- `GET /api/v1/sessions/{id}/carbon-calculations`

### Admin-only APIs
- `GET /api/v1/admin/system/status`
- `GET /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{user_id}`
- `POST /api/v1/admin/users/{user_id}/reset-password`
- `GET /api/v1/admin/feedback/overview`
- `GET /api/v1/admin/private-samples`
- `PATCH /api/v1/admin/private-samples/{doc_id}`
- `GET /api/v1/admin/knowledge-refresh-tasks`
- `POST /api/v1/admin/knowledge-refresh-tasks`
- `GET /api/v1/admin/knowledge-items`
- `PATCH /api/v1/admin/knowledge-items/{knowledge_item_id}`
- `GET /api/v1/admin/knowledge-tasks`
- `POST /api/v1/admin/knowledge-tasks/scan`
- `POST /api/v1/admin/knowledge-tasks/rebuild`
- `POST /api/v1/admin/knowledge-tasks/{task_id}/retry`

## Current Capability Boundaries

### Ask
- supports `public`, `private_sample`, and `mixed`
- uses grounded citations
- private retrieval now reads indexed `knowledge_items` / `knowledge_chunks`
- only returns the current authenticated user's sessions and bindings

### Session Memory
- ask uses session compaction when context grows beyond the estimated budget
- the session keeps a summary plus a recent-message window
- `GET /api/v1/sessions/{id}` now returns `memory_state`, including context estimate, summary presence, compacted-message count, and compaction status
- session summary is not a knowledge library entry
- `memory_notes` exist only as backend-managed user-level prewire, not as a front-end memory UI

### Private Knowledge
- uploaded files enter the knowledge task flow after upload
- shared `data/private_sample/` entries are imported as shared knowledge items
- private / mixed ask only searches knowledge items already attached to the current session
- unsupported or non-extractable files fall into `parse_failed` and can be retried

### Calc Carbon
- supports:
  - `electricity_kwh`
  - `natural_gas_m3`
  - `diesel_l`
- persists results to the current authenticated user's runtime data

### Report
- supports:
  - `policy_summary`
  - `mixed_analysis`
  - `carbon_summary`
- every report is bound to a `session_id`
- reports can reuse ask citations and optional calc results
- generated reports can be re-opened and edited in place

## Local Start

### Standard local start
Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-local.ps1
```

macOS / Linux:

```bash
bash scripts/dev-local.sh
```

### Bootstrap only
Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

macOS / Linux:

```bash
bash scripts/bootstrap.sh
```

`bootstrap` installs dependencies and prepares local templates. It does not keep frontend and backend running.

## Release Discipline
- local development: `feature/*`
- stable cloud release line: `release/cloud-stable`
- do not publish every commit to cloud
- Netlify production should track `release/cloud-stable`
- VPS production should deploy `release/cloud-stable`

## Documents
- [before_all.md](/F:/Project\CarbonRag\CarbonRag/before_all.md)
- [docs/API_BOUNDARY_DRAFT.md](/F:/Project\CarbonRag\CarbonRag/docs/API_BOUNDARY_DRAFT.md)
- [docs/DEVELOPMENT_BOOTSTRAP.md](/F:/Project\CarbonRag\CarbonRag/docs/DEVELOPMENT_BOOTSTRAP.md)
- [docs/GIT_WORKFLOW.md](/F:/Project\CarbonRag\CarbonRag/docs/GIT_WORKFLOW.md)
- [docs/GIT_RELEASE_FLOW.md](/F:/Project\CarbonRag\CarbonRag/docs/GIT_RELEASE_FLOW.md)
- [docs/architecture/PRIVATE_KNOWLEDGE_TASK_FLOW.md](/F:/Project\CarbonRag\CarbonRag/docs/architecture/PRIVATE_KNOWLEDGE_TASK_FLOW.md)
- [docs/research/claw-code/07_CHAT_UX_AND_MEMORY_NOTES.md](/F:/Project\CarbonRag\CarbonRag/docs/research/claw-code/07_CHAT_UX_AND_MEMORY_NOTES.md)
- [docs/deploy/LOCAL_DEV_VS_CLOUD_STABLE.md](/F:/Project\CarbonRag\CarbonRag/docs/deploy/LOCAL_DEV_VS_CLOUD_STABLE.md)
- [docs/deploy/VPS_BACKEND_DEPLOY.md](/F:/Project\CarbonRag\CarbonRag/docs/deploy/VPS_BACKEND_DEPLOY.md)
- [docs/deploy/NETLIFY_FRONTEND.md](/F:/Project\CarbonRag\CarbonRag/docs/deploy/NETLIFY_FRONTEND.md)
- [docs/PLAN/V1.0.0.md](/F:/Project\CarbonRag\CarbonRag/docs/PLAN/V1.0.0.md)
- [docs/PLAN/V1.1.0.md](/F:/Project\CarbonRag\CarbonRag/docs/PLAN/V1.1.0.md)
- [docs/PLAN/V1.1.3.md](/F:/Project\CarbonRag\CarbonRag/docs/PLAN/V1.1.3.md)
- [docs/PLAN/V1.1.4.md](/F:/Project\CarbonRag\CarbonRag/docs/PLAN/V1.1.4.md)
