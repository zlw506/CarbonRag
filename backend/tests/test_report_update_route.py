import json

from fastapi.testclient import TestClient

from app.main import app
from app.report.service import ReportService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from app.schemas.ask import AskCitation
from tests.test_helpers import patch_test_auth_service, register_and_login

client = TestClient(app)


class FakeChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}: report update route test."}
            for heading in payload["template_sections"]
        ]
        return type(
            "Result",
            (),
            {"content": json.dumps({"title": payload["template_name"], "sections": sections}, ensure_ascii=False)},
        )()


def test_report_update_route_persists_edited_content(monkeypatch, tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=store)
    report_service = ReportService(session_service=session_service)

    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.reports.get_report_service", lambda: report_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    user = register_and_login(client, prefix="report-update")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    session_service.record_exchange(
        owner_user_id=user["user_id"],
        session_id=session_id,
        user_content="Explain policy requirements",
        assistant_content="Policy answer.",
        assistant_status="ok",
        trace_id="trace-ask-001",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="Policy Basis",
                source_type="public_policy",
                source="State Council",
                source_url="https://example.com/policy",
                snippet="Policy snippet",
                chunk_id="policy_001_chunk_01",
            )
        ],
    )
    session_detail = session_service.get_session(owner_user_id=user["user_id"], session_id=session_id)

    created = client.post(
        "/api/v1/reports",
        json={
            "session_id": session_id,
            "report_type": "policy_summary",
            "source_message_ids": [session_detail.messages[-1].message_id],
        },
    ).json()

    response = client.patch(
        f"/api/v1/reports/{created['report_id']}",
        json={
            "title": "Edited Report Title",
            "content": "# Edited\n\nUpdated markdown body.",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["title"] == "Edited Report Title"
    assert payload["content"] == "# Edited\n\nUpdated markdown body."
