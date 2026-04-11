import json

import pytest

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest
from app.carbon.service import CarbonService
from app.report.schemas import CreateReportRequest
from app.report.service import ReportService, ReportValidationError
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from app.schemas.ask import AskCitation
from tests.test_helpers import create_test_user_id


class FakeChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        payload = json.loads(user_input)
        sections = [
            {"heading": heading, "body": f"{heading}: generated report content."}
            for heading in payload["template_sections"]
        ]
        requested_title = payload.get("requested_title") or f"{payload['template_name']} - {payload['session']['title']}"
        return type(
            "Result",
            (),
            {
                "content": json.dumps(
                    {"title": requested_title, "sections": sections},
                    ensure_ascii=False,
                )
            },
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
    owner_user_id = create_test_user_id(session_service.store.db_path, prefix="report-mixed")
    session = session_service.create_session(owner_user_id=owner_user_id)
    session_service.record_exchange(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        user_content="Analyze the current enterprise issue with both policy and sample evidence.",
        assistant_content="This is a mixed response.",
        assistant_status="ok",
        trace_id="trace-001",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="Policy Basis",
                source_type="public_policy",
                source="State Council",
                source_url="https://example.com/policy",
                snippet="Policy requirement snippet",
                chunk_id="policy_001_chunk_01",
            ),
            AskCitation(
                doc_id="enterprise_doc_001",
                title="Enterprise Sample",
                source_type="private_sample",
                source="Sanitized sample",
                source_url=None,
                snippet="Enterprise sample snippet",
                chunk_id="enterprise_doc_001_chunk_01",
            ),
        ],
        knowledge_scope="mixed",
    )
    return owner_user_id, session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)


def test_report_service_generates_mixed_report_and_appends_system_message(monkeypatch, tmp_path) -> None:
    session_service, _, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    owner_user_id, session = seed_mixed_session(session_service)

    created = report_service.create_report(
        owner_user_id=owner_user_id,
        payload=CreateReportRequest(
            session_id=session.session_id,
            report_type="mixed_analysis",
            source_message_ids=[session.messages[-1].message_id],
        ),
    )

    refreshed = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)
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
    owner_user_id = create_test_user_id(session_service.store.db_path, prefix="report-carbon")
    session = session_service.create_session(owner_user_id=owner_user_id)
    result = carbon_service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(
            session_id=session.session_id,
            period_label="2026-Q2",
            electricity_kwh=100,
        ),
    )

    created = report_service.create_report(
        owner_user_id=owner_user_id,
        payload=CreateReportRequest(
            session_id=session.session_id,
            report_type="carbon_summary",
            carbon_result_id=result.trace_id,
        ),
    )

    assert created.report_type == "carbon_summary"
    assert created.source_summary.carbon_factor_count == 3
    assert any(item.source_type == "carbon_factor" for item in created.citations)


def test_report_service_rejects_mixed_report_without_private_citation(monkeypatch, tmp_path) -> None:
    session_service, _, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    owner_user_id = create_test_user_id(session_service.store.db_path, prefix="report-invalid")
    session = session_service.create_session(owner_user_id=owner_user_id)
    session_service.record_exchange(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        user_content="Explain policy requirements",
        assistant_content="Policy-only answer",
        assistant_status="ok",
        trace_id="trace-002",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="Policy Basis",
                source_type="public_policy",
                source="State Council",
                source_url="https://example.com/policy",
                snippet="Policy requirement snippet",
                chunk_id="policy_001_chunk_01",
            )
        ],
    )
    session_detail = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)

    with pytest.raises(ReportValidationError):
        report_service.create_report(
            owner_user_id=owner_user_id,
            payload=CreateReportRequest(
                session_id=session.session_id,
                report_type="mixed_analysis",
                source_message_ids=[session_detail.messages[-1].message_id],
            ),
        )


def test_report_service_falls_back_to_recent_valid_message_and_carbon_result(monkeypatch, tmp_path) -> None:
    session_service, carbon_service, report_service = build_services(tmp_path)
    monkeypatch.setattr("app.report.service.get_chat_provider", lambda: FakeChatProvider())
    owner_user_id, session = seed_mixed_session(session_service)
    result = carbon_service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(
            session_id=session.session_id,
            period_label="2026-Q3",
            electricity_kwh=88,
        ),
    )

    mixed_report = report_service.create_report(
        owner_user_id=owner_user_id,
        payload=CreateReportRequest(
            session_id=session.session_id,
            report_type="mixed_analysis",
        ),
    )
    carbon_report = report_service.create_report(
        owner_user_id=owner_user_id,
        payload=CreateReportRequest(
            session_id=session.session_id,
            report_type="carbon_summary",
        ),
    )

    assert mixed_report.source_summary.public_policy_count == 1
    assert mixed_report.source_summary.private_sample_count == 1
    assert any(source.source_type == "message" for source in mixed_report.sources)
    assert carbon_report.source_summary.carbon_factor_count == 3
    assert any(source.source_type == "carbon_result" and source.source_ref == result.trace_id for source in carbon_report.sources)
