import sqlite3

CORE_TABLES = (
    "sessions",
    "messages",
    "files",
    "session_private_samples",
    "feedback_entries",
    "carbon_calculations",
    "reports",
    "report_sources",
)

SQLITE_SCHEMA_SCRIPT = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    knowledge_scope_last_used TEXT,
    source_summary_json TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    message_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL UNIQUE,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT,
    trace_id TEXT,
    citations_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS files (
    file_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL UNIQUE,
    session_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    stored_at TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS session_private_samples (
    attachment_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    attached_at TEXT NOT NULL,
    UNIQUE (session_id, doc_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback_entries (
    feedback_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_id TEXT NOT NULL UNIQUE,
    target_type TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    session_id TEXT,
    rating TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_calculations (
    calculation_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL UNIQUE,
    session_id TEXT,
    period_label TEXT,
    electricity_kwh REAL NOT NULL,
    natural_gas_m3 REAL NOT NULL,
    diesel_l REAL NOT NULL,
    total_emission_kgco2e REAL NOT NULL,
    breakdown_json TEXT NOT NULL,
    citations_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    report_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL UNIQUE,
    session_id TEXT NOT NULL,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    output_format TEXT NOT NULL,
    citations_json TEXT NOT NULL,
    source_summary_json TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_sources (
    source_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    label TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session_seq
    ON messages(session_id, message_seq);
CREATE INDEX IF NOT EXISTS idx_files_session_seq
    ON files(session_id, file_seq);
CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
    ON sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_private_samples_session_seq
    ON session_private_samples(session_id, attachment_seq DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_entries_trace
    ON feedback_entries(trace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_carbon_calculations_session_created_at
    ON carbon_calculations(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_session_updated_at
    ON reports(session_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_sources_report_order
    ON report_sources(report_id, order_index ASC);
"""

POSTGRES_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        knowledge_scope_last_used TEXT,
        source_summary_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        message_seq BIGSERIAL PRIMARY KEY,
        message_id TEXT NOT NULL UNIQUE,
        session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        status TEXT,
        trace_id TEXT,
        citations_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS files (
        file_seq BIGSERIAL PRIMARY KEY,
        file_id TEXT NOT NULL UNIQUE,
        session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        filename TEXT NOT NULL,
        size BIGINT NOT NULL,
        mime_type TEXT NOT NULL,
        stored_at TEXT NOT NULL,
        storage_path TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS session_private_samples (
        attachment_seq BIGSERIAL PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        doc_id TEXT NOT NULL,
        attached_at TEXT NOT NULL,
        UNIQUE (session_id, doc_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS feedback_entries (
        feedback_seq BIGSERIAL PRIMARY KEY,
        feedback_id TEXT NOT NULL UNIQUE,
        target_type TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        session_id TEXT,
        rating TEXT NOT NULL,
        comment TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS carbon_calculations (
        calculation_seq BIGSERIAL PRIMARY KEY,
        trace_id TEXT NOT NULL UNIQUE,
        session_id TEXT,
        period_label TEXT,
        electricity_kwh DOUBLE PRECISION NOT NULL,
        natural_gas_m3 DOUBLE PRECISION NOT NULL,
        diesel_l DOUBLE PRECISION NOT NULL,
        total_emission_kgco2e DOUBLE PRECISION NOT NULL,
        breakdown_json TEXT NOT NULL,
        citations_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reports (
        report_seq BIGSERIAL PRIMARY KEY,
        report_id TEXT NOT NULL UNIQUE,
        session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        report_type TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        output_format TEXT NOT NULL,
        citations_json TEXT NOT NULL,
        source_summary_json TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS report_sources (
        source_seq BIGSERIAL PRIMARY KEY,
        report_id TEXT NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
        source_type TEXT NOT NULL,
        source_ref TEXT NOT NULL,
        label TEXT NOT NULL,
        order_index INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_messages_session_seq ON messages(session_id, message_seq)",
    "CREATE INDEX IF NOT EXISTS idx_files_session_seq ON files(session_id, file_seq)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_private_samples_session_seq ON session_private_samples(session_id, attachment_seq DESC)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_entries_trace ON feedback_entries(trace_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_carbon_calculations_session_created_at ON carbon_calculations(session_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_reports_session_updated_at ON reports(session_id, updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_report_sources_report_order ON report_sources(report_id, order_index ASC)",
)


def ensure_sqlite_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SQLITE_SCHEMA_SCRIPT)
    _ensure_sqlite_column(connection, "sessions", "knowledge_scope_last_used", "TEXT")
    _ensure_sqlite_column(connection, "sessions", "source_summary_json", "TEXT")


def _ensure_sqlite_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing_columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in existing_columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_postgres_schema(connection) -> None:
    with connection.cursor() as cursor:
        for statement in POSTGRES_SCHEMA_STATEMENTS:
            cursor.execute(statement)
