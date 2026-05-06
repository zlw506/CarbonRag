# Design

## Approach

V1.2.5 treats collaboration infrastructure as a governance capability, not as product behavior. The implementation is documentation-first plus OpenSpec delta:

- Keep `openspec/specs/**` as the reviewed source of truth.
- Use `openspec/changes/formalize-open-collaboration-guide` to capture the governance update.
- Publish runbooks under `docs/governance/**`.
- Keep local-only generated artifacts ignored and rebuildable.

## Key Decisions

- `main` is the shared collaboration entrypoint and public deployment baseline.
- `release/cloud-stable` remains a compatibility branch only.
- #2/#3 use fork-and-PR.
- `Git-ys1` remains the final `main` approver.
- GitHub CLI and VS Code GitHub Pull Requests are recommended review tools, but human #1 approval is still required.

## Risks

- Contributors may assume ignored local files are missing required source. The asset inventory explicitly explains how each ignored class is rebuilt.
- OpenSpec automation may not be available in every Codex client. The workflow runbook provides manual fallback commands and file layout.
- GitHub CLI requires user authentication, so unauthenticated local checks are documented as blocked until `gh auth login`.
