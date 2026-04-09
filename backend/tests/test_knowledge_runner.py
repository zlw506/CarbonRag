from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from app.knowledge.runner import KnowledgeTaskRunner
from app.knowledge.service import KnowledgeService
from app.knowledge.store import KnowledgeStore
from app.session.adapters.sqlite_store import SQLiteSessionStore
from tests.test_helpers import create_test_user_id


class _NoBootstrapKnowledgeService(KnowledgeService):
    def bootstrap_shared_library(self):  # type: ignore[override]
        return []


class _FakeSessionService:
    knowledge_service = None


def test_knowledge_task_runner_processes_queued_item(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    owner_user_id = create_test_user_id(db_path, prefix="knrunner")
    store = KnowledgeStore(sqlite_db_path=db_path)
    session_store = SQLiteSessionStore(db_path)

    session = session_store.create_session(
        session_id="session-runner",
        owner_user_id=owner_user_id,
        title="知识库运行器测试会话",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    source_path = tmp_path / "energy.txt"
    source_path.write_text("企业节能改造\n照明优化\n空调优化", encoding="utf-8")
    uploaded_file = session_store.create_uploaded_file(
        file_id="file-runner",
        session_id=session.session_id,
        filename="energy.txt",
        size=source_path.stat().st_size,
        mime_type="text/plain",
        stored_at=datetime.now(timezone.utc).isoformat(),
        storage_path=str(source_path),
    )
    item = store.get_item_by_source(
        owner_user_id=owner_user_id,
        library_scope="personal",
        source_type="uploaded_file",
        source_ref=uploaded_file.file_id,
    )
    if item is None:
        from app.knowledge.schemas import KnowledgeItem

        item = KnowledgeItem(
            knowledge_item_id="knowledge-item-runner",
            owner_user_id=owner_user_id,
            library_scope="personal",
            source_type="uploaded_file",
            source_ref=uploaded_file.file_id,
            file_id=uploaded_file.file_id,
            source="用户上传知识",
            source_url=None,
            sample_type=None,
            business_topic="energy",
            title="energy.txt",
            mime_type="text/plain",
            storage_path=str(source_path),
            parse_status="pending",
            ingest_status="pending",
            index_status="pending",
            is_enabled=True,
            session_attachable=True,
            source_hash=hashlib.sha256(source_path.read_bytes()).hexdigest(),
            source_mtime=str(source_path.stat().st_mtime),
            last_error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_indexed_at=None,
        )
    store.upsert_item(item)
    task = store.create_task(
        task_id="task-runner-001",
        knowledge_item_id=item.knowledge_item_id,
        owner_user_id=owner_user_id,
        requested_by_user_id=owner_user_id,
        task_type="upload_ingest",
        summary="上传文件入库",
    )

    service = _NoBootstrapKnowledgeService(store=store, session_service=_FakeSessionService())
    monkeypatch.setattr("app.knowledge.service.get_knowledge_service", lambda: service)

    runner = KnowledgeTaskRunner()
    runner.enqueue(task.task_id)
    processed = runner.run_once()

    assert processed == [task.task_id]
    refreshed_item = store.get_item(item.knowledge_item_id)
    assert refreshed_item is not None
    assert refreshed_item.index_status == "indexed"
    assert refreshed_item.parse_status == "parsed"
    assert store.list_chunks(item.knowledge_item_id)
