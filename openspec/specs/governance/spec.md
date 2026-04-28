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
