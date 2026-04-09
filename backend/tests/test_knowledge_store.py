from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone

from app.knowledge.chunker import chunk_text_to_knowledge_chunks
from app.knowledge.schemas import KnowledgeItem
from app.knowledge.store import KnowledgeStore
from app.session.adapters.sqlite_store import SQLiteSessionStore
from tests.test_helpers import create_test_user_id


def test_knowledge_store_supports_items_tasks_chunks_and_session_attachments(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = KnowledgeStore(sqlite_db_path=db_path)
    session_store = SQLiteSessionStore(db_path)
    owner_user_id = create_test_user_id(db_path, prefix="knowledge-owner")

    session = session_store.create_session(
        session_id="session-knowledge",
        owner_user_id=owner_user_id,
        title="知识库测试会话",
        created_at="2026-04-09T10:00:00+00:00",
    )
    upload_source = tmp_path / "upload.txt"
    upload_source.write_text("企业节能改造\n2026 年计划", encoding="utf-8")
    uploaded_file = session_store.create_uploaded_file(
        file_id="file-knowledge-001",
        session_id=session.session_id,
        filename="upload.txt",
        size=upload_source.stat().st_size,
        mime_type="text/plain",
        stored_at="2026-04-09T10:00:01+00:00",
        storage_path=str(upload_source),
    )

    item = KnowledgeItem(
        knowledge_item_id=uploaded_file.file_id,
        owner_user_id=owner_user_id,
        library_scope="personal",
        source_type="uploaded_file",
        source_ref=uploaded_file.file_id,
        file_id=uploaded_file.file_id,
        source="用户上传知识",
        source_url=None,
        sample_type=None,
        business_topic="energy",
        title=uploaded_file.filename,
        mime_type=uploaded_file.mime_type,
        storage_path=str(upload_source),
        parse_status="pending",
        ingest_status="pending",
        index_status="pending",
        is_enabled=True,
        session_attachable=True,
        source_hash=hashlib.sha256(upload_source.read_bytes()).hexdigest(),
        source_mtime=str(upload_source.stat().st_mtime),
        last_error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_indexed_at=None,
    )
    store.upsert_item(item)

    created_task = store.create_task(
        task_id="task-knowledge-001",
        knowledge_item_id=item.knowledge_item_id,
        owner_user_id=owner_user_id,
        requested_by_user_id=owner_user_id,
        task_type="upload_ingest",
        summary="上传文件入库",
    )
    assert created_task.status == "queued"

    claimed_task = store.claim_next_task()
    assert claimed_task is not None
    assert claimed_task.task_id == created_task.task_id
    assert claimed_task.status == "running"

    chunks = chunk_text_to_knowledge_chunks(
        knowledge_item_id=item.knowledge_item_id,
        title=item.title,
        source_type=item.source_type,
        library_scope=item.library_scope,
        source=item.source or "用户上传知识",
        snippet_text="企业正在推进能耗优化。\n\n重点关注照明与空调节能。",
        source_url=None,
        business_topic=item.business_topic,
    )
    store.replace_chunks(knowledge_item_id=item.knowledge_item_id, chunks=chunks)
    finished_task = store.finish_task(
        task_id=created_task.task_id,
        status="succeeded",
        summary="入库完成",
        error_detail=None,
    )
    assert finished_task is not None

    refreshed_item = store.get_item(item.knowledge_item_id)
    assert refreshed_item is not None
    assert refreshed_item.index_status == "indexed"
    assert refreshed_item.parse_status == "parsed"
    assert refreshed_item.ingest_status == "ingested"
    assert refreshed_item.chunk_count == len(chunks)
    assert refreshed_item.task_count >= 1

    detail = store.get_item_detail(knowledge_item_id=item.knowledge_item_id)
    assert detail is not None
    assert detail.item.knowledge_item_id == item.knowledge_item_id
    assert detail.chunks
    assert detail.tasks

    visible_item = store.get_visible_item(owner_user_id=owner_user_id, knowledge_item_id=item.knowledge_item_id)
    assert visible_item is not None
    item_by_source = store.get_item_by_source(
        owner_user_id=owner_user_id,
        library_scope="personal",
        source_type="uploaded_file",
        source_ref=uploaded_file.file_id,
    )
    assert item_by_source is not None
    assert item_by_source.knowledge_item_id == item.knowledge_item_id

    store.replace_session_knowledge_items(
        session_id=session.session_id,
        knowledge_item_ids=[item.knowledge_item_id],
        attached_at="2026-04-09T10:00:02+00:00",
    )
    assert store.list_session_knowledge_item_ids(session_id=session.session_id) == [item.knowledge_item_id]
    assert store.list_session_knowledge_items(session_id=session.session_id)[0].knowledge_item_id == item.knowledge_item_id

    uploads = store.list_my_uploads(owner_user_id=owner_user_id)
    assert uploads
    assert uploads[0].file_id == uploaded_file.file_id
    assert uploads[0].knowledge_item_id == item.knowledge_item_id

    connection = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    finally:
        connection.close()
    assert "session_knowledge_items" in tables
