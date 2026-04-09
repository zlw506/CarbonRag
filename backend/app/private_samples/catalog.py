from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from app.knowledge import get_knowledge_service
from app.knowledge.schemas import KnowledgeItem
from app.retrieval.private_corpus_loader import load_private_sample_manifest, resolve_private_corpus_dir
from app.retrieval.private_schemas import PrivateSampleCatalogItem


def _ensure_shared_knowledge_items_loaded() -> None:
    service = get_knowledge_service()
    corpus_dir = resolve_private_corpus_dir()
    for metadata in load_private_sample_manifest():
        doc_path = corpus_dir / metadata.filepath
        if not doc_path.exists():
            continue

        source_hash = _compute_sha256(doc_path)
        source_mtime = str(doc_path.stat().st_mtime)
        existing = service.store.get_item_by_source(
            owner_user_id=None,
            library_scope="shared",
            source_type="private_sample_repo",
            source_ref=metadata.doc_id,
        )
        should_refresh = (
            existing is None
            or existing.source_hash != source_hash
            or existing.source_mtime != source_mtime
            or existing.parse_status != "parsed"
            or existing.ingest_status != "ingested"
            or existing.index_status != "indexed"
        )
        item = KnowledgeItem(
            knowledge_item_id=metadata.doc_id,
            owner_user_id=None,
            library_scope="shared",
            source_type="private_sample_repo",
            source_ref=metadata.doc_id,
            file_id=None,
            source="管理员共享样例",
            source_url=None,
            sample_type=metadata.sample_type,
            business_topic=metadata.business_topic,
            title=metadata.title,
            mime_type="text/markdown" if metadata.sample_type == "doc" else "text/csv",
            storage_path=str(doc_path),
            parse_status="pending" if should_refresh else (existing.parse_status if existing else "pending"),
            ingest_status="pending" if should_refresh else (existing.ingest_status if existing else "pending"),
            index_status="stale" if should_refresh and existing else "pending" if should_refresh else (existing.index_status if existing else "pending"),
            is_enabled=existing.is_enabled if existing else True,
            session_attachable=existing.session_attachable if existing else metadata.session_attachable,
            source_hash=source_hash,
            source_mtime=source_mtime,
            last_error=None if should_refresh else (existing.last_error if existing else None),
            created_at=existing.created_at if existing else service.store.utcnow(),
            updated_at=service.store.utcnow(),
            last_indexed_at=existing.last_indexed_at if existing else None,
        )
        service.store.upsert_item(item=item)
        if should_refresh:
            task = service.store.create_task(
                task_id=f"ktask-{uuid4().hex[:12]}",
                knowledge_item_id=item.knowledge_item_id,
                owner_user_id=None,
                requested_by_user_id=None,
                task_type="rebuild",
                summary="共享样例已加入重建队列。",
            )
            service.store.update_task_status(
                task_id=task.task_id,
                status="running",
                summary=task.summary,
                started_at=service.store.utcnow(),
            )
            service.process_task(task_id=task.task_id)
    try:
        service.run_queued_tasks()
    except Exception:
        # Catalog visibility should still work even if a refresh task failed.
        pass


def list_attachable_private_sample_catalog(
    *,
    database_url: str | None = None,
    sqlite_db_path=None,
) -> list[PrivateSampleCatalogItem]:
    del database_url, sqlite_db_path
    _ensure_shared_knowledge_items_loaded()
    service = get_knowledge_service()
    items: list[PrivateSampleCatalogItem] = []
    for item in service.list_shared_items(source_type="private_sample_repo"):
        if not item.is_enabled or not item.session_attachable:
            continue
        items.append(
            PrivateSampleCatalogItem(
                doc_id=item.knowledge_item_id,
                title=item.title,
                source_type=item.source_type,
                sample_type=item.sample_type or "doc",
                business_topic=item.business_topic or "project_background",
                session_attachable=item.session_attachable,
            )
        )
    return items


def list_admin_private_sample_catalog(
    *,
    database_url: str | None = None,
    sqlite_db_path=None,
) -> list[dict]:
    del database_url, sqlite_db_path
    _ensure_shared_knowledge_items_loaded()
    service = get_knowledge_service()
    items: list[dict] = []
    for item in service.list_shared_items(source_type="private_sample_repo"):
        items.append(
            {
                "doc_id": item.knowledge_item_id,
                "title": item.title,
                "source_type": item.source_type,
                "sample_type": item.sample_type or "doc",
                "business_topic": item.business_topic or "project_background",
                "session_attachable": item.session_attachable,
                "is_enabled": item.is_enabled,
                "knowledge_item_id": item.knowledge_item_id,
                "library_scope": item.library_scope,
                "parse_status": item.parse_status,
                "ingest_status": item.ingest_status,
                "index_status": item.index_status,
                "updated_at": item.updated_at,
            }
        )
    return items


def refresh_private_sample_catalog() -> None:
    _ensure_shared_knowledge_items_loaded()


def _compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
