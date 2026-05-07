# Proposal

## Summary

Add a lightweight RAG workflow and governance foundation for V2.0.0. The ingest path remains synchronous, but each upload/index task can record workflow nodes and checkpoints so failures can be located without introducing a workflow engine.

## Scope

- Add `WorkflowRun`, `WorkflowNode`, and `ExecutionCheckpoint` contracts.
- Record the existing knowledge ingest task as upload, parse, block, chunk, embedding, vector index, optional graph, and completion nodes.
- Reserve tenant/owner/visibility metadata fields on RAG documents, chunks, embeddings, graph objects, and workflow runs.
- Extend RAG trace fields with workflow/parser/vector/error observability.

## Non-Goals

- No Keycloak, OpenFGA, Argo CD, K8s, LangGraph, or full OpenTelemetry.
- No rewrite of the current knowledge ingestion flow.
- No change to `/ask`, RAG Lab defaults, `/calc_carbon`, `/generate_report`, sessions, or reports.
