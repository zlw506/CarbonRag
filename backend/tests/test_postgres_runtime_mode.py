import json

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.carbon.schemas import CalcCarbonRequest
from app.feedback.schemas import FeedbackRequest
from app.feedback.service import FeedbackService
from app.session.adapters.postgres_store import PostgreSQLSessionStore
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService


class FakeRuntimeDatabase:
    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.messages: list[dict] = []
        self.files: list[dict] = []
        self.session_private_samples: list[dict] = []
        self.feedback_entries: dict[str, dict] = {}
        self.carbon_calculations: dict[str, dict] = {}

    def build_session_summary(self, session_id: str) -> dict | None:
        session = self.sessions.get(session_id)
        if session is None:
            return None
        return {
            "session_id": session["session_id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "message_count": sum(1 for item in self.messages if item["session_id"] == session_id),
            "file_count": sum(1 for item in self.files if item["session_id"] == session_id),
            "attached_private_sample_count": sum(
                1 for item in self.session_private_samples if item["session_id"] == session_id
            ),
        }

    def list_session_summaries(self) -> list[dict]:
        summaries = [
            self.build_session_summary(session_id)
            for session_id in self.sessions
        ]
        return sorted(
            [item for item in summaries if item is not None],
            key=lambda item: (item["updated_at"], item["created_at"]),
            reverse=True,
        )


class FakeCursor:
    def __init__(self, db: FakeRuntimeDatabase) -> None:
        self.db = db
        self._rows: list[dict] = []
        self.rowcount = 0

    def execute(self, statement: str, params=None) -> None:
        normalized = " ".join(statement.split()).lower()
        params = params or ()
        self.rowcount = 0

        if normalized.startswith("create table") or normalized.startswith("create index"):
            self._rows = []
            return

        if normalized.startswith("insert into sessions"):
            session_id, title, created_at, updated_at = params
            self.db.sessions[session_id] = {
                "session_id": session_id,
                "title": title,
                "created_at": created_at,
                "updated_at": updated_at,
                "knowledge_scope_last_used": None,
                "source_summary_json": None,
            }
            self.rowcount = 1
            self._rows = []
            return

        if "from sessions s" in normalized:
            if "where s.session_id = %s" in normalized:
                summary = self.db.build_session_summary(params[0])
                self._rows = [summary] if summary is not None else []
            else:
                self._rows = self.db.list_session_summaries()
            return

        if "select knowledge_scope_last_used, source_summary_json from sessions" in normalized:
            session = self.db.sessions.get(params[0])
            self._rows = [
                {
                    "knowledge_scope_last_used": session["knowledge_scope_last_used"],
                    "source_summary_json": session["source_summary_json"],
                }
            ] if session else []
            return

        if normalized.startswith("update sessions set title = %s, updated_at = %s"):
            title, updated_at, session_id = params
            session = self.db.sessions.get(session_id)
            if session is not None:
                session["title"] = title
                session["updated_at"] = updated_at
                self.rowcount = 1
            self._rows = []
            return

        if normalized.startswith("update sessions set updated_at = %s, knowledge_scope_last_used = %s"):
            updated_at, knowledge_scope_last_used, source_summary_json, session_id = params
            session = self.db.sessions.get(session_id)
            if session is not None:
                session["updated_at"] = updated_at
                session["knowledge_scope_last_used"] = knowledge_scope_last_used
                session["source_summary_json"] = source_summary_json
                self.rowcount = 1
            self._rows = []
            return

        if normalized.startswith("update sessions set updated_at = %s where session_id = %s"):
            updated_at, session_id = params
            session = self.db.sessions.get(session_id)
            if session is not None:
                session["updated_at"] = updated_at
                self.rowcount = 1
            self._rows = []
            return

        if normalized.startswith("insert into messages"):
            message_id, session_id, role, content, status, trace_id, citations_json, created_at = params
            self.db.messages.append(
                {
                    "message_seq": len(self.db.messages) + 1,
                    "message_id": message_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "status": status,
                    "trace_id": trace_id,
                    "citations_json": citations_json,
                    "created_at": created_at,
                }
            )
            self.rowcount = 1
            self._rows = []
            return

        if "from messages" in normalized and "where message_id = %s" in normalized:
            row = next((item for item in self.db.messages if item["message_id"] == params[0]), None)
            self._rows = [row] if row is not None else []
            return

        if "from messages" in normalized and "where session_id = %s" in normalized:
            rows = [item for item in self.db.messages if item["session_id"] == params[0]]
            rows.sort(key=lambda item: item["message_seq"], reverse="desc" in normalized)
            if "limit %s" in normalized:
                rows = rows[: params[1]]
            self._rows = rows
            return

        if normalized.startswith("select 1 from sessions where session_id = %s"):
            self._rows = [{"exists": 1}] if params[0] in self.db.sessions else []
            return

        if normalized.startswith("insert into files"):
            file_id, session_id, filename, size, mime_type, stored_at, storage_path = params
            self.db.files.append(
                {
                    "file_seq": len(self.db.files) + 1,
                    "file_id": file_id,
                    "session_id": session_id,
                    "filename": filename,
                    "size": size,
                    "mime_type": mime_type,
                    "stored_at": stored_at,
                    "storage_path": storage_path,
                }
            )
            self.rowcount = 1
            self._rows = []
            return

        if "from files" in normalized and "where file_id = %s" in normalized:
            row = next((item for item in self.db.files if item["file_id"] == params[0]), None)
            if row is not None:
                row = {
                    "file_id": row["file_id"],
                    "session_id": row["session_id"],
                    "filename": row["filename"],
                    "size": row["size"],
                    "mime_type": row["mime_type"],
                    "stored_at": row["stored_at"],
                }
            self._rows = [row] if row is not None else []
            return

        if "from files" in normalized and "where session_id = %s" in normalized:
            rows = [item for item in self.db.files if item["session_id"] == params[0]]
            rows.sort(key=lambda item: item["file_seq"], reverse=True)
            self._rows = [
                {
                    "file_id": row["file_id"],
                    "session_id": row["session_id"],
                    "filename": row["filename"],
                    "size": row["size"],
                    "mime_type": row["mime_type"],
                    "stored_at": row["stored_at"],
                }
                for row in rows
            ]
            return

        if normalized.startswith("delete from session_private_samples where session_id = %s"):
            session_id = params[0]
            self.db.session_private_samples = [
                item for item in self.db.session_private_samples if item["session_id"] != session_id
            ]
            self._rows = []
            return

        if normalized.startswith("insert into session_private_samples"):
            session_id, doc_id, attached_at = params
            self.db.session_private_samples.append(
                {
                    "attachment_seq": len(self.db.session_private_samples) + 1,
                    "session_id": session_id,
                    "doc_id": doc_id,
                    "attached_at": attached_at,
                }
            )
            self.rowcount = 1
            self._rows = []
            return

        if "select doc_id, attached_at from session_private_samples" in normalized:
            rows = [item for item in self.db.session_private_samples if item["session_id"] == params[0]]
            rows.sort(key=lambda item: item["attachment_seq"], reverse=True)
            self._rows = rows
            return

        if "select doc_id from session_private_samples" in normalized:
            rows = [item for item in self.db.session_private_samples if item["session_id"] == params[0]]
            rows.sort(key=lambda item: item["attachment_seq"], reverse=True)
            self._rows = [{"doc_id": row["doc_id"]} for row in rows]
            return

        if normalized.startswith("insert into feedback_entries"):
            (
                feedback_id,
                target_type,
                trace_id,
                session_id,
                rating,
                comment,
                created_at,
            ) = params
            self.db.feedback_entries[feedback_id] = {
                "feedback_id": feedback_id,
                "target_type": target_type,
                "trace_id": trace_id,
                "session_id": session_id,
                "rating": rating,
                "comment": comment,
                "created_at": created_at,
            }
            self.rowcount = 1
            self._rows = []
            return

        if "from feedback_entries" in normalized and "where feedback_id = %s" in normalized:
            row = self.db.feedback_entries.get(params[0])
            self._rows = [row] if row is not None else []
            return

        if normalized.startswith("insert into carbon_calculations"):
            (
                trace_id,
                session_id,
                period_label,
                electricity_kwh,
                natural_gas_m3,
                diesel_l,
                total_emission_kgco2e,
                breakdown_json,
                citations_json,
                created_at,
            ) = params
            self.db.carbon_calculations[trace_id] = {
                "trace_id": trace_id,
                "session_id": session_id,
                "period_label": period_label,
                "electricity_kwh": electricity_kwh,
                "natural_gas_m3": natural_gas_m3,
                "diesel_l": diesel_l,
                "total_emission_kgco2e": total_emission_kgco2e,
                "breakdown_json": breakdown_json,
                "citations_json": citations_json,
                "created_at": created_at,
            }
            self.rowcount = 1
            self._rows = []
            return

        if "from carbon_calculations" in normalized and "where trace_id = %s" in normalized:
            row = self.db.carbon_calculations.get(params[0])
            self._rows = [row] if row is not None else []
            return

        raise AssertionError(f"Unsupported SQL in fake PostgreSQL layer: {statement}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeConnection:
    def __init__(self, db: FakeRuntimeDatabase) -> None:
        self.db = db

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.db)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def patch_postgres_connect(monkeypatch, db: FakeRuntimeDatabase) -> None:
    fake_connect = lambda *args, **kwargs: FakeConnection(db)
    monkeypatch.setattr("app.runtime_db.bootstrap.psycopg.connect", fake_connect)
    monkeypatch.setattr("app.session.adapters.postgres_store.psycopg.connect", fake_connect)
    monkeypatch.setattr("app.feedback.service.psycopg.connect", fake_connect)
    monkeypatch.setattr("app.carbon.service.psycopg.connect", fake_connect)


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


def test_postgres_session_store_persists_message_and_file(monkeypatch) -> None:
    db = FakeRuntimeDatabase()
    patch_postgres_connect(monkeypatch, db)
    store = PostgreSQLSessionStore("postgresql://example")

    created = store.create_session(
        session_id="session-demo",
        title="新对话 2026-04-08 10:00",
        created_at="2026-04-08T10:00:00+00:00",
    )
    store.append_message(
        session_id=created.session_id,
        message_id="msg-001",
        role="user",
        content="什么是双碳目标？",
        created_at="2026-04-08T10:00:01+00:00",
    )
    store.create_uploaded_file(
        file_id="file-001",
        session_id=created.session_id,
        filename="sample.txt",
        size=128,
        mime_type="text/plain",
        stored_at="2026-04-08T10:00:02+00:00",
        storage_path="/srv/carbonrag/shared/uploads/sample.txt",
    )
    store.replace_attached_private_samples(
        session_id=created.session_id,
        doc_ids=["enterprise_doc_001"],
        attached_at="2026-04-08T10:00:03+00:00",
    )

    session = store.get_session(created.session_id)

    assert session is not None
    assert len(session.messages) == 1
    assert session.messages[0].content == "什么是双碳目标？"
    assert len(session.files) == 1
    assert session.files[0].filename == "sample.txt"
    assert any(item.source_type == "private_sample" for item in session.attached_files)


def test_feedback_service_persists_with_postgres_backend(monkeypatch, tmp_path) -> None:
    db = FakeRuntimeDatabase()
    patch_postgres_connect(monkeypatch, db)
    sqlite_store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=sqlite_store)
    session = session_service.create_session()
    service = FeedbackService(
        session_service=session_service,
        store=sqlite_store,
        database_url="postgresql://example",
    )

    result = service.submit(
        FeedbackRequest(
            target_type="ask",
            trace_id="trace-ask-001",
            session_id=session.session_id,
            rating="up",
            comment="grounded answer",
        )
    )
    stored = service.get_entry(result.feedback_id)

    assert stored is not None
    assert stored.trace_id == "trace-ask-001"
    assert stored.rating == "up"


def test_carbon_service_persists_with_postgres_backend(monkeypatch, tmp_path) -> None:
    db = FakeRuntimeDatabase()
    patch_postgres_connect(monkeypatch, db)
    sqlite_store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=sqlite_store)
    session = session_service.create_session()
    service = CarbonService(
        factor_loader=CarbonFactorLoader(build_factor_file(tmp_path)),
        session_service=session_service,
        store=sqlite_store,
        database_url="postgresql://example",
    )

    result = service.calculate(
        CalcCarbonRequest(
            session_id=session.session_id,
            period_label="2026-Q1",
            electricity_kwh=12000,
            natural_gas_m3=800,
            diesel_l=120,
        )
    )
    stored = service.get_stored_calculation(result.trace_id)

    assert stored is not None
    assert stored.session_id == session.session_id
    assert stored.total_emission_kgco2e == result.total_emission_kgco2e
    assert len(stored.breakdown) == 3
    assert len(stored.citations) == 3
