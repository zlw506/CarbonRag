# CarbonRag

Current status: `V1.0.0 identity + isolation + admin foundation in progress`

## Project Positioning
CarbonRag is an SME-oriented carbon policy and enterprise application workbench. The current product line has already moved beyond a single-user prototype:

- session conversation workbench
- grounded ask with `public / private_sample / mixed`
- carbon calculation
- report generation
- feedback persistence
- local-dev and cloud-stable dual environment strategy

V1.0.0 adds the minimum governance layer required for multi-user trial use:

- local account system
- authenticated sessions with cookies
- per-user data isolation
- admin entry page

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

## Authentication and Governance
- Authentication uses `HttpOnly` cookie-based server-side sessions.
- Local account registration is open for normal users.
- Seed admin account: `admin / 123456`
- The seed admin must change password on first login.
- Roles are limited to `user` and `admin`.

Users can:
- ask questions
- run carbon calculations
- generate reports
- upload files
- view only their own history

Admins can additionally:
- view system status
- manage users
- manage private sample entry visibility and attachability
- view feedback overview
- trigger knowledge refresh tasks

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
- `POST /api/v1/sessions`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{id}`
- `PATCH /api/v1/sessions/{id}`
- `POST /api/v1/sessions/{id}/ask`
- `POST /api/v1/files`
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

## Current Capability Boundaries

### Ask
- supports `public`, `private_sample`, and `mixed`
- uses grounded citations
- only returns the current authenticated user's sessions and bindings

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
- [docs/deploy/LOCAL_DEV_VS_CLOUD_STABLE.md](/F:/Project\CarbonRag\CarbonRag/docs/deploy/LOCAL_DEV_VS_CLOUD_STABLE.md)
- [docs/deploy/VPS_BACKEND_DEPLOY.md](/F:/Project\CarbonRag\CarbonRag/docs/deploy/VPS_BACKEND_DEPLOY.md)
- [docs/deploy/NETLIFY_FRONTEND.md](/F:/Project\CarbonRag\CarbonRag/docs/deploy/NETLIFY_FRONTEND.md)
- [docs/PLAN/V1.0.0.md](/F:/Project\CarbonRag\CarbonRag/docs/PLAN/V1.0.0.md)
