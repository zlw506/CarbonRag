# Design

## Approach

The current knowledge task runner already processes upload/rebuild tasks synchronously. V2.0.0 keeps that behavior and adds a small workflow recorder around the existing steps. The workflow layer is deliberately boring: Pydantic models, runtime DB persistence, and explicit node status updates.

## Workflow Nodes

The RAG ingest workflow records:

- `upload_received`
- `parse_document`
- `build_blocks`
- `build_chunks`
- `build_embeddings`
- `upsert_vector_index`
- `build_graph_candidates`
- `index_completed`

`build_graph_candidates` is allowed to be skipped. Embedding/vector nodes may be recorded as completed or skipped depending on the current lightweight backend.

## Governance Reservation

Governance fields are optional and default-safe:

- `tenant_id`
- `owner_user_id`
- `visibility`
- `created_by`
- `created_at`
- `updated_at`

The first version does not enforce RBAC. It only stores or exposes these fields where the current data model can carry them safely.

## Persistence

Runtime database tables store workflow runs, nodes, and checkpoints. Existing knowledge items and chunks receive additive governance columns with defaults derived from current owner/library scope values.

## Compatibility

Default ask/session/report/calc behavior remains unchanged. Retrieval-only metadata may include additional trace fields, but existing chunks, references, and metadata fields are preserved.
