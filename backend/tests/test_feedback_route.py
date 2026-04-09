from fastapi.testclient import TestClient

from app.feedback.service import FeedbackService
from app.main import app
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import patch_test_auth_service, register_and_login

client = TestClient(app)


def build_test_services(tmp_path) -> tuple[SessionService, FeedbackService]:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=store)
    feedback_service = FeedbackService(session_service=session_service, store=store)
    return session_service, feedback_service


def test_feedback_route_persists_ask_feedback(monkeypatch, tmp_path) -> None:
    session_service, feedback_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.feedback.get_feedback_service", lambda: feedback_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    user = register_and_login(client, prefix="feedback-ask")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "ask",
            "trace_id": "trace-ask-001",
            "session_id": session_id,
            "rating": "up",
            "comment": "Citations are clear.",
        },
    )

    payload = response.json()
    stored = feedback_service.get_entry(owner_user_id=user["user_id"], feedback_id=payload["feedback_id"])
    assert response.status_code == 200
    assert stored is not None
    assert stored.target_type == "ask"
    assert stored.rating == "up"


def test_feedback_route_persists_calc_feedback(monkeypatch, tmp_path) -> None:
    session_service, feedback_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.feedback.get_feedback_service", lambda: feedback_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    user = register_and_login(client, prefix="feedback-calc")
    response = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "calc_carbon",
            "trace_id": "calc-trace-001",
            "rating": "down",
        },
    )

    payload = response.json()
    stored = feedback_service.get_entry(owner_user_id=user["user_id"], feedback_id=payload["feedback_id"])
    assert response.status_code == 200
    assert stored is not None
    assert stored.target_type == "calc_carbon"
    assert stored.rating == "down"


def test_feedback_route_rejects_too_long_comment(monkeypatch, tmp_path) -> None:
    _, feedback_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.feedback.get_feedback_service", lambda: feedback_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="feedback-limit")
    response = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "ask",
            "trace_id": "trace-ask-002",
            "rating": "up",
            "comment": "a" * 501,
        },
    )

    assert response.status_code == 422
