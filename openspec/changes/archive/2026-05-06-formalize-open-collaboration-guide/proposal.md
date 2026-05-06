# formalize-open-collaboration-guide

## Why

CarbonRag is entering multi-seat development. #2 and later contributors need a cloud-visible baseline that explains what to track, what to ignore, how to run OpenSpec, how to use Codex, how to test locally, and how PR review works.

## What Changes

- Add a unified open collaboration guide.
- Add seat onboarding, OpenSpec + Codex workflow, PR review, and tracked asset inventory runbooks.
- Record local OpenSpec, GitHub CLI, VS Code PR extension, and ignore-rule verification.
- Clarify that `main` is the shared collaboration entrypoint.

## What Does Not Change

- No business API changes.
- No frontend UI changes.
- No AI chat, auth, knowledge, report, calc, or feedback behavior changes.

## Verification

- `openspec list`
- `openspec validate --all`
- `git check-ignore -v .spec-gen/test.txt`
- `git check-ignore -v 3rdparty/spec-gen/test.txt`
- `git check-ignore -v .env`
- Local bootstrap and build checks where environment allows.
