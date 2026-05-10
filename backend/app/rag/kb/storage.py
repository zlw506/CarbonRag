from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import get_settings
from app.knowledge import get_knowledge_service
from app.knowledge.schemas import KnowledgeItemListFilters
from app.rag.documents.chunking import recursive_chunk_text
from app.rag.documents.status import resolve_document_status
from app.rag.embeddings import RagEmbeddingUnavailable, embed_documents
from app.rag.kb.models import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, RagChunk, RagDocument
from app.rag.retrieval.dense import get_vector_store
from app.rag.vector_backend.base import VectorIndexResult
from app.rag.vector_backend.runtime import is_milvus_backend, resolve_vector_runtime
from app.retrieval.public_chunker import chunk_public_policy_document
from app.retrieval.public_corpus_loader import load_public_policy_documents
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.runtime_db.compat import connect_postgres
from app.session.store import DEFAULT_SESSION_DB_PATH


class RagKnowledgeStore:
    """RAG-Pro style KB store over CarbonRag runtime DB."""

    def __init__(self, *, database_url: str | None = None, sqlite_db_path: Path | str | None = None) -> None:
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or DEFAULT_SESSION_DB_PATH)
        self.backend_kind = get_runtime_backend_kind(self.database_url)
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_runtime_database(database_url=self.database_url, sqlite_db_path=self.sqlite_db_path)

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def _connect(self):
        if self.backend_kind == "postgresql":
            return connect_postgres(self.database_url)
        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_kb(self, *, owner_user_id: str, payload: KnowledgeBaseCreate, is_default: bool = False) -> KnowledgeBase:
        now = self.utcnow().isoformat()
        kb_id = f"kb-{uuid4().hex[:12]}"
        self._ensure_user_reference(owner_user_id=owner_user_id)
        self._execute(
            """
            INSERT INTO rag_knowledge_bases (
                kb_id, owner_user_id, name, description, visibility, retrieval_mode,
                is_default, created_at, updated_at, metadata_json
            )
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """,
            [
                kb_id,
                owner_user_id,
                payload.name,
                payload.description,
                payload.visibility,
                payload.retrieval_mode,
                is_default,
                now,
                now,
                "{}",
            ],
        )
        kb = self.get_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        if kb is None:
            raise RuntimeError("rag knowledge base create failed")
        return kb

    def ensure_default_kb(self, *, owner_user_id: str) -> KnowledgeBase:
        rows = self._select(
            """
            SELECT * FROM rag_knowledge_bases
            WHERE owner_user_id = {p} AND is_default = {p}
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            [owner_user_id, True],
        )
        if rows:
            return self._row_to_kb(rows[0])
        return self.create_kb(
            owner_user_id=owner_user_id,
            payload=KnowledgeBaseCreate(name="默认知识库", description="CarbonRag 自动创建的个人 RAG-Pro 知识库。"),
            is_default=True,
        )

    def list_kbs(self, *, owner_user_id: str) -> list[KnowledgeBase]:
        rows = self._select(
            """
            SELECT * FROM rag_knowledge_bases
            WHERE owner_user_id = {p} OR visibility IN ('shared', 'public')
            ORDER BY is_default DESC, updated_at DESC
            """,
            [owner_user_id],
        )
        return [self._row_to_kb(row) for row in rows]

    def get_kb(self, *, owner_user_id: str, kb_id: str) -> KnowledgeBase | None:
        rows = self._select(
            """
            SELECT * FROM rag_knowledge_bases
            WHERE kb_id = {p} AND (owner_user_id = {p} OR visibility IN ('shared', 'public'))
            """,
            [kb_id, owner_user_id],
        )
        return self._row_to_kb(rows[0]) if rows else None

    def update_kb(self, *, owner_user_id: str, kb_id: str, payload: KnowledgeBaseUpdate) -> KnowledgeBase:
        kb = self.get_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        if kb is None or kb.owner_user_id != owner_user_id:
            raise KeyError(kb_id)
        now = self.utcnow().isoformat()
        self._execute(
            """
            UPDATE rag_knowledge_bases
            SET name = {p}, description = {p}, visibility = {p}, retrieval_mode = {p}, updated_at = {p}
            WHERE kb_id = {p} AND owner_user_id = {p}
            """,
            [
                payload.name or kb.name,
                payload.description if payload.description is not None else kb.description,
                payload.visibility or kb.visibility,
                payload.retrieval_mode or kb.retrieval_mode,
                now,
                kb_id,
                owner_user_id,
            ],
        )
        updated = self.get_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        if updated is None:
            raise RuntimeError("rag knowledge base update failed")
        return updated

    def delete_kb(self, *, owner_user_id: str, kb_id: str) -> None:
        self._execute("DELETE FROM rag_knowledge_bases WHERE kb_id = {p} AND owner_user_id = {p}", [kb_id, owner_user_id])

    def create_document(self, *, owner_user_id: str, kb_id: str, payload: dict[str, Any]) -> RagDocument:
        kb = self.get_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        if kb is None:
            raise KeyError(kb_id)
        now = self.utcnow().isoformat()
        doc_id = f"rag-doc-{uuid4().hex[:12]}"
        knowledge_item_id = _optional_str(payload.get("knowledge_item_id"))
        file_id = _optional_str(payload.get("file_id"))
        title = _optional_str(payload.get("title"))
        source_type = _optional_str(payload.get("source_type")) or "manual"
        metadata: dict[str, Any] = {}

        if knowledge_item_id:
            item = get_knowledge_service().store.get_visible_item(owner_user_id=owner_user_id, knowledge_item_id=knowledge_item_id)
            if item is None:
                raise KeyError(knowledge_item_id)
            title = title or item.title
            file_id = file_id or item.file_id
            source_type = item.source_type
            metadata.update(
                {
                    "knowledge_item_id": item.knowledge_item_id,
                    "file_id": item.file_id,
                    "library_scope": item.library_scope,
                    "source_url": item.source_url,
                    "source": item.source,
                }
            )
        elif payload.get("text"):
            metadata["text"] = str(payload["text"])
            for key in ("source", "source_url", "library_scope", "region", "doc_type"):
                if payload.get(key) is not None:
                    metadata[key] = payload[key]

        if not title:
            title = "未命名文档"
        self._execute(
            """
            INSERT INTO rag_documents (
                doc_id, kb_id, owner_user_id, knowledge_item_id, file_id, title, source_type,
                status, parse_status, chunk_status, index_status, chunk_count, indexed_chunk_count,
                error_message, created_at, updated_at, metadata_json
            )
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """,
            [
                doc_id,
                kb_id,
                owner_user_id,
                knowledge_item_id,
                file_id,
                title,
                source_type,
                "uploaded",
                "uploaded",
                "pending",
                "pending",
                0,
                0,
                None,
                now,
                now,
                json.dumps(metadata, ensure_ascii=False),
            ],
        )
        return self.get_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)  # type: ignore[return-value]

    def list_documents(self, *, owner_user_id: str, kb_id: str) -> list[RagDocument]:
        self.require_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        rows = self._select(
            "SELECT * FROM rag_documents WHERE kb_id = {p} ORDER BY updated_at DESC",
            [kb_id],
        )
        return [self._row_to_document(row) for row in rows]

    def get_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument | None:
        self.require_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        rows = self._select("SELECT * FROM rag_documents WHERE kb_id = {p} AND doc_id = {p}", [kb_id, doc_id])
        return self._row_to_document(rows[0]) if rows else None

    def parse_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument:
        doc = self._require_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
        parse_status = "parsed"
        error = None
        if doc.knowledge_item_id:
            item = get_knowledge_service().store.get_visible_item(owner_user_id=owner_user_id, knowledge_item_id=doc.knowledge_item_id)
            if item is None:
                parse_status = "failed"
                error = "linked knowledge item is not visible"
            elif item.parse_status not in {"parsed"} and item.index_status != "indexed":
                parse_status = "failed"
                error = f"linked knowledge item parse_status={item.parse_status}"
        elif not doc.metadata.get("text"):
            parse_status = "failed"
            error = "document has no linked knowledge item or text payload"
        return self._mark_document(
            doc=doc,
            parse_status=parse_status,
            chunk_status=doc.chunk_status,
            index_status=doc.index_status,
            error_message=error,
        )

    def chunk_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument:
        doc = self._require_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
        texts: list[tuple[str, dict[str, Any], str | None]] = []
        if doc.knowledge_item_id:
            chunks = get_knowledge_service().store.list_chunks(doc.knowledge_item_id)
            for chunk in chunks:
                texts.append(
                    (
                        chunk.snippet,
                        {
                            **chunk.metadata,
                            "title": chunk.title,
                            "source_type": chunk.source_type,
                            "library_scope": chunk.library_scope,
                            "source": chunk.source,
                            "source_url": chunk.source_url,
                            "knowledge_item_id": chunk.knowledge_item_id,
                            "file_id": doc.file_id,
                        },
                        chunk.chunk_id,
                    )
                )
        elif doc.metadata.get("text"):
            for chunk in recursive_chunk_text(str(doc.metadata["text"])):
                texts.append(
                    (
                        chunk.text,
                        {
                            "title": doc.title,
                            "source_type": doc.source_type,
                            "library_scope": doc.metadata.get("library_scope"),
                            "source": doc.metadata.get("source"),
                            "source_url": doc.metadata.get("source_url"),
                            "region": doc.metadata.get("region"),
                            "doc_type": doc.metadata.get("doc_type"),
                        },
                        None,
                    )
                )

        if not texts:
            return self._mark_document(
                doc=doc,
                parse_status=doc.parse_status,
                chunk_status="failed",
                index_status=doc.index_status,
                error_message="no chunks available",
            )

        self._execute("DELETE FROM rag_chunks WHERE doc_id = {p}", [doc_id])
        now = self.utcnow().isoformat()
        for index, (text, metadata, knowledge_chunk_id) in enumerate(texts):
            payload = _chunk_metadata(metadata)
            self._execute(
                """
                INSERT INTO rag_chunks (
                    rag_chunk_id, kb_id, doc_id, owner_user_id, knowledge_chunk_id, parent_chunk_id,
                    chunk_index, text, token_estimate, page_number, sheet_name, slide_number, section_title,
                    status, vector_status, dense_vector_json, sparse_vector_json, created_at, updated_at, metadata_json
                )
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """,
                [
                    f"rag-chunk-{uuid4().hex[:12]}",
                    kb_id,
                    doc_id,
                    owner_user_id,
                    knowledge_chunk_id,
                    None,
                    index,
                    text,
                    max(1, len(text) // 2),
                    payload.get("page_number"),
                    payload.get("sheet_name"),
                    payload.get("slide_number"),
                    payload.get("section_title"),
                    "chunked",
                    "pending",
                    None,
                    None,
                    now,
                    now,
                    json.dumps(payload, ensure_ascii=False),
                ],
            )
        return self._mark_document(
            doc=doc,
            parse_status="parsed",
            chunk_status="chunked",
            index_status="pending",
            chunk_count=len(texts),
            indexed_chunk_count=0,
            error_message=None,
        )

    def index_document(self, *, owner_user_id: str, kb_id: str, doc_id: str, vector_backend: str = "memory") -> RagDocument:
        doc = self._require_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
        chunks = self.list_chunks(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
        if not chunks:
            doc = self.chunk_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
            chunks = self.list_chunks(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
        if not chunks:
            return self._mark_document(
                doc=doc,
                parse_status=doc.parse_status,
                chunk_status="failed",
                index_status="failed",
                error_message="no chunks to index",
            )
        now = self.utcnow().isoformat()
        runtime = resolve_vector_runtime(backend=vector_backend)
        try:
            embeddings = embed_documents([chunk.text for chunk in chunks]) if is_milvus_backend(vector_backend) else None
            vector_result = get_vector_store(vector_backend).index_chunks(chunks=chunks, embeddings=embeddings)
        except RagEmbeddingUnavailable as exc:
            vector_result = VectorIndexResult(
                indexed_count=0,
                backend=runtime.vector_runtime,
                available=False,
                degraded=True,
                warning=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            vector_result = VectorIndexResult(
                indexed_count=0,
                backend=runtime.vector_runtime,
                available=False,
                degraded=True,
                warning=str(exc),
            )

        if not vector_result.available or vector_result.indexed_count <= 0:
            self._update_document_metadata(
                doc_id=doc_id,
                metadata={
                    **doc.metadata,
                    "last_index_result": {
                        "vector_backend": vector_result.backend,
                        "degraded": True,
                        "warnings": [vector_result.warning or f"{vector_backend} index unavailable"],
                    },
                },
            )
            self._execute(
                "UPDATE rag_chunks SET vector_status = {p}, updated_at = {p} WHERE doc_id = {p}",
                [f"failed:{vector_backend}", now, doc_id],
            )
            return self._mark_document(
                doc=doc,
                parse_status=doc.parse_status,
                chunk_status="chunked",
                index_status="failed",
                indexed_chunk_count=0,
                error_message=vector_result.warning or f"{vector_backend} index unavailable",
            )

        if embeddings is not None:
            for index, chunk in enumerate(chunks):
                dense_vector = embeddings.dense[index] if index < len(embeddings.dense) else None
                sparse_vector = embeddings.sparse[index] if index < len(embeddings.sparse) else None
                self._execute(
                    """
                    UPDATE rag_chunks
                    SET vector_status = {p}, dense_vector_json = {p}, sparse_vector_json = {p}, updated_at = {p}
                    WHERE rag_chunk_id = {p}
                    """,
                    [
                        f"indexed:{vector_result.backend}",
                        json.dumps(dense_vector, ensure_ascii=False) if dense_vector is not None else None,
                        json.dumps(sparse_vector, ensure_ascii=False) if sparse_vector is not None else None,
                        now,
                        chunk.rag_chunk_id,
                    ],
                )
        else:
            self._execute("UPDATE rag_chunks SET vector_status = {p}, updated_at = {p} WHERE doc_id = {p}", [f"indexed:{vector_result.backend}", now, doc_id])
        self._update_document_metadata(
            doc_id=doc_id,
            metadata={
                **doc.metadata,
                "last_index_result": {
                    "vector_backend": vector_result.backend,
                    "degraded": bool(vector_result.degraded),
                    "warnings": [vector_result.warning] if vector_result.warning else [],
                },
            },
        )
        return self._mark_document(
            doc=doc,
            parse_status="parsed",
            chunk_status="chunked",
            index_status="indexed",
            indexed_chunk_count=vector_result.indexed_count,
            error_message=None,
        )

    def list_chunks(self, *, owner_user_id: str, kb_id: str, doc_id: str | None = None) -> list[RagChunk]:
        self.require_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        params: list[object] = [kb_id]
        where = "kb_id = {p}"
        if doc_id:
            where += " AND doc_id = {p}"
            params.append(doc_id)
        rows = self._select(f"SELECT * FROM rag_chunks WHERE {where} ORDER BY doc_id ASC, chunk_index ASC", params)
        return [self._row_to_chunk(row) for row in rows]

    def list_searchable_chunks(
        self,
        *,
        owner_user_id: str,
        kb_id: str | None,
        knowledge_scope: str,
        allowed_knowledge_item_ids: list[str] | None = None,
    ) -> list[RagChunk]:
        params: list[object] = []
        clauses = ["c.status = 'chunked'"]
        if kb_id:
            kb = self.get_kb(owner_user_id=owner_user_id, kb_id=kb_id)
            if kb is None:
                raise KeyError(kb_id)
            clauses.append("c.kb_id = {p}")
            params.append(kb_id)
        else:
            clauses.append("(k.owner_user_id = {p} OR k.visibility IN ('shared', 'public'))")
            params.append(owner_user_id)

        if knowledge_scope == "public":
            clauses.append("d.source_type = 'public_policy_web'")
        elif knowledge_scope == "private_sample":
            if allowed_knowledge_item_ids:
                placeholders = ", ".join(self._placeholder() for _ in allowed_knowledge_item_ids)
                clauses.append(f"d.knowledge_item_id IN ({placeholders})")
                params.extend(allowed_knowledge_item_ids)
            else:
                clauses.append("d.owner_user_id = {p}")
                params.append(owner_user_id)
        elif allowed_knowledge_item_ids:
            placeholders = ", ".join(self._placeholder() for _ in allowed_knowledge_item_ids)
            clauses.append(f"(d.source_type = 'public_policy_web' OR d.knowledge_item_id IN ({placeholders}))")
            params.extend(allowed_knowledge_item_ids)
        else:
            clauses.append("(d.owner_user_id = {p} OR d.source_type = 'public_policy_web')")
            params.append(owner_user_id)

        rows = self._select(
            f"""
            SELECT c.*
            FROM rag_chunks c
            JOIN rag_documents d ON d.doc_id = c.doc_id
            JOIN rag_knowledge_bases k ON k.kb_id = c.kb_id
            WHERE {" AND ".join(clauses)}
            ORDER BY c.updated_at DESC, c.chunk_index ASC
            """,
            params,
        )
        return [self._row_to_chunk(row) for row in rows]

    def sync_visible_knowledge(
        self,
        *,
        owner_user_id: str,
        knowledge_scope: str,
        allowed_knowledge_item_ids: list[str] | None = None,
        vector_backend: str = "memory",
    ) -> KnowledgeBase:
        kb = self.ensure_default_kb(owner_user_id=owner_user_id)
        if knowledge_scope in {"public", "mixed"}:
            self._sync_public_policy_corpus(owner_user_id=owner_user_id, kb=kb, vector_backend=vector_backend)
        filters = KnowledgeItemListFilters(
            knowledge_item_ids=allowed_knowledge_item_ids or [],
            is_enabled=True,
            session_attachable=True,
        )
        items = get_knowledge_service().list_visible_items(owner_user_id=owner_user_id, filters=filters)
        for item in items:
            if knowledge_scope == "public" and item.source_type != "public_policy_web":
                continue
            existing = self._select(
                "SELECT * FROM rag_documents WHERE kb_id = {p} AND knowledge_item_id = {p}",
                [kb.kb_id, item.knowledge_item_id],
            )
            if existing:
                continue
            doc = self.create_document(
                owner_user_id=owner_user_id,
                kb_id=kb.kb_id,
                payload={"knowledge_item_id": item.knowledge_item_id},
            )
            self.parse_document(owner_user_id=owner_user_id, kb_id=kb.kb_id, doc_id=doc.doc_id)
            self.chunk_document(owner_user_id=owner_user_id, kb_id=kb.kb_id, doc_id=doc.doc_id)
            self.index_document(owner_user_id=owner_user_id, kb_id=kb.kb_id, doc_id=doc.doc_id, vector_backend=vector_backend)
        return kb

    def _sync_public_policy_corpus(
        self,
        *,
        owner_user_id: str,
        kb: KnowledgeBase,
        vector_backend: str,
    ) -> None:
        try:
            documents = load_public_policy_documents()
        except Exception:
            return
        for public_doc in documents:
            metadata = public_doc.metadata
            existing = self._select(
                """
                SELECT * FROM rag_documents
                WHERE kb_id = {p} AND source_type = {p} AND title = {p}
                """,
                [kb.kb_id, "public_policy_web", metadata.title],
            )
            if existing:
                continue
            doc = self.create_document(
                owner_user_id=owner_user_id,
                kb_id=kb.kb_id,
                payload={
                    "title": metadata.title,
                    "text": public_doc.body,
                    "source_type": "public_policy_web",
                    "source": metadata.source,
                    "source_url": metadata.source_url,
                    "library_scope": "shared",
                    "region": metadata.region,
                    "doc_type": metadata.doc_type,
                },
            )
            self.parse_document(owner_user_id=owner_user_id, kb_id=kb.kb_id, doc_id=doc.doc_id)
            self._insert_public_policy_chunks(
                owner_user_id=owner_user_id,
                kb_id=kb.kb_id,
                doc_id=doc.doc_id,
                chunks=chunk_public_policy_document(public_doc),
            )
            self.index_document(owner_user_id=owner_user_id, kb_id=kb.kb_id, doc_id=doc.doc_id, vector_backend=vector_backend)

    def _insert_public_policy_chunks(
        self,
        *,
        owner_user_id: str,
        kb_id: str,
        doc_id: str,
        chunks,
    ) -> None:
        self._execute("DELETE FROM rag_chunks WHERE doc_id = {p}", [doc_id])
        now = self.utcnow().isoformat()
        for index, chunk in enumerate(chunks):
            payload = _chunk_metadata(
                {
                    "title": chunk.title,
                    "source_type": "public_policy_web",
                    "library_scope": "shared",
                    "source": chunk.source,
                    "source_url": chunk.source_url,
                    "region": chunk.region,
                    "doc_type": chunk.doc_type,
                    "section_title": chunk.section_title,
                }
            )
            self._execute(
                """
                INSERT INTO rag_chunks (
                    rag_chunk_id, kb_id, doc_id, owner_user_id, knowledge_chunk_id, parent_chunk_id,
                    chunk_index, text, token_estimate, page_number, sheet_name, slide_number, section_title,
                    status, vector_status, dense_vector_json, sparse_vector_json, created_at, updated_at, metadata_json
                )
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """,
                [
                    f"rag-chunk-{uuid4().hex[:12]}",
                    kb_id,
                    doc_id,
                    owner_user_id,
                    chunk.chunk_id,
                    None,
                    index,
                    chunk.snippet,
                    max(1, len(chunk.snippet) // 2),
                    chunk.page_number,
                    chunk.sheet_name,
                    chunk.slide_number,
                    chunk.section_title,
                    "chunked",
                    "pending",
                    None,
                    None,
                    now,
                    now,
                    json.dumps(payload, ensure_ascii=False),
                ],
            )
        doc = self._row_to_document(self._select("SELECT * FROM rag_documents WHERE doc_id = {p}", [doc_id])[0])
        self._mark_document(
            doc=doc,
            parse_status="parsed",
            chunk_status="chunked",
            index_status="pending",
            chunk_count=len(chunks),
            indexed_chunk_count=0,
            error_message=None,
        )

    def record_test_qa(
        self,
        *,
        owner_user_id: str,
        kb_id: str,
        query: str,
        answer: str,
        trace: dict[str, Any],
        citations: list[dict[str, Any]],
    ) -> str:
        self.require_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        run_id = f"rag-qa-{uuid4().hex[:12]}"
        self._execute(
            """
            INSERT INTO rag_test_qa_runs (run_id, kb_id, owner_user_id, query, answer, trace_json, citations_json, created_at)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """,
            [
                run_id,
                kb_id,
                owner_user_id,
                query,
                answer,
                json.dumps(trace, ensure_ascii=False),
                json.dumps(citations, ensure_ascii=False),
                self.utcnow().isoformat(),
            ],
        )
        return run_id

    def stats(self, *, owner_user_id: str | None = None) -> dict[str, int]:
        owner_clause = ""
        params: list[object] = []
        if owner_user_id is not None:
            owner_clause = " WHERE owner_user_id = {p}"
            params.append(owner_user_id)
        kb_count = self._count(f"SELECT COUNT(*) AS count FROM rag_knowledge_bases{owner_clause}", params)
        document_count = self._count(f"SELECT COUNT(*) AS count FROM rag_documents{owner_clause}", params)
        chunk_count = self._count(f"SELECT COUNT(*) AS count FROM rag_chunks{owner_clause}", params)
        indexed_count = self._count(
            f"SELECT COUNT(*) AS count FROM rag_chunks{owner_clause}{' AND' if owner_clause else ' WHERE'} vector_status LIKE 'indexed:%'",
            params,
        )
        return {
            "kb_count": kb_count,
            "document_count": document_count,
            "chunk_count": chunk_count,
            "indexed_chunk_count": indexed_count,
        }

    def require_kb(self, *, owner_user_id: str, kb_id: str) -> KnowledgeBase:
        kb = self.get_kb(owner_user_id=owner_user_id, kb_id=kb_id)
        if kb is None:
            raise KeyError(kb_id)
        return kb

    def _require_document(self, *, owner_user_id: str, kb_id: str, doc_id: str) -> RagDocument:
        doc = self.get_document(owner_user_id=owner_user_id, kb_id=kb_id, doc_id=doc_id)
        if doc is None:
            raise KeyError(doc_id)
        return doc

    def _mark_document(
        self,
        *,
        doc: RagDocument,
        parse_status: str,
        chunk_status: str,
        index_status: str,
        chunk_count: int | None = None,
        indexed_chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> RagDocument:
        now = self.utcnow().isoformat()
        status = resolve_document_status(parse_status=parse_status, chunk_status=chunk_status, index_status=index_status)
        self._execute(
            """
            UPDATE rag_documents
            SET status = {p}, parse_status = {p}, chunk_status = {p}, index_status = {p},
                chunk_count = {p}, indexed_chunk_count = {p}, error_message = {p}, updated_at = {p}
            WHERE doc_id = {p}
            """,
            [
                status,
                parse_status,
                chunk_status,
                index_status,
                doc.chunk_count if chunk_count is None else chunk_count,
                doc.indexed_chunk_count if indexed_chunk_count is None else indexed_chunk_count,
                error_message,
                now,
                doc.doc_id,
            ],
        )
        return self.get_document(owner_user_id=doc.owner_user_id or "", kb_id=doc.kb_id, doc_id=doc.doc_id) or doc

    def _count(self, query: str, params: list[object]) -> int:
        rows = self._select(query, params)
        return int(rows[0]["count"]) if rows else 0

    def _select(self, query: str, params: list[object]) -> list[dict[str, Any]]:
        sql = self._format_query(query)
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    return [dict(row) for row in cursor.fetchall()]
            rows = connection.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def _execute(self, query: str, params: list[object]) -> None:
        sql = self._format_query(query)
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                connection.commit()
                return
            connection.execute(sql, params)
            connection.commit()

    def _ensure_user_reference(self, *, owner_user_id: str) -> None:
        if not owner_user_id:
            raise ValueError("owner_user_id is required for RAG knowledge base persistence")
        rows = self._select("SELECT user_id FROM users WHERE user_id = {p}", [owner_user_id])
        if rows:
            return
        now = self.utcnow().isoformat()
        self._execute(
            """
            INSERT INTO users (user_id, username, password_hash, role, is_active, password_must_change, created_at, updated_at)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """,
            [
                owner_user_id,
                owner_user_id,
                "rag-kb-shadow-user",
                "user",
                True,
                False,
                now,
                now,
            ],
        )

    def _update_document_metadata(self, *, doc_id: str, metadata: dict[str, Any]) -> None:
        self._execute(
            "UPDATE rag_documents SET metadata_json = {p} WHERE doc_id = {p}",
            [json.dumps(metadata, ensure_ascii=False), doc_id],
        )

    def _format_query(self, query: str) -> str:
        return query.replace("{p}", self._placeholder())

    def _placeholder(self) -> str:
        return "%s" if self.backend_kind == "postgresql" else "?"

    @staticmethod
    def _row_to_kb(row: dict[str, Any]) -> KnowledgeBase:
        payload = dict(row)
        payload["metadata"] = _parse_json_object(payload.pop("metadata_json", None))
        payload["is_default"] = bool(payload.get("is_default"))
        return KnowledgeBase.model_validate(payload)

    @staticmethod
    def _row_to_document(row: dict[str, Any]) -> RagDocument:
        payload = dict(row)
        metadata = _parse_json_object(payload.pop("metadata_json", None))
        payload["metadata"] = metadata
        last_index = metadata.get("last_index_result") if isinstance(metadata, dict) else None
        if isinstance(last_index, dict):
            payload["vector_backend"] = last_index.get("vector_backend")
            payload["degraded"] = bool(last_index.get("degraded"))
            warnings = last_index.get("warnings")
            payload["index_warnings"] = warnings if isinstance(warnings, list) else []
        return RagDocument.model_validate(payload)

    @staticmethod
    def _row_to_chunk(row: dict[str, Any]) -> RagChunk:
        payload = dict(row)
        payload["metadata"] = _parse_json_object(payload.pop("metadata_json", None))
        payload["dense_vector"] = _parse_json_list(payload.pop("dense_vector_json", None))
        payload["sparse_vector"] = _parse_json_object(payload.pop("sparse_vector_json", None)) or None
        return RagChunk.model_validate(payload)


def _chunk_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    payload = dict(metadata)
    for key in ("page_number", "slide_number"):
        if payload.get(key) in ("", None):
            payload[key] = None
        elif payload.get(key) is not None:
            try:
                payload[key] = int(payload[key])
            except (TypeError, ValueError):
                payload[key] = None
    for key in ("sheet_name", "section_title"):
        payload[key] = _optional_str(payload.get(key))
    return payload


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_json_object(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_json_list(value: Any) -> list[float] | None:
    if not value:
        return None
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None

