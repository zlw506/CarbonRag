from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.service import AuthService
from app.core.config import get_settings
from app.main import app
from app.memory.service import MemoryService
from app.memory.store import MemoryStore
from tests.test_helpers import register_and_login, patch_test_auth_service


def _build_memory_service(tmp_path) -> MemoryService:
    return MemoryService(store=MemoryStore(sqlite_db_path=tmp_path / "carbonrag.sqlite3"))


def test_memory_notes_crud_and_user_isolation(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    patch_test_auth_service(monkeypatch, db_path=db_path)
    memory_service = _build_memory_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.memory.get_memory_service", lambda: memory_service)
    monkeypatch.setattr("app.memory.service.get_memory_service", lambda: memory_service)

    client_a = TestClient(app)
    client_b = TestClient(app)

    user_a = register_and_login(client_a, prefix="memory-a")
    register_and_login(client_b, prefix="memory-b")

    create_response = client_a.post(
        "/api/v1/memory-notes",
        json={"title": "  我的记忆  ", "content": "  需要保留的上下文  ", "is_enabled": True},
    )
    assert create_response.status_code == 200, create_response.text
    note_id = create_response.json()["memory_note_id"]
    assert create_response.json()["owner_user_id"] == user_a["user_id"]

    list_response = client_a.get("/api/v1/memory-notes")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["title"] == "我的记忆"

    update_response = client_a.patch(
        f"/api/v1/memory-notes/{note_id}",
        json={"title": "  更新后的标题  ", "content": "  更新后的内容  ", "is_enabled": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "更新后的标题"
    assert update_response.json()["content"] == "更新后的内容"
    assert update_response.json()["is_enabled"] is False

    assert client_b.get("/api/v1/memory-notes").json() == []
    assert client_b.patch(
        f"/api/v1/memory-notes/{note_id}",
        json={"title": "非法修改"},
    ).status_code == 404
    assert client_b.delete(f"/api/v1/memory-notes/{note_id}").status_code == 404

    delete_response = client_a.delete(f"/api/v1/memory-notes/{note_id}")
    assert delete_response.status_code == 200
    assert client_a.get("/api/v1/memory-notes").json() == []

    get_settings.cache_clear()
