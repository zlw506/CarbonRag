import json

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.carbon.schemas import CalcCarbonRequest
from app.report.service import ReportService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from app.schemas.ask import AskCitation


class FakeChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}：session reports listing 测试。"}
            for heading in payload["template_sections"]
        ]
        return type("Result", (), {"content": json.dumps({"title": payload["template_name"], "sections": sections}, ensure_ascii=False)})()


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

    session = session_service.create_session()
    session_service.record_exchange(
        session_id=session.session_id,
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
    session_detail = session_service.get_session(session.session_id)
    report_service.create_report(
        {
            "session_id": session.session_id,
            "report_type": "policy_summary",
            "source_message_ids": [session_detail.messages[-1].message_id],
        }
    )
    carbon_service.calculate(CalcCarbonRequest(session_id=session.session_id, electricity_kwh=100))

    reports = report_service.list_session_reports(session.session_id)
    carbon_results = report_service.list_session_carbon_results(session.session_id)

    assert len(reports) == 1
    assert reports[0].source_count >= 1
    assert len(carbon_results) == 1
