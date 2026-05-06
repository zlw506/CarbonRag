## ADDED Requirements

### Requirement: Codex manages Git only through repository guardrails
CarbonRag SHALL allow Codex to inspect and operate Git for development tasks only according to repository workflow rules, with command intent visible before state-changing operations.

#### Scenario: Codex prepares a work round
- **WHEN** Codex starts a task in an existing checkout
- **THEN** it inspects worktree, branch, OpenSpec status, and relevant docs before proposing or executing state-changing Git operations

#### Scenario: Codex performs state-changing Git
- **WHEN** Codex needs to create a branch, commit, push, merge, or rebase
- **THEN** it states the intended command class and reason, avoids destructive commands, and follows the active OpenSpec and PR discipline

### Requirement: Existing CarbonRag checkouts do not repeat OpenSpec init
CarbonRag SHALL treat the existing `openspec/` directory as initialized brownfield project state and refresh instructions with `openspec update .` instead of repeating `openspec init`.

#### Scenario: Developer starts OpenSpec in this repository
- **WHEN** `openspec/config.yaml` and `openspec/specs/**` already exist
- **THEN** the workflow uses `openspec update .`, `openspec list`, and `openspec validate --all`

### Requirement: OpenSpec cleanup prompts preserve CarbonRag instructions by default
CarbonRag SHALL preserve `openspec/AGENTS.md` and Codex instruction files unless #1 confirms their content has been migrated.

#### Scenario: OpenSpec update asks to remove legacy files
- **WHEN** `openspec update .` asks whether to remove `openspec/AGENTS.md` or instruction files
- **THEN** the default answer is `n` until #1 approves cleanup after content preservation
