## ADDED Requirements

### Requirement: Local model assets stay outside source control

CarbonRag SHALL document local chat model package placement and SHALL keep runtime model assets out of Git.

#### Scenario: Team member needs the local DeepSeek package

- **WHEN** a team member cannot download the model online
- **THEN** they request the offline package from #1 and place it under `data/outputs/models/LLM/<model-name>/`.

#### Scenario: Repository is cloned by another team

- **WHEN** a team member pulls `main`
- **THEN** they receive env examples, scripts, and docs, but no model weights.

