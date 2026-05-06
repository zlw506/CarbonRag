## Purpose
Defines local/cloud runtime modes, CI, deployment, environment variables, rollback, and release branch policy.

## Requirements

### Requirement: CI validates PRs to main
CarbonRag SHALL run backend tests, frontend typecheck, and frontend build for pull requests targeting main.

#### Scenario: Pull request targets main
- **WHEN** a PR is opened or updated against main
- **THEN** GitHub Actions runs the required validation jobs

### Requirement: Main is the default public release baseline
CarbonRag SHALL treat main as the stable source and current public deployment baseline from V1.2.1 onward.

#### Scenario: Deployment docs are consulted
- **WHEN** Netlify or VPS deployment instructions are read
- **THEN** main is shown as the default deployment branch
