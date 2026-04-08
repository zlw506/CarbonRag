from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import REPO_ROOT
from app.schemas.ask import AskCitation, AskSourceSummary, AskStatus, KnowledgeScope
from app.session.schemas import SessionDetail, SessionMessage, SessionSummary, UploadedFile

RUNTIME_DIR = REPO_ROOT / "data" / "outputs" / "runtime"
DEFAULT_SESSION_DB_PATH = RUNTIME_DIR / "carbonrag.sqlite3"


class SessionStore(ABC):
    @abstractmethod
    def create_session(self, *, session_id: str, title: str, created_at: str) -> SessionSummary:
        raise NotImplementedError

    @abstractmethod
    def list_sessions(self) -> list[SessionSummary]:
        raise NotImplementedError

    @abstractmethod
    def get_session(self, session_id: str) -> SessionDetail | None:
        raise NotImplementedError

    @abstractmethod
    def update_session_title(self, *, session_id: str, title: str, updated_at: str) -> SessionSummary | None:
        raise NotImplementedError

    @abstractmethod
    def update_session_runtime_state(
        self,
        *,
        session_id: str,
        updated_at: str,
        knowledge_scope_last_used: KnowledgeScope,
        source_summary: AskSourceSummary,
    ) -> SessionSummary | None:
        raise NotImplementedError

    @abstractmethod
    def append_message(
        self,
        *,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        created_at: str,
        status: AskStatus | None = None,
        trace_id: str | None = None,
        citations: list[AskCitation] | None = None,
    ) -> SessionMessage:
        raise NotImplementedError

    @abstractmethod
    def list_recent_messages(self, *, session_id: str, limit: int) -> list[SessionMessage]:
        raise NotImplementedError

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_uploaded_file(
        self,
        *,
        file_id: str,
        session_id: str,
        filename: str,
        size: int,
        mime_type: str,
        stored_at: str,
        storage_path: str,
    ) -> UploadedFile:
        raise NotImplementedError

    @abstractmethod
    def replace_attached_private_samples(self, *, session_id: str, doc_ids: list[str], attached_at: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_attached_private_sample_ids(self, *, session_id: str) -> list[str]:
        raise NotImplementedError
