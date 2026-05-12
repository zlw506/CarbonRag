from datetime import datetime, timezone

from app.api.v1.endpoints.sessions import build_chat_request
from app.auth.schemas import AuthenticatedUser
from app.knowledge.schemas import KnowledgeItem
from app.schemas.ask import AskRequest


def _item(
    *,
    knowledge_item_id: str,
    source_type: str,
    index_status: str,
    file_id: str | None = None,
) -> KnowledgeItem:
    now = datetime.now(timezone.utc)
    return KnowledgeItem(
        knowledge_item_id=knowledge_item_id,
        owner_user_id="user-001",
        library_scope="personal",
        source_type=source_type,  # type: ignore[arg-type]
        source_ref=file_id or knowledge_item_id,
        file_id=file_id,
        source="用户上传知识" if source_type == "uploaded_file" else "样例库",
        title=knowledge_item_id,
        mime_type="text/plain",
        storage_path=f"/tmp/{knowledge_item_id}.txt",
        parse_status="parsed",
        ingest_status="ingested",
        index_status=index_status,  # type: ignore[arg-type]
        created_at=now,
        updated_at=now,
    )


class _FakeSessionService:
    def list_session_knowledge_items(self, *, owner_user_id: str, session_id: str):
        return [
            _item(knowledge_item_id="file-001", source_type="uploaded_file", index_status="indexed", file_id="file-001"),
            _item(knowledge_item_id="file-002", source_type="uploaded_file", index_status="pending", file_id="file-002"),
            _item(knowledge_item_id="sample-001", source_type="private_sample_repo", index_status="indexed"),
        ]

    def build_session_context(self, **kwargs):  # noqa: ANN003
        return {"recent_messages": [], "context_usage_estimate": 0}


class _FakeSessionServiceWithoutUploadLink:
    def list_session_knowledge_items(self, *, owner_user_id: str, session_id: str):
        return [
            _item(knowledge_item_id="sample-001", source_type="private_sample_repo", index_status="indexed"),
        ]

    def build_session_context(self, **kwargs):  # noqa: ANN003
        return {"recent_messages": [], "context_usage_estimate": 0}


class _FakeKnowledgeStore:
    def __init__(self) -> None:
        self.item = _item(
            knowledge_item_id="file-003",
            source_type="uploaded_file",
            index_status="indexed",
            file_id="file-003",
        )

    def get_item_by_source(self, **kwargs):  # noqa: ANN003
        if kwargs.get("source_ref") == "file-003":
            return self.item
        return None

    def get_uploaded_file_detail(self, **kwargs):  # noqa: ANN003
        if kwargs.get("file_id") == "file-003":
            return {"file_id": "file-003", "session_id": "session-001"}
        return None


class _FakeKnowledgeService:
    def __init__(self) -> None:
        self.store = _FakeKnowledgeStore()

    def list_visible_items(self, **kwargs):  # noqa: ANN003
        if kwargs.get("file_id") == "file-003":
            return [self.store.item]
        if "file-003" in (kwargs.get("knowledge_item_ids") or []):
            return [self.store.item]
        return []


def test_build_chat_request_only_includes_selected_indexed_attached_files(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: _FakeSessionService())
    user = AuthenticatedUser(
        user_id="user-001",
        username="tester",
        display_name="tester",
        role="user",
        is_active=True,
        password_must_change=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    chat_request, effective_private_ids = build_chat_request(
        session_id="session-001",
        current_user=user,
        payload=AskRequest(
            question="读取上传文件",
            knowledge_scope="public",
            attached_file_ids=["file-001", "file-002", "missing-file"],
        ),
    )

    assert effective_private_ids == ["sample-001"]
    assert chat_request.payload["attached_file_knowledge_item_ids"] == ["file-001"]


def test_build_chat_request_resolves_selected_upload_from_files_table(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: _FakeSessionServiceWithoutUploadLink())
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_knowledge_service", lambda: _FakeKnowledgeService())
    user = AuthenticatedUser(
        user_id="user-001",
        username="tester",
        display_name="tester",
        role="user",
        is_active=True,
        password_must_change=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    chat_request, effective_private_ids = build_chat_request(
        session_id="session-001",
        current_user=user,
        payload=AskRequest(
            question="读取上传文件",
            knowledge_scope="public",
            attached_file_ids=["file-003"],
        ),
    )

    assert effective_private_ids == ["sample-001"]
    assert chat_request.payload["attached_file_knowledge_item_ids"] == ["file-003"]
