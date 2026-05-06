# CarbonRag Agent Instructions

## OpenSpec First

Before implementing any non-trivial feature, read the relevant specs under `openspec/specs/**`.

Also read `docs/governance/OPEN_COLLABORATION_GUIDE.md` and the active `openspec/changes/<change-id>/**` when the task affects collaboration, review, release, or module boundaries.

Use this mapping first:

- M1 AI Runtime / Provider / Model Config: `openspec/specs/ai-runtime/spec.md`
- M2 Conversation / Session / Memory: `openspec/specs/conversation-memory/spec.md`
- M3 Frontend Chat UX / Theme / Settings: `openspec/specs/frontend-shell-settings/spec.md`
- M4 Auth / User / Admin Governance: `openspec/specs/auth-governance/spec.md`
- M5 Knowledge / File / RAG: `openspec/specs/knowledge-rag/spec.md`
- M6 Carbon / Report / Feedback: `openspec/specs/carbon-report-feedback/spec.md`
- M7 DevOps / CI / Release: `openspec/specs/devops-release/spec.md`
- M8 Spec / Governance / Project Docs: `openspec/specs/governance/spec.md`

## Change Discipline

- Do not start a new feature without an OpenSpec change id unless the task is explicitly docs-only or an emergency hotfix.
- PRs must state the OpenSpec change id, affected specs, affected modules, risks, verification, and approval state.
- `Git-ys1` is the final `main` reviewer and CODEOWNERS fallback owner.
- This repository is already initialized for OpenSpec. Do not run `openspec init` in this repo unless #1 explicitly requests a full re-initialization.
- `openspec update .` may be used to refresh instructions. If it asks to remove `openspec/AGENTS.md` or instruction files, default to preserving them until #1 confirms migration.
- Codex may operate Git for setup, branching, commits, pushes, and merges only within the active task goal and repository workflow. State-changing Git operations must have a clear reason and must not be destructive unless explicitly requested.

## Local Artifacts

Never commit:

- `.spec-gen/`
- `3rdparty/spec-gen/`
- local model paths
- API keys or credentials
- local agent session records
- runtime outputs under `data/outputs/`

Local-only ignored files are not missing source. Recreate them from templates, scripts, dependency installs, or local runtime commands.

## Worktree Safety

- Do not revert user changes unless explicitly asked.
- Keep generated drafts separate from manually reviewed specs.
- Treat `openspec/specs/**` as the current behavior source of truth and `openspec/changes/**` as proposed change work.
