from fastapi.testclient import TestClient

from app.main import app
from app.memory.service import MemoryService
from app.memory.store import MemoryStore
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import TEST_PASSWORD, patch_test_auth_service, register_and_login


client = TestClient(app)


class RouteSummaryProvider:
    def describe(self):
        from app.ai_runtime.providers.base import ProviderDescriptor

        return ProviderDescriptor(name="route-summary", provider_type="test", mode="chat", default_model="stub")

    def generate_response(self, *, system_prompt: str, user_input: str):
        del system_prompt, user_input
        from app.ai_runtime.providers.base import ChatCompletionResult

        return ChatCompletionResult(content="路由测试摘要。")


def build_services(tmp_path):
    db_path = tmp_path / "carbonrag.sqlite3"
    session_store = SQLiteSessionStore(db_path)
    memory_store = MemoryStore(sqlite_db_path=db_path)
    memory_service = MemoryService(store=memory_store, chat_provider=RouteSummaryProvider())
    session_service = SessionService(store=session_store, memory_service=memory_service)
    return session_service, memory_service, db_path


def test_memory_note_routes_and_user_isolation(monkeypatch, tmp_path) -> None:
    session_service, memory_service, db_path = build_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.memory.get_memory_service", lambda: memory_service)
    patch_test_auth_service(monkeypatch, db_path=db_path)

    first_user = register_and_login(client, prefix="memory-route-a")
    create_response = client.post(
        "/api/v1/memory-notes",
        json={"title": "企业背景", "content": "企业重点关注碳核算可解释性。", "is_enabled": True},
    )
    assert create_response.status_code == 200, create_response.text
    note_id = create_response.json()["memory_note_id"]

    list_response = client.get("/api/v1/memory-notes")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    client.post("/api/v1/auth/logout")
    second_user = register_and_login(client, prefix="memory-route-b")
    assert second_user["user_id"] != first_user["user_id"]

    assert client.get("/api/v1/memory-notes").json() == []
    not_found_response = client.patch(
        f"/api/v1/memory-notes/{note_id}",
        json={"title": "无权修改"},
    )
    assert not_found_response.status_code == 404


def test_session_detail_exposes_memory_state(monkeypatch, tmp_path) -> None:
    session_service, memory_service, db_path = build_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.memory.get_memory_service", lambda: memory_service)
    patch_test_auth_service(monkeypatch, db_path=db_path)

    current_user = register_and_login(client, prefix="memory-session")
    session_response = client.post("/api/v1/sessions", json={})
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    for index in range(8):
        session_service.record_exchange(
            owner_user_id=current_user["user_id"],
            session_id=session_id,
            user_content=f"第 {index + 1} 轮用户消息 {index}",
            assistant_content=f"第 {index + 1} 轮助手回复 {index}",
            assistant_status="ok",
            trace_id=f"trace-{index + 1:03d}",
            citations=[],
        )

    session_service.build_session_context(
        owner_user_id=current_user["user_id"],
        session_id=session_id,
        max_turns=6,
        upcoming_user_input="继续提问。",
    )

    detail_response = client.get(f"/api/v1/sessions/{session_id}")
    assert detail_response.status_code == 200
    memory_state = detail_response.json()["memory_state"]
    assert memory_state["summary_present"] is True
    assert memory_state["compaction_status"] == "compacted"
    assert memory_state["compacted_message_count"] == 4
