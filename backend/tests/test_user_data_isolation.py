import json

from fastapi.testclient import TestClient

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.feedback.service import FeedbackService
from app.files.service import FileService
from app.files.storage import FileStorage
from app.main import app
from app.report.service import ReportService
from app.report.storage import ReportStorage
from app.schemas.ask import AskCitation
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import TEST_PASSWORD, patch_test_auth_service


class FakeReportChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}: generated from isolated session sources."}
            for heading in payload["template_sections"]
        ]
        return type(
            "Result",
            (),
            {
                "content": json.dumps(
                    {"title": payload["requested_title"] or payload["template_name"], "sections": sections},
                    ensure_ascii=False,
                )
            },
        )()


def build_factor_file(tmp_path):
    payload = {
        "version": "v1.0.0-test",
        "factors": [
            {
                "factor_id": "factor-electricity",
                "item": "electricity",
                "name": "Electricity Demo Factor",
                "unit": "kgCO2e/kWh",
                "value": 0.57,
                "source": "Demo Source",
                "source_url": "https://example.com/electricity",
                "note": "demo",
                "version": "v1.0.0-test",
            },
            {
                "factor_id": "factor-natural-gas",
                "item": "natural_gas",
                "name": "Natural Gas Demo Factor",
                "unit": "kgCO2e/m3",
                "value": 2.162,
                "source": "Demo Source",
                "source_url": "https://example.com/gas",
                "note": "demo",
                "version": "v1.0.0-test",
            },
            {
                "factor_id": "factor-diesel",
                "item": "diesel",
                "name": "Diesel Demo Factor",
                "unit": "kgCO2e/L",
                "value": 2.63,
                "source": "Demo Source",
                "source_url": "https://example.com/diesel",
                "note": "demo",
                "version": "v1.0.0-test",
            },
        ],
    }
    factor_file = tmp_path / "factors.json"
    factor_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return factor_file


def patch_runtime_services(monkeypatch, tmp_path):
    db_path = tmp_path / "carbonrag.sqlite3"
    auth_service = patch_test_auth_service(monkeypatch, db_path=db_path)
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    file_service = FileService(
        session_service=session_service,
        storage=FileStorage(upload_root=tmp_path / "uploads"),
    )
    feedback_service = FeedbackService(session_service=session_service, store=store)
    carbon_service = CarbonService(
        factor_loader=CarbonFactorLoader(build_factor_file(tmp_path)),
        session_service=session_service,
        store=store,
    )
    report_storage = ReportStorage(store=store)
    report_service = ReportService(
        session_service=session_service,
        carbon_service=carbon_service,
        storage=report_storage,
    )

    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.private_samples.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)
    monkeypatch.setattr("app.api.v1.endpoints.feedback.get_feedback_service", lambda: feedback_service)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    monkeypatch.setattr("app.api.v1.endpoints.reports.get_report_service", lambda: report_service)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeReportChatProvider())

    return auth_service, session_service, feedback_service


def register_and_login(client: TestClient, username: str) -> dict:
    client.cookies.clear()
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200
    return login_response.json()["user"]


def test_user_owned_resources_are_isolated(monkeypatch, tmp_path) -> None:
    _, session_service, feedback_service = patch_runtime_services(monkeypatch, tmp_path)
    client_a = TestClient(app)
    client_b = TestClient(app)

    user_a = register_and_login(client_a, "member_a")
    user_b = register_and_login(client_b, "member_b")

    session_response = client_a.post("/api/v1/sessions", json={})
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    private_samples_response = client_a.get("/api/v1/private-samples")
    assert private_samples_response.status_code == 200
    first_doc_id = private_samples_response.json()[0]["doc_id"]
    attach_response = client_a.put(
        f"/api/v1/sessions/{session_id}/attached-files/private-samples",
        json={"doc_ids": [first_doc_id]},
    )
    assert attach_response.status_code == 200

    upload_response = client_a.post(
        "/api/v1/files",
        data={"session_id": session_id},
        files={"file": ("sample.txt", b"demo content", "text/plain")},
    )
    assert upload_response.status_code == 200

    calc_response = client_a.post(
        "/api/v1/calc-carbon",
        json={
            "session_id": session_id,
            "period_label": "2026-Q2",
            "electricity_kwh": 1200,
            "natural_gas_m3": 80,
            "diesel_l": 12,
        },
    )
    assert calc_response.status_code == 200
    carbon_result_id = calc_response.json()["trace_id"]

    session_service.record_exchange(
        owner_user_id=user_a["user_id"],
        session_id=session_id,
        user_content="Summarize the policy basis.",
        assistant_content="This response cites policy evidence.",
        assistant_status="ok",
        trace_id="trace-ask-owned",
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
    session_detail = session_service.get_session(owner_user_id=user_a["user_id"], session_id=session_id)
    assert session_detail is not None
    source_message_id = session_detail.messages[-1].message_id

    report_response = client_a.post(
        "/api/v1/reports",
        json={
            "session_id": session_id,
            "report_type": "policy_summary",
            "source_message_ids": [source_message_id],
            "output_format": "markdown",
        },
    )
    assert report_response.status_code == 200
    report_id = report_response.json()["report_id"]

    feedback_response = client_a.post(
        "/api/v1/feedback",
        json={
            "target_type": "ask",
            "trace_id": "trace-ask-owned",
            "session_id": session_id,
            "rating": "up",
            "comment": "Grounded.",
        },
    )
    assert feedback_response.status_code == 200
    feedback_id = feedback_response.json()["feedback_id"]

    assert client_b.get(f"/api/v1/sessions/{session_id}").status_code == 404
    assert client_b.get(f"/api/v1/reports/{report_id}").status_code == 404
    assert client_b.get(f"/api/v1/sessions/{session_id}/reports").status_code == 404
    assert client_b.get(f"/api/v1/sessions/{session_id}/carbon-calculations").status_code == 404

    session_detail_b = session_service.get_session(owner_user_id=user_b["user_id"], session_id=session_id)
    assert session_detail_b is None
    feedback_b = feedback_service.get_entry(owner_user_id=user_b["user_id"], feedback_id=feedback_id)
    assert feedback_b is None

    list_sessions_response = client_b.get("/api/v1/sessions")
    assert list_sessions_response.status_code == 200
    assert all(item["session_id"] != session_id for item in list_sessions_response.json())
    assert client_a.get(f"/api/v1/reports/{report_id}").status_code == 200
    assert client_a.get(f"/api/v1/sessions/{session_id}/carbon-calculations").status_code == 200
    assert client_a.get(f"/api/v1/sessions/{session_id}").status_code == 200
