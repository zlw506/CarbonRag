from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterator

from app.ai_runtime.providers.base import ChatProviderError

RETRY_BACKOFF_SECONDS = [0.8, 1.6, 3.2, 5.0, 8.0]


def is_retryable_provider_error(exc: ChatProviderError, *, first_token_received: bool) -> bool:
    if exc.reason in {"network_error", "timeout"}:
        return True
    if exc.status_code in {408, 409, 429}:
        return True
    if exc.status_code is not None and exc.status_code >= 500:
        return True
    if not first_token_received and exc.reason in {"invalid_response", "empty_content"}:
        return True
    return False


def get_retry_delay(attempt: int) -> float:
    base = RETRY_BACKOFF_SECONDS[min(max(attempt - 1, 0), len(RETRY_BACKOFF_SECONDS) - 1)]
    return base + random.uniform(0.05, 0.25)


@dataclass
class BufferedStreamEvent:
    seq: int
    event: str
    data: dict


@dataclass
class ActiveStreamSession:
    request_group_id: str
    owner_user_id: str
    session_id: str
    user_message_id: str
    assistant_message_id: str
    trace_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    events: list[BufferedStreamEvent] = field(default_factory=list)
    is_done: bool = False
    has_first_answer_token: bool = False
    attempt: int = 1
    title_updated: bool = False
    provider_ref: str = "builtin:carbonrag-cloud"
    _next_seq: int = 1
    _condition: threading.Condition = field(default_factory=threading.Condition)

    def append(self, *, event: str, data: dict) -> None:
        with self._condition:
            buffered = BufferedStreamEvent(seq=self._next_seq, event=event, data=data)
            self._next_seq += 1
            self.events.append(buffered)
            self._condition.notify_all()

    def complete(self) -> None:
        with self._condition:
            self.is_done = True
            self.completed_at = datetime.now(timezone.utc)
            self._condition.notify_all()

    def subscribe(self, *, after_cursor: int = 0) -> Iterator[BufferedStreamEvent]:
        index = 0
        with self._condition:
            while index < len(self.events) and self.events[index].seq <= after_cursor:
                index += 1

        while True:
            with self._condition:
                while index >= len(self.events) and not self.is_done:
                    self._condition.wait(timeout=10.0)
                if index < len(self.events):
                    event = self.events[index]
                    index += 1
                elif self.is_done:
                    break
                else:
                    continue
            yield event


class ActiveStreamRegistry:
    def __init__(self) -> None:
        self._streams: dict[str, ActiveStreamSession] = {}
        self._lock = threading.Lock()
        self._retention = timedelta(minutes=10)

    def get(self, request_group_id: str) -> ActiveStreamSession | None:
        self._cleanup()
        with self._lock:
            return self._streams.get(request_group_id)

    def create(
        self,
        *,
        request_group_id: str,
        owner_user_id: str,
        session_id: str,
        user_message_id: str,
        assistant_message_id: str,
        trace_id: str,
    ) -> ActiveStreamSession:
        self._cleanup()
        with self._lock:
            session = ActiveStreamSession(
                request_group_id=request_group_id,
                owner_user_id=owner_user_id,
                session_id=session_id,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                trace_id=trace_id,
            )
            self._streams[request_group_id] = session
            return session

    def _cleanup(self) -> None:
        threshold = datetime.now(timezone.utc) - self._retention
        with self._lock:
            expired = [
                request_group_id
                for request_group_id, stream in self._streams.items()
                if stream.completed_at is not None and stream.completed_at < threshold
            ]
            for request_group_id in expired:
                self._streams.pop(request_group_id, None)


_registry = ActiveStreamRegistry()


def get_active_stream_registry() -> ActiveStreamRegistry:
    return _registry
