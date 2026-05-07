from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.runner import KnowledgeTaskRunner
from app.knowledge.service import KnowledgeService
from app.knowledge.store import KnowledgeStore
from app.rag.contracts import ChunkRecord, EmbeddingRecord, ParsedDocument, RetrievalTrace
from app.rag.graph import GraphEntity, GraphRelation
from app.rag.service import build_rag_query_params
from app.rag.workflow import WorkflowRecorder, build_rag_ingest_workflow
from app.session.adapters.sqlite_store import SQLiteSessionStore
from tests.test_helpers import create_test_user_id


class _NoBootstrapKnowledgeService(KnowledgeService):
    def bootstrap_shared_library(self):  # type: ignore[override]
        return []


class _FakeSessionService:
    knowledge_service = None


def _create_upload(tmp_path, *, filename: str, content: str, mime_type: str = "text/plain"):
    db_path = tmp_path / "carbonrag.sqlite3"
    owner_user_id = create_test_user_id(db_path, prefix="workflow")
    session_store = SQLiteSessionStore(db_path)
    session = session_store.create_session(
        session_id="session-workflow",
        owner_user_id=owner_user_id,
        title="workflow test",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    source_path = tmp_path / filename
    source_path.write_text(content, encoding="utf-8")
    uploaded_file = session_store.create_uploaded_file(
        file_id=f"file-{filename.replace('.', '-')}",
        session_id=session.session_id,
        filename=filename,
        size=source_path.stat().st_size,
        mime_type=mime_type,
        stored_at=datetime.now(timezone.utc).isoformat(),
        storage_path=str(source_path),
    )
    return db_path, owner_user_id, uploaded_file


def test_workflow_recorder_tracks_node_status_and_checkpoints() -> None:
    workflow = build_rag_ingest_workflow(
        knowledge_item_id="item-001",
        owner_user_id="user-001",
        tenant_id="tenant-001",
        visibility="private",
    )
    recorder = WorkflowRecorder(workflow)

    recorder.start_run()
    recorder.start_node("upload_received", state={"file_id": "file-001"})
    recorder.complete_node("upload_received", state={"accepted": True})
    recorder.start_node("parse_document")
    recorder.fail_node("parse_document", error_message="parse failed")

    assert workflow.status == "failed"
    assert workflow.current_node == "parse_document"
    assert workflow.node("upload_received").status == "completed"  # type: ignore[union-attr]
    assert workflow.node("parse_document").status == "failed"  # type: ignore[union-attr]
    assert workflow.checkpoints
    assert workflow.tenant_id == "tenant-001"
    assert workflow.visibility == "private"


def test_knowledge_ingest_success_records_completed_workflow_and_governance(tmp_path, monkeypatch) -> None:
    db_path, owner_user_id, uploaded_file = _create_upload(
        tmp_path,
        filename="workflow.txt",
        content="Carbon accounting workflow test.\n\nThis file should produce an indexed chunk.",
    )
    store = KnowledgeStore(sqlite_db_path=db_path)
    runner = KnowledgeTaskRunner()
    service = _NoBootstrapKnowledgeService(store=store, session_service=_FakeSessionService())

    monkeypatch.setattr("app.knowledge.runner.get_knowledge_task_runner", lambda: runner)
    monkeypatch.setattr("app.knowledge.service.get_knowledge_service", lambda: service)

    tasks = service.sync_uploaded_files(owner_user_id=owner_user_id)
    processed = runner.run_once()

    assert tasks[0].task_id in processed
    workflow = store.get_latest_workflow_run(knowledge_item_id=uploaded_file.file_id)
    assert workflow is not None
    assert workflow.status == "completed"
    assert workflow.current_node == "index_completed"
    assert workflow.owner_user_id == owner_user_id
    assert workflow.tenant_id == owner_user_id
    assert workflow.visibility == "private"

    nodes = {node.node_id: node for node in workflow.nodes}
    assert nodes["upload_received"].status == "completed"
    assert nodes["parse_document"].status == "completed"
    assert nodes["build_chunks"].status == "completed"
    assert nodes["build_embeddings"].status == "skipped"
    assert nodes["upsert_vector_index"].status == "completed"
    assert nodes["build_graph_candidates"].status == "skipped"
    assert nodes["index_completed"].status == "completed"
    assert workflow.checkpoints

    item = store.get_item(uploaded_file.file_id)
    chunks = store.list_chunks(uploaded_file.file_id)
    assert item is not None
    assert item.tenant_id == owner_user_id
    assert item.visibility == "private"
    assert item.created_by == owner_user_id
    assert chunks
    assert chunks[0].tenant_id == owner_user_id
    assert chunks[0].owner_user_id == owner_user_id
    assert chunks[0].visibility == "private"


def test_knowledge_ingest_parse_failure_marks_workflow_failed(tmp_path, monkeypatch) -> None:
    db_path, owner_user_id, uploaded_file = _create_upload(
        tmp_path,
        filename="legacy.doc",
        content="legacy binary doc is unsupported",
        mime_type="application/msword",
    )
    store = KnowledgeStore(sqlite_db_path=db_path)
    runner = KnowledgeTaskRunner()
    service = _NoBootstrapKnowledgeService(store=store, session_service=_FakeSessionService())

    monkeypatch.setattr("app.knowledge.runner.get_knowledge_task_runner", lambda: runner)
    monkeypatch.setattr("app.knowledge.service.get_knowledge_service", lambda: service)

    tasks = service.sync_uploaded_files(owner_user_id=owner_user_id)
    processed = runner.run_once()

    assert tasks[0].task_id in processed
    workflow = store.get_latest_workflow_run(knowledge_item_id=uploaded_file.file_id)
    assert workflow is not None
    assert workflow.status == "failed"
    assert workflow.current_node == "parse_document"
    parse_node = next(node for node in workflow.nodes if node.node_id == "parse_document")
    assert parse_node.status == "failed"
    assert parse_node.error_message


def test_rag_contracts_reserve_governance_and_trace_fields() -> None:
    parsed = ParsedDocument(
        source_uri="file://doc.md",
        source_type="local_file",
        title="Doc",
        text="content",
        tenant_id="tenant-001",
        owner_user_id="user-001",
        visibility="tenant",
        created_by="user-001",
    )
    chunk = ChunkRecord(
        chunk_id="chunk-001",
        document_id=parsed.document_id,
        text="content",
        source_type="private_upload",
        title="Doc",
        tenant_id=parsed.tenant_id,
        owner_user_id=parsed.owner_user_id,
        visibility=parsed.visibility,
        created_by=parsed.created_by,
    )
    embedding = EmbeddingRecord(
        chunk_id=chunk.chunk_id,
        vector=[0.1, 0.2],
        tenant_id=chunk.tenant_id,
        visibility=chunk.visibility,
    )
    entity = GraphEntity(entity_id="entity-001", name="CarbonRag", tenant_id=chunk.tenant_id, visibility=chunk.visibility)
    relation = GraphRelation(
        relation_id="relation-001",
        source_entity_id=entity.entity_id,
        target_entity_id="entity-002",
        tenant_id=chunk.tenant_id,
        visibility=chunk.visibility,
    )
    trace = RetrievalTrace(
        query="test",
        workflow_id="workflow-001",
        parser_name="default",
        vector_backend="current",
        error_code=None,
    )

    assert parsed.visibility == "tenant"
    assert chunk.tenant_id == "tenant-001"
    assert embedding.dimension == 2
    assert entity.visibility == "tenant"
    assert relation.tenant_id == "tenant-001"
    assert trace.workflow_id == "workflow-001"
    assert trace.vector_backend == "current"


def test_default_ask_params_do_not_enable_experimental_workflow_modes() -> None:
    params = build_rag_query_params(question="carbon policy", knowledge_scope="mixed")

    assert params.graph_mode == "off"
    assert params.retrieval_strategy is None
    assert params.retrieval_only is True
