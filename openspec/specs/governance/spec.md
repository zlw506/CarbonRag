## Purpose
Defines OpenSpec usage, PR discipline, CODEOWNERS, module boundaries, version rules, and multi-team collaboration rules.
## Requirements
### Requirement: OpenSpec governs proposed feature changes
CarbonRag SHALL use OpenSpec changes for new non-trivial feature proposals before implementation.

#### Scenario: PR modifies product behavior
- **WHEN** a PR changes product behavior
- **THEN** the PR declares an OpenSpec change id and affected specs

### Requirement: PRs declare module impact and approval
CarbonRag SHALL require PRs to declare affected M1-M8 modules, risks, verification, and approval status.

#### Scenario: PR is submitted to main
- **WHEN** a contributor opens a PR to main
- **THEN** the PR template captures module, risk, verification, and approval fields

### Requirement: Shared collaboration assets are tracked
CarbonRag SHALL keep OpenSpec specs, Codex skills, governance docs, architecture docs, scripts, PR templates, CODEOWNERS, env templates, and version plans in the repository so every seat can start from the same collaboration baseline.

#### Scenario: New contributor clones main
- **WHEN** a contributor clones or forks `main`
- **THEN** the repository includes the OpenSpec specs, governance runbooks, scripts, env templates, PR template, and CODEOWNERS needed to run local validation

### Requirement: Local-only artifacts are rebuildable and ignored
CarbonRag SHALL ignore secrets, dependencies, runtime databases, uploads, spec-gen output, local model paths, and local analysis caches while documenting how each class is recreated locally.

#### Scenario: Contributor does not receive ignored files
- **WHEN** a contributor does not receive `.env`, `node_modules`, `.spec-gen`, SQLite files, uploads, or local runtime data from Git
- **THEN** the governance docs explain how to recreate or regenerate those assets from tracked templates, scripts, or local commands

### Requirement: OpenSpec and Codex workflow is executable from terminal instructions
CarbonRag SHALL document a terminal-first OpenSpec workflow and a Codex prompt template for proposing, applying, reviewing, and validating changes.

#### Scenario: Codex client cannot invoke OpenSpec automation
- **WHEN** a Codex client cannot directly call OpenSpec skills or commands
- **THEN** the contributor can follow the documented terminal commands and manual `openspec/changes/<change-id>` file layout

### Requirement: PR review remains human-approved
CarbonRag SHALL allow Codex-assisted review but require #1 human approval before a PR is accepted into `main`.

#### Scenario: PR is ready for review
- **WHEN** a PR targets `main`
- **THEN** #1 runs or reviews OpenSpec validation, module/risk impact, tests, and Codex review output before approving, commenting, or requesting changes
