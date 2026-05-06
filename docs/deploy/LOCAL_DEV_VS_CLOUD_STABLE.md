# Local Dev vs Cloud Stable

## Purpose
CarbonRag now runs in two intentionally different modes:

- `local-dev`: latest development environment
- `cloud-stable`: stable validation environment

This split is required to keep daily feature work from polluting the shared demo and test surface.

## Branch and Runtime Discipline
- `t1/v1.2/*` and `t2/v1.2/*`: team development branches
- `feature/*`: legacy or single-person development branches
- `main`: stable source baseline and current public deployment baseline
- `release/cloud-stable`: compatibility release line retained during transition

The intended flow is:
1. develop on `t1/*`, `t2/*`, or approved feature branches
2. merge accepted work into `main` through PR review
3. deploy public cloud from `main`
4. keep `release/cloud-stable` only as a compatibility branch until fully retired

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

Fresh clone setup for #2/#3:

```powershell
git remote add upstream https://github.com/Git-ys1/CarbonRag.git
git fetch upstream
git switch -c t2/v1.2/onboarding-smoke upstream/main
openspec list
openspec validate --all
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

Ignored local assets are expected. `.env`, `frontend/.env.local`, dependencies, SQLite, uploads, and `.spec-gen/` are rebuilt locally and are not required from #1's machine.

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
V1.1.0 and V1.1.3 extend this split with private knowledge items, knowledge tasks, and session memory:

- every session belongs to one authenticated user
- reports, feedback, uploaded files, knowledge item bindings, carbon calculations, and memory notes inherit that ownership
- cross-user reads return `404`
- local uploaded files create local knowledge items only
- cloud uploaded files create cloud knowledge items only
- local and cloud do not share knowledge task queues, indexed private chunks, or session summaries

This rule applies in both environments. The difference is only the backing runtime database and deployment surface.

## Session Memory Boundary
- session compaction belongs to the session runtime, not the knowledge library
- session summary is a compressed view of old dialogue, not a knowledge item
- `memory_notes` are backend-only user-level notes, not a visible knowledge-library replacement
- knowledge library stores uploaded files and shared samples; memory stores dialogue context and user-level notes

## Which Environment Is For What?
- `local-dev` is for fast iteration and trial-and-error
- `cloud-stable` is for stable demo and external validation

Do not use the shared cloud environment for unfinished daily development noise.

## Release Discipline
- active work happens on `feature/*`
- stable source baseline is `main`
- stable cloud publishing happens from `main`
- Netlify production should track `main`
- VPS production should deploy `main`
- `release/cloud-stable` is retained only for compatibility while deployment settings are verified
- do not publish every commit

## Collaboration Docs

New seats should read:

- `docs/governance/OPEN_COLLABORATION_GUIDE.md`
- `docs/governance/SEAT_ONBOARDING_RUNBOOK.md`
- `docs/governance/OPENSPEC_CODEX_WORKFLOW_RUNBOOK.md`
- `docs/governance/TRACKED_COLLABORATION_ASSET_INVENTORY.md`
