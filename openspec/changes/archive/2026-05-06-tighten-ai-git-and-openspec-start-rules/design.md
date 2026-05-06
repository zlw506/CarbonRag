# Design

## Approach

Keep the workflow simple: one visible start prompt, then Codex performs inspection and safe Git/OpenSpec operations according to repository policy.

## Rules

- Codex can run `git status`, `git branch`, `git log`, `git fetch`, `git diff`, and other inspection commands as part of normal setup.
- Codex can create branches, commit, push, and merge only when the current task explicitly requires it and after it reports the exact intent.
- Codex must not use destructive Git commands unless explicitly requested.
- Existing CarbonRag checkouts use `openspec update .`, `openspec list`, and `openspec validate --all`, not `openspec init`.
- If `openspec update .` asks to remove `openspec/AGENTS.md`, default to preserving it until #1 migrates its content elsewhere.
