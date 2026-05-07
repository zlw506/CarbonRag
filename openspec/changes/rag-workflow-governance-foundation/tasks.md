# Tasks

## Proposal

- [x] Create V2.0.0 OpenSpec change for RAG workflow and governance foundation.
- [x] Inspect current knowledge upload, parse, chunk, and indexing flow.

## Apply

- [x] Add workflow contracts and a lightweight recorder for node/checkpoint status.
- [x] Add runtime DB tables and store methods for workflow runs, nodes, and checkpoints.
- [x] Integrate workflow recording into existing knowledge task processing without changing default behavior.
- [x] Reserve tenant/owner/visibility governance fields on RAG contracts, graph objects, knowledge items, and chunks.
- [x] Add minimal RAG trace fields for workflow/parser/vector/error metadata.
- [x] Add tests for workflow creation, node status, parse failure, successful ingest, governance fields, and default ask compatibility.
- [x] Run `openspec validate rag-workflow-governance-foundation --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
- [x] Commit locally without push or PR.
