# tighten-ai-git-and-openspec-start-rules

## Why

The V1.2.5 collaboration docs made OpenSpec available, but the start workflow still reads as if humans must manually run Git before AI work begins. This creates confusion and weakens the intended Codex-assisted workflow.

## What Changes

- Clarify that Codex may operate Git, but only under repository rules and visible command intent.
- Clarify that `openspec init` is not repeated for the existing CarbonRag brownfield repository.
- Clarify that `openspec update .` is a refresh command and legacy cleanup prompts require preservation review.
- Add a single "start work" prompt that lets Codex inspect the worktree, OpenSpec state, branch state, and propose the next safe steps.

## What Does Not Change

- No business code changes.
- No API changes.
- No UI changes.
- No new module boundaries.

## Verification

- `openspec validate tighten-ai-git-and-openspec-start-rules --strict`
- `openspec validate --all`
