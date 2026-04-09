# Local Dev vs Cloud Stable

## Purpose
CarbonRag now runs in two intentionally different modes:

- `local-dev`: latest development environment
- `cloud-stable`: stable validation environment

This split is required to keep daily feature work from polluting the shared demo and test surface.

## `local-dev`
- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`
- Frontend API base: `http://127.0.0.1:8000/api`
- Runtime database: SQLite fallback
- Typical use:
  - feature development
  - debugging
  - destructive verification
  - temporary or experimental data

Recommended start:

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-local.ps1
```

macOS / Linux:

```bash
bash scripts/dev-local.sh
```

## `cloud-stable`
- Frontend: Netlify
- Backend: VPS
- Frontend API base: `/api`
- Backend runtime database: PostgreSQL
- Typical use:
  - stable demo
  - external validation
  - release acceptance

## Do Local and Cloud Share Data?
No.

Current rule:
- local development uses SQLite fallback
- cloud-stable uses PostgreSQL

That means these differences are expected:
- local chat history is not the same as cloud chat history
- local reports are not the same as cloud reports
- local carbon calculations are not the same as cloud carbon calculations
- cloud sessions can sync across devices, while local and cloud do not sync with each other

## Authentication and Ownership
V1.1.0 further extends this split with private knowledge items and knowledge tasks:

- every session belongs to one authenticated user
- reports, feedback, uploaded files, knowledge item bindings, and carbon calculations inherit that ownership
- cross-user reads return `404`
- local uploaded files create local knowledge items only
- cloud uploaded files create cloud knowledge items only
- local and cloud do not share knowledge task queues or indexed private chunks

This rule applies in both environments. The difference is only the backing runtime database and deployment surface.

## Which Environment Is For What?
- `local-dev` is for fast iteration and trial-and-error
- `cloud-stable` is for stable demo and external validation

Do not use the shared cloud environment for unfinished daily development noise.

## Release Discipline
- active work happens on `feature/*`
- stable cloud publishing happens from `release/cloud-stable`
- Netlify production should track `release/cloud-stable`
- VPS production should deploy `release/cloud-stable`
- do not publish every commit
