from datetime import datetime, timezone

from app.report.schemas import ReportCitation, ReportSourceEntry, ReportSourceSummary, StoredReport
from app.report.storage import ReportStorage
from app.session.adapters.sqlite_store import SQLiteSessionStore
from tests.test_helpers import create_test_user_id


def test_report_storage_persists_and_reload_report(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    owner_user_id = create_test_user_id(db_path, prefix="report-storage")
    created_session = store.create_session(
        session_id="session-demo",
        owner_user_id=owner_user_id,
        title="新对话 2026-04-09 12:00",
        created_at="2026-04-09T12:00:00+00:00",
    )
    storage = ReportStorage(store=store)

    created = storage.create_report(
        owner_user_id=owner_user_id,
        report=StoredReport(
            report_id="report-demo",
            session_id=created_session.session_id,
            report_type="policy_summary",
            title="Policy Summary",
            content="# Policy Summary\n\nGenerated content.",
            output_format="markdown",
            citations=[
                ReportCitation(
                    source_type="public_policy",
                    title="Policy Basis",
                    source="State Council",
                    source_url="https://example.com/policy",
                    snippet="Policy snippet",
                    chunk_id="policy_001_chunk_01",
                )
            ],
            source_summary=ReportSourceSummary(
                public_policy_count=1,
                private_sample_count=0,
                carbon_factor_count=0,
                total_citation_count=1,
            ),
            sources=[
                ReportSourceEntry(
                    source_type="message",
                    source_ref="msg-001",
                    label="Assistant message",
                    order_index=1,
                )
            ],
            trace_id="report-trace-001",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    )

    reloaded = storage.get_report(owner_user_id=owner_user_id, report_id=created.report_id)

    assert reloaded is not None
    assert reloaded.report_id == created.report_id
    assert reloaded.session_id == created_session.session_id
    assert reloaded.source_summary.public_policy_count == 1
    assert reloaded.sources[0].source_type == "message"
