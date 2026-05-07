import json

from fastapi.testclient import TestClient

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
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
            {"heading": heading, "body": f"{heading}: generated in report route test."}
            for heading in payload["template_sections"]
        ]
        return type(
            "Result",
            (),
            {"content": json.dumps({"title": payload["template_name"], "sections": sections}, ensure_ascii=False)},
        )()


def build_factor_file(tmp_path):
    payload = {
        "version": "v0.1.9a",
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
                "version": "v0.1.9a",
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
                "version": "v0.1.9a",
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
                "version": "v0.1.9a",
            },
        ],
    }
    factor_file = tmp_path / "factors.json"
    factor_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return factor_file


def build_services(tmp_path):
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=store)
    carbon_service = CarbonService(
        factor_loader=CarbonFactorLoader(build_factor_file(tmp_path)),
        session_service=session_service,
        store=store,
    )
    report_service = ReportService(
        session_service=session_service,
        carbon_service=carbon_service,
    )
    return session_service, carbon_service, report_service


def test_report_route_creates_policy_summary(monkeypatch, tmp_path) -> None:
    session_service, _, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.reports.get_report_service", lambda: report_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="report-policy")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    current_user = client.get("/api/v1/auth/me").json()["user"]
    session_service.record_exchange(
        owner_user_id=current_user["user_id"],
        session_id=session_id,
        user_content="What is the dual-carbon target?",
        assistant_content="Dual-carbon target explanation.",
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
    session = session_service.get_session(owner_user_id=current_user["user_id"], session_id=session_id)

    response = client.post(
        "/api/v1/reports",
        json={
            "session_id": session_id,
            "report_type": "policy_summary",
            "source_message_ids": [session.messages[-1].message_id],
            "output_format": "markdown",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["report_type"] == "policy_summary"
    assert payload["session_id"] == session_id
    assert payload["source_summary"]["public_policy_count"] == 1


def test_report_route_creates_carbon_summary(monkeypatch, tmp_path) -> None:
    session_service, carbon_service, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    monkeypatch.setattr("app.api.v1.endpoints.reports.get_report_service", lambda: report_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="report-carbon")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    calc_result = client.post(
        "/api/v1/calc-carbon",
        json={"session_id": session_id, "electricity_kwh": 12000},
    ).json()

    response = client.post(
        "/api/v1/reports",
        json={
            "session_id": session_id,
            "report_type": "carbon_summary",
            "carbon_result_id": calc_result["trace_id"],
            "output_format": "markdown",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["report_type"] == "carbon_summary"
    assert payload["source_summary"]["carbon_factor_count"] == 1


def test_report_route_uses_default_session_context_when_sources_omitted(monkeypatch, tmp_path) -> None:
    session_service, carbon_service, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    monkeypatch.setattr("app.api.v1.endpoints.reports.get_report_service", lambda: report_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="report-defaults")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    current_user = client.get("/api/v1/auth/me").json()["user"]
    session_service.record_exchange(
        owner_user_id=current_user["user_id"],
        session_id=session_id,
        user_content="Please summarize the policy and enterprise gap.",
        assistant_content="Mixed answer.",
        assistant_status="ok",
        trace_id="trace-ask-002",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="Policy Basis",
                source_type="public_policy",
                source="State Council",
                source_url="https://example.com/policy",
                snippet="Policy snippet",
                chunk_id="policy_001_chunk_01",
            ),
            AskCitation(
                doc_id="enterprise_doc_001",
                title="Enterprise Sample",
                source_type="private_sample",
                source="Sample",
                source_url=None,
                snippet="Enterprise snippet",
                chunk_id="enterprise_doc_001_chunk_01",
            ),
        ],
    )
    calc_result = client.post(
        "/api/v1/calc-carbon",
        json={"session_id": session_id, "electricity_kwh": 12000},
    ).json()

    mixed_response = client.post(
        "/api/v1/reports",
        json={
            "session_id": session_id,
            "report_type": "mixed_analysis",
            "output_format": "markdown",
        },
    )
    carbon_response = client.post(
        "/api/v1/reports",
        json={
            "session_id": session_id,
            "report_type": "carbon_summary",
            "output_format": "markdown",
        },
    )

    assert mixed_response.status_code == 200
    assert mixed_response.json()["source_summary"]["private_sample_count"] == 1
    assert carbon_response.status_code == 200
    assert any(source["source_ref"] == calc_result["trace_id"] for source in carbon_response.json()["sources"])
