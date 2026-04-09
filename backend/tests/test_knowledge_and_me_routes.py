import json
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.auth.service import AuthService
from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.feedback.service import FeedbackService
from app.files.service import FileService
from app.files.storage import FileStorage
from app.knowledge import KnowledgeService
from app.knowledge.store import KnowledgeStore
from app.main import app
from app.report.service import ReportService
from app.report.storage import ReportStorage
from app.schemas.ask import AskCitation
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import TEST_PASSWORD, patch_test_auth_service, register_and_login

client = TestClient(app)


class FakeReportChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}: generated from knowledge-linked sources."}
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


def _build_factor_file(tmp_path: Path) -> Path:
    payload = {
        "version": "v1.1.0-test",
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
                "version": "v1.1.0-test",
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
                "version": "v1.1.0-test",
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
                "version": "v1.1.0-test",
            },
        ],
    }
    factor_file = tmp_path / "factors.json"
    factor_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return factor_file


def _build_runtime_services(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "carbonrag.sqlite3"
    patch_test_auth_service(monkeypatch, db_path=db_path)
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    knowledge_store = KnowledgeStore(sqlite_db_path=db_path)
    knowledge_service = KnowledgeService(store=knowledge_store, session_service=session_service)
    session_service.knowledge_service = knowledge_service
    file_service = FileService(session_service=session_service, storage=FileStorage(tmp_path / "uploads"))
    feedback_service = FeedbackService(session_service=session_service, store=store)
    carbon_service = CarbonService(
        factor_loader=CarbonFactorLoader(_build_factor_file(tmp_path)),
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
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)
    monkeypatch.setattr("app.api.v1.endpoints.knowledge.get_knowledge_service", lambda: knowledge_service)
    monkeypatch.setattr("app.api.v1.endpoints.private_samples.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.private_samples.catalog.get_knowledge_service", lambda: knowledge_service)
    monkeypatch.setattr("app.knowledge.get_knowledge_service", lambda: knowledge_service)
    monkeypatch.setattr("app.knowledge.service.get_knowledge_service", lambda: knowledge_service)
    monkeypatch.setattr("app.api.v1.endpoints.me.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.me.get_knowledge_service", lambda: knowledge_service)
    monkeypatch.setattr("app.api.v1.endpoints.me.get_report_service", lambda: report_service)
    monkeypatch.setattr("app.api.v1.endpoints.feedback.get_feedback_service", lambda: feedback_service)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeReportChatProvider())

    return session_service, file_service, feedback_service, knowledge_service, carbon_service, report_service


def test_knowledge_items_routes_attach_and_list_visible_sources(monkeypatch, tmp_path) -> None:
    session_service, _, _, _, _, _ = _build_runtime_services(monkeypatch, tmp_path)
    register_and_login(client, prefix="knowledge")

    response = client.get("/api/v1/knowledge-items")
    assert response.status_code == 200
    items = response.json()
    assert any(item["knowledge_item_id"] == "enterprise_doc_001" for item in items)
    assert any(item["knowledge_item_id"] == "energy_bill_sample_001" for item in items)

    detail_response = client.get("/api/v1/knowledge-items/enterprise_doc_001")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["knowledge_item_id"] == "enterprise_doc_001"

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    attach_response = client.put(
        f"/api/v1/sessions/{session_id}/knowledge-items",
        json={"knowledge_item_ids": ["enterprise_doc_001"]},
    )
    assert attach_response.status_code == 200
    assert attach_response.json()["attached_knowledge_item_count"] >= 1
    assert any(item["knowledge_item_id"] == "enterprise_doc_001" for item in attach_response.json()["attached_files"])

    task_response = client.get("/api/v1/knowledge-tasks")
    assert task_response.status_code == 200
    assert isinstance(task_response.json(), list)


def test_me_routes_return_current_user_assets_reports_and_feedback(monkeypatch, tmp_path) -> None:
    session_service, file_service, feedback_service, knowledge_service, _, report_service = _build_runtime_services(
        monkeypatch, tmp_path
    )
    user = register_and_login(client, prefix="me")

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]

    upload_response = client.post(
        "/api/v1/files",
        data={"session_id": session_id},
        files={"file": ("sample.txt", BytesIO(b"hello carbon"), "text/plain")},
    )
    assert upload_response.status_code == 200
    upload_id = upload_response.json()["file_id"]

    session_service.record_exchange(
        owner_user_id=user["user_id"],
        session_id=session_id,
        user_content="Summarize the policy basis.",
        assistant_content="This response cites policy evidence.",
        assistant_status="ok",
        trace_id="trace-me-report",
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
    assert session_detail is not None
    report_service.create_report(
        owner_user_id=user["user_id"],
        payload={
            "session_id": session_id,
            "report_type": "policy_summary",
            "source_message_ids": [session_detail.messages[-1].message_id],
            "output_format": "markdown",
        },
    )

    feedback_response = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "ask",
            "trace_id": "trace-me-feedback",
            "session_id": session_id,
            "rating": "up",
            "comment": "good",
        },
    )
    assert feedback_response.status_code == 200

    uploads_response = client.get("/api/v1/me/uploads")
    assert uploads_response.status_code == 200
    assert any(item["file_id"] == upload_id for item in uploads_response.json())

    reports_response = client.get("/api/v1/me/reports")
    assert reports_response.status_code == 200
    assert reports_response.json()

    feedbacks_response = client.get("/api/v1/me/feedback")
    assert feedbacks_response.status_code == 200
    assert any(item["trace_id"] == "trace-me-feedback" for item in feedbacks_response.json())
