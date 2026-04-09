from datetime import datetime, timezone
from uuid import uuid4

from app.private_samples.catalog import list_attachable_private_sample_catalog
from app.schemas.ask import AskCitation, AskSourceSummary, AskStatus, KnowledgeScope
from app.session.schemas import SessionDetail, SessionMessage, SessionSummary, UploadedFile
from app.session.store import SessionStore, get_session_store

DEFAULT_TITLE_PREFIX = "新对话"
DEFAULT_CONTEXT_TURNS = 4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SessionService:
    def __init__(self, store: SessionStore | None = None) -> None:
        self.store = store or get_session_store()

    def create_session(self, *, owner_user_id: str, title: str | None = None) -> SessionSummary:
        created_at = utcnow()
        session_id = f"session-{uuid4().hex[:12]}"
        session_title = title or f"{DEFAULT_TITLE_PREFIX} {created_at.astimezone().strftime('%Y-%m-%d %H:%M')}"
        return self.store.create_session(
            session_id=session_id,
            owner_user_id=owner_user_id,
            title=session_title,
            created_at=created_at.isoformat(),
        )

    def list_sessions(self, *, owner_user_id: str) -> list[SessionSummary]:
        return self.store.list_sessions(owner_user_id=owner_user_id)

    def get_session(self, *, owner_user_id: str, session_id: str) -> SessionDetail | None:
        return self.store.get_session(owner_user_id=owner_user_id, session_id=session_id)

    def require_session(self, *, owner_user_id: str, session_id: str) -> SessionDetail:
        session = self.get_session(owner_user_id=owner_user_id, session_id=session_id)
        if session is None:
            raise KeyError(f"Unknown session: {session_id}")
        return session

    def update_session_title(self, *, owner_user_id: str, session_id: str, title: str) -> SessionSummary | None:
        self.require_session(owner_user_id=owner_user_id, session_id=session_id)
        return self.store.update_session_title(
            session_id=session_id,
            title=title,
            updated_at=utcnow().isoformat(),
        )

    def build_session_context(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        max_turns: int = DEFAULT_CONTEXT_TURNS,
    ) -> list[dict[str, str]]:
        self.require_session(owner_user_id=owner_user_id, session_id=session_id)
        recent_messages = self.store.list_recent_messages(session_id=session_id, limit=max_turns * 4)
        conversation_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in recent_messages
            if message.role in {"user", "assistant"}
        ]
        return conversation_messages[-(max_turns * 2):]

    def record_exchange(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        user_content: str,
        assistant_content: str,
        assistant_status: AskStatus,
        trace_id: str,
        citations: list[AskCitation],
        knowledge_scope: KnowledgeScope = "public",
        source_summary: AskSourceSummary | None = None,
    ) -> tuple[SessionMessage, SessionMessage]:
        self.require_session(owner_user_id=owner_user_id, session_id=session_id)
        timestamp = utcnow()
        user_message = self.store.append_message(
            session_id=session_id,
            message_id=f"msg-{uuid4().hex[:12]}",
            role="user",
            content=user_content,
            created_at=timestamp.isoformat(),
        )
        assistant_message = self.store.append_message(
            session_id=session_id,
            message_id=f"msg-{uuid4().hex[:12]}",
            role="assistant",
            content=assistant_content,
            created_at=utcnow().isoformat(),
            status=assistant_status,
            trace_id=trace_id,
            citations=citations,
        )
        effective_source_summary = source_summary or AskSourceSummary(
            knowledge_scope=knowledge_scope,
            public_policy_count=sum(1 for citation in citations if citation.source_type == "public_policy"),
            private_sample_count=sum(1 for citation in citations if citation.source_type == "private_sample"),
            total_citation_count=len(citations),
        )
        self.store.update_session_runtime_state(
            session_id=session_id,
            updated_at=utcnow().isoformat(),
            knowledge_scope_last_used=knowledge_scope,
            source_summary=effective_source_summary,
        )
        return user_message, assistant_message

    def maybe_promote_title_from_first_question(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        question: str,
    ) -> SessionSummary | None:
        session = self.get_session(owner_user_id=owner_user_id, session_id=session_id)
        if session is None:
            return None
        if not session.title.startswith(DEFAULT_TITLE_PREFIX):
            return session
        if len(session.messages) > 2:
            return session

        trimmed = question.strip()
        if not trimmed:
            return session

        max_length = 24
        promoted = trimmed if len(trimmed) <= max_length else f"{trimmed[:max_length].rstrip()}..."
        return self.update_session_title(owner_user_id=owner_user_id, session_id=session_id, title=promoted)

    def record_system_message(self, *, owner_user_id: str, session_id: str, content: str) -> SessionMessage:
        self.require_session(owner_user_id=owner_user_id, session_id=session_id)
        return self.store.append_message(
            session_id=session_id,
            message_id=f"msg-{uuid4().hex[:12]}",
            role="system",
            content=content,
            created_at=utcnow().isoformat(),
        )

    def record_uploaded_file(
        self,
        *,
        owner_user_id: str,
        file_id: str | None = None,
        session_id: str,
        filename: str,
        size: int,
        mime_type: str,
        storage_path: str,
    ) -> UploadedFile:
        self.require_session(owner_user_id=owner_user_id, session_id=session_id)
        stored_at = utcnow().isoformat()
        return self.store.create_uploaded_file(
            file_id=file_id or f"file-{uuid4().hex[:12]}",
            session_id=session_id,
            filename=filename,
            size=size,
            mime_type=mime_type,
            stored_at=stored_at,
            storage_path=storage_path,
        )

    def list_private_sample_catalog(self):
        return list_attachable_private_sample_catalog(
            database_url=getattr(self.store, "database_url", None),
            sqlite_db_path=getattr(self.store, "db_path", None),
        )

    def replace_attached_private_samples(self, *, owner_user_id: str, session_id: str, doc_ids: list[str]) -> None:
        self.require_session(owner_user_id=owner_user_id, session_id=session_id)
        catalog = {item.doc_id: item for item in self.list_private_sample_catalog()}
        normalized: list[str] = []
        for doc_id in doc_ids:
            candidate = doc_id.strip()
            if not candidate:
                continue
            if candidate not in catalog:
                raise ValueError(f"Unknown private sample: {candidate}")
            normalized.append(candidate)
        deduplicated = list(dict.fromkeys(normalized))
        self.store.replace_attached_private_samples(
            session_id=session_id,
            doc_ids=deduplicated,
            attached_at=utcnow().isoformat(),
        )

    def list_attached_private_sample_ids(self, *, owner_user_id: str, session_id: str) -> list[str]:
        self.require_session(owner_user_id=owner_user_id, session_id=session_id)
        return self.store.list_attached_private_sample_ids(session_id=session_id)


def get_session_service() -> SessionService:
    return SessionService()
