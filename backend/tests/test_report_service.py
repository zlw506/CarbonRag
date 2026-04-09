import json

import pytest

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.carbon.schemas import CalcCarbonRequest
from app.report.schemas import CreateReportRequest
from app.report.service import ReportService, ReportValidationError
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from app.schemas.ask import AskCitation


class FakeChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}：基于当前上下文生成的报告内容。"}
            for heading in payload["template_sections"]
        ]
        requested_title = payload.get("requested_title") or f"{payload['template_name']} - {payload['session']['title']}"
        return type("Result", (), {"content": json.dumps({"title": requested_title, "sections": sections}, ensure_ascii=False)})()


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


def build_services(tmp_path) -> tuple[SessionService, CarbonService, ReportService]:
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


def seed_mixed_session(session_service: SessionService):
    session = session_service.create_session()
    session_service.record_exchange(
        session_id=session.session_id,
        user_content="结合政策和样例分析当前企业问题。",
        assistant_content="这是一次 mixed 回答。",
        assistant_status="ok",
        trace_id="trace-001",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="政策依据",
                source_type="public_policy",
                source="国务院",
                source_url="https://example.com/policy",
                snippet="政策要求片段",
                chunk_id="policy_001_chunk_01",
            ),
            AskCitation(
                doc_id="enterprise_doc_001",
                title="企业样例",
                source_type="private_sample",
                source="脱敏样例",
                source_url=None,
                snippet="企业样例片段",
                chunk_id="enterprise_doc_001_chunk_01",
            ),
        ],
        knowledge_scope="mixed",
    )
    return session_service.get_session(session.session_id)


def test_report_service_generates_mixed_report_and_appends_system_message(monkeypatch, tmp_path) -> None:
    session_service, _, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    session = seed_mixed_session(session_service)

    created = report_service.create_report(
        CreateReportRequest(
            session_id=session.session_id,
            report_type="mixed_analysis",
            source_message_ids=[session.messages[-1].message_id],
        )
    )

    refreshed = session_service.get_session(session.session_id)
    assert created.report_type == "mixed_analysis"
    assert created.source_summary.public_policy_count == 1
    assert created.source_summary.private_sample_count == 1
    assert "## 依据列表" in created.content
    assert refreshed is not None
    assert refreshed.messages[-1].role == "system"
    assert created.report_id in refreshed.messages[-1].content


def test_report_service_generates_carbon_summary(monkeypatch, tmp_path) -> None:
    session_service, carbon_service, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    session = session_service.create_session()
    result = carbon_service.calculate(
        CalcCarbonRequest(
            session_id=session.session_id,
            period_label="2026-Q2",
            electricity_kwh=100,
        )
    )

    created = report_service.create_report(
        CreateReportRequest(
            session_id=session.session_id,
            report_type="carbon_summary",
            carbon_result_id=result.trace_id,
        )
    )

    assert created.report_type == "carbon_summary"
    assert created.source_summary.carbon_factor_count == 3
    assert any(item.source_type == "carbon_factor" for item in created.citations)


def test_report_service_rejects_mixed_report_without_private_citation(monkeypatch, tmp_path) -> None:
    session_service, _, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    session = session_service.create_session()
    session_service.record_exchange(
        session_id=session.session_id,
        user_content="解释政策",
        assistant_content="只有政策依据",
        assistant_status="ok",
        trace_id="trace-002",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="政策依据",
                source_type="public_policy",
                source="国务院",
                source_url="https://example.com/policy",
                snippet="政策要求片段",
                chunk_id="policy_001_chunk_01",
            )
        ],
    )
    session_detail = session_service.get_session(session.session_id)

    with pytest.raises(ReportValidationError):
        report_service.create_report(
            CreateReportRequest(
                session_id=session.session_id,
                report_type="mixed_analysis",
                source_message_ids=[session_detail.messages[-1].message_id],
            )
        )
