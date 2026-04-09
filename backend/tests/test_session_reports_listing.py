import json

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest
from app.carbon.service import CarbonService
from app.report.service import ReportService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from app.schemas.ask import AskCitation
from tests.test_helpers import create_test_user_id


class FakeChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}: session reports listing test."}
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


def test_session_reports_listing_and_carbon_results(monkeypatch, tmp_path) -> None:
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
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())

    owner_user_id = create_test_user_id(store.db_path, prefix="report-list")
    session = session_service.create_session(owner_user_id=owner_user_id)
    session_service.record_exchange(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        user_content="Explain the dual-carbon target",
        assistant_content="Policy summary answer.",
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
    session_detail = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)
    report_service.create_report(
        owner_user_id=owner_user_id,
        payload={
            "session_id": session.session_id,
            "report_type": "policy_summary",
            "source_message_ids": [session_detail.messages[-1].message_id],
        },
    )
    carbon_service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(session_id=session.session_id, electricity_kwh=100),
    )

    reports = report_service.list_session_reports(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
    )
    carbon_results = report_service.list_session_carbon_results(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
    )

    assert len(reports) == 1
    assert reports[0].source_count >= 1
    assert len(carbon_results) == 1
