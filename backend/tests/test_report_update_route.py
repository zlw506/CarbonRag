import json

from fastapi.testclient import TestClient

from app.main import app
from app.report.service import ReportService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from app.schemas.ask import AskCitation

client = TestClient(app)


class FakeChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}：报告更新测试。"}
            for heading in payload["template_sections"]
        ]
        return type("Result", (), {"content": json.dumps({"title": payload["template_name"], "sections": sections}, ensure_ascii=False)})()


def test_report_update_route_persists_edited_content(monkeypatch, tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=store)
    report_service = ReportService(session_service=session_service)

    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.reports.get_report_service", lambda: report_service)

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    session_service.record_exchange(
        session_id=session_id,
        user_content="解释双碳目标",
        assistant_content="政策摘要回答。",
        assistant_status="ok",
        trace_id="trace-ask-001",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="政策依据",
                source_type="public_policy",
                source="国务院",
                source_url="https://example.com/policy",
                snippet="政策片段",
                chunk_id="policy_001_chunk_01",
            )
        ],
    )
    detail = session_service.get_session(session_id)
    created = client.post(
        "/api/v1/reports",
        json={
            "session_id": session_id,
            "report_type": "policy_summary",
            "source_message_ids": [detail.messages[-1].message_id],
            "output_format": "markdown",
        },
    ).json()

    updated = client.patch(
        f"/api/v1/reports/{created['report_id']}",
        json={
            "title": "编辑后的报告",
            "content": "# 编辑后的正文\n\n这是修改后的内容。\n",
        },
    )

    payload = updated.json()
    assert updated.status_code == 200
    assert payload["title"] == "编辑后的报告"
    assert payload["content"].startswith("# 编辑后的正文")
