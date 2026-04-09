from datetime import datetime, timezone

from app.report.schemas import ReportCitation, ReportSourceEntry, ReportSourceSummary, StoredReport
from app.report.storage import ReportStorage
from app.session.adapters.sqlite_store import SQLiteSessionStore


def test_report_storage_persists_and_reload_report(tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    created_session = store.create_session(
        session_id="session-demo",
        title="新对话 2026-04-09 12:00",
        created_at="2026-04-09T12:00:00+00:00",
    )
    storage = ReportStorage(store=store)
    timestamp = datetime.now(timezone.utc)

    stored = storage.create_report(
        StoredReport(
            report_id="report-001",
            session_id=created_session.session_id,
            report_type="policy_summary",
            title="政策解读摘要 - 新对话",
            content="# Demo report\n",
            output_format="markdown",
            citations=[
                ReportCitation(
                    source_type="public_policy",
                    title="政策标题",
                    source="国务院",
                    source_url="https://example.com/policy",
                    snippet="政策片段",
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
                    label="消息来源",
                    order_index=0,
                )
            ],
            trace_id="report-trace-001",
            created_at=timestamp,
            updated_at=timestamp,
        )
    )

    assert stored.report_id == "report-001"
    assert stored.citations[0].source_type == "public_policy"
    assert stored.sources[0].source_type == "message"

    reloaded = storage.get_report("report-001")
    assert reloaded is not None
    assert reloaded.title == "政策解读摘要 - 新对话"
    assert reloaded.source_summary.total_citation_count == 1
