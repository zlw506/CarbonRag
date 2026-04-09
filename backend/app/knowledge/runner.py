from __future__ import annotations

from functools import lru_cache
import queue
import threading
import time


class KnowledgeTaskRunner:
    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        from app.knowledge.service import get_knowledge_service

        service = get_knowledge_service()
        service.store.reset_running_tasks()
        for task in service.store.list_admin_tasks():
            if task.status == "queued":
                self.enqueue(task.task_id)
        self._thread = threading.Thread(target=self._run, name="knowledge-task-runner", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._started = False

    def enqueue(self, task_id: str) -> None:
        self._queue.put(task_id)

    def submit(self, task_id: str) -> None:
        self.enqueue(task_id)

    def run_once(self) -> list[str]:
        from app.knowledge.service import get_knowledge_service

        service = get_knowledge_service()
        service.discover_pending_sources()
        processed: list[str] = []
        while True:
            try:
                task_id = self._queue.get_nowait()
            except queue.Empty:
                break
            task = service.store.get_task(task_id=task_id)
            if task is None:
                continue
            if task.status == "queued":
                claimed = service.store.claim_next_task()
                if claimed is None:
                    continue
                service.process_task(task_id=claimed.task_id)
                processed.append(claimed.task_id)
            elif task.status == "running":
                service.process_task(task_id=task.task_id)
                processed.append(task.task_id)
        return processed

    def _run(self) -> None:
        from app.knowledge.service import get_knowledge_service

        while not self._stop_event.is_set():
            try:
                task_id = self._queue.get(timeout=1.0)
            except queue.Empty:
                self._drain_queued_tasks()
                continue
            service = get_knowledge_service()
            task = service.store.get_task(task_id=task_id)
            if task is None:
                continue
            if task.status == "queued":
                claimed = service.store.claim_next_task()
                if claimed is None:
                    continue
                service.process_task(task_id=claimed.task_id)
            elif task.status == "running":
                service.process_task(task_id=task.task_id)

    def _drain_queued_tasks(self) -> None:
        from app.knowledge.service import get_knowledge_service

        service = get_knowledge_service()
        queued = [task.task_id for task in service.store.list_admin_tasks() if task.status == "queued"]
        for task_id in queued:
            try:
                self._queue.put_nowait(task_id)
            except queue.Full:
                break
        time.sleep(0.1)


@lru_cache(maxsize=1)
def get_knowledge_task_runner() -> KnowledgeTaskRunner:
    return KnowledgeTaskRunner()
