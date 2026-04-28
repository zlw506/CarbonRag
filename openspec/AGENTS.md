# OpenSpec Agent Instructions

## Role
Use `openspec/specs/**` as the current CarbonRag behavior source of truth and `openspec/changes/**` for proposed modifications.

## Rules
- Do not implement a new feature without an OpenSpec change id unless the task is explicitly docs-only or emergency hotfix.
- Do not treat spec-gen output as authoritative until it is manually reviewed.
- Keep specs aligned with the eight module domains in `docs/architecture/MODULE_BOUNDARY_MAP.md`.
- Mention affected specs and modules in every PR.

## Local Artifacts
- `.spec-gen/` is local analysis output and must not be committed.
- `3rdparty/spec-gen/` is a local pilot checkout and must not be committed.
