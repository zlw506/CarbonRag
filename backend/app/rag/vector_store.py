from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from app.rag.contracts import ChunkRecord, EmbeddingRecord
from app.retrieval.mixed_retriever import MixedScopeRetriever, get_mixed_scope_retriever
from app.retrieval.private_retriever import PrivateSampleRetriever, get_private_sample_retriever
from app.retrieval.public_retriever import PublicPolicyRetriever, get_public_policy_retriever
from app.retrieval.schemas import RetrievedChunk

VectorStoreHealthStatus = Literal["ok", "degraded", "disabled", "error"]
VectorStoreFilters = dict[str, Any]


class VectorStoreHealth(BaseModel):
    backend: str
    status: VectorStoreHealthStatus
    available: bool
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorStoreUpsertResult(BaseModel):
    backend: str
    upserted_count: int = 0
    skipped_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorStoreSearchResult(BaseModel):
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    total_hits: int = 0
    backend: str | None = None
    adapter_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorStoreAdapter(Protocol):
    def healthcheck(self) -> VectorStoreHealth:
        ...

    def upsert_chunks(
        self,
        *,
        chunks: list[ChunkRecord],
        embeddings: list[EmbeddingRecord] | None = None,
    ) -> VectorStoreUpsertResult:
        ...

    def search(
        self,
        *,
        question: str | None = None,
        query: str | None = None,
        filters: VectorStoreFilters | None = None,
        query_embedding: list[float] | None = None,
        top_k: int = 5,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> VectorStoreSearchResult:
        ...

    def delete_by_document(self, *, document_id: str) -> VectorStoreUpsertResult:
        ...


class DisabledVectorStoreAdapter:
    backend = "disabled"

    def __init__(self, *, reason: str = "vector_store_disabled") -> None:
        self.reason = reason

    def healthcheck(self) -> VectorStoreHealth:
        return VectorStoreHealth(
            backend=self.backend,
            status="disabled",
            available=False,
            reason=self.reason,
        )

    def upsert_chunks(
        self,
        *,
        chunks: list[ChunkRecord],
        embeddings: list[EmbeddingRecord] | None = None,
    ) -> VectorStoreUpsertResult:
        return VectorStoreUpsertResult(
            backend=self.backend,
            upserted_count=0,
            skipped_count=len(chunks),
            metadata={"reason": self.reason, "embedding_count": len(embeddings or [])},
        )

    def search(
        self,
        *,
        question: str | None = None,
        query: str | None = None,
        filters: VectorStoreFilters | None = None,
        query_embedding: list[float] | None = None,
        top_k: int = 5,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> VectorStoreSearchResult:
        resolved_query = _resolve_query(question=question, query=query)
        return VectorStoreSearchResult(
            chunks=[],
            total_hits=0,
            backend=self.backend,
            adapter_name=type(self).__name__,
            metadata={
                "status": "disabled",
                "reason": self.reason,
                "query_length": len(resolved_query),
                "embedding_seen": query_embedding is not None,
                "top_k": top_k,
                "filters": filters or {},
                "allowed_knowledge_item_count": len(allowed_knowledge_item_ids or set()),
            },
        )

    def delete_by_document(self, *, document_id: str) -> VectorStoreUpsertResult:
        return VectorStoreUpsertResult(
            backend=self.backend,
            upserted_count=0,
            skipped_count=0,
            metadata={"reason": self.reason, "document_id": document_id},
        )


class CurrentVectorStoreAdapter:
    backend = "current"

    def __init__(
        self,
        *,
        public_retriever: PublicPolicyRetriever | None = None,
        private_retriever: PrivateSampleRetriever | None = None,
        mixed_retriever: MixedScopeRetriever | None = None,
    ) -> None:
        self.public_retriever = public_retriever or get_public_policy_retriever()
        self.private_retriever = private_retriever or get_private_sample_retriever()
        self.mixed_retriever = mixed_retriever or get_mixed_scope_retriever()

    def healthcheck(self) -> VectorStoreHealth:
        try:
            public_chunk_count = _count_retriever_chunks(self.public_retriever)
            private_chunk_count = _count_retriever_chunks(self.private_retriever)
            return VectorStoreHealth(
                backend=self.backend,
                status="ok",
                available=True,
                metadata={
                    "adapter_name": type(self).__name__,
                    "storage": "in_memory_bm25",
                    "public_chunk_count": public_chunk_count,
                    "private_chunk_count": private_chunk_count,
                },
            )
        except Exception as exc:  # noqa: BLE001
            return VectorStoreHealth(
                backend=self.backend,
                status="degraded",
                available=False,
                reason=str(exc),
                metadata={"adapter_name": type(self).__name__, "error_type": type(exc).__name__},
            )

    def upsert_chunks(
        self,
        *,
        chunks: list[ChunkRecord],
        embeddings: list[EmbeddingRecord] | None = None,
    ) -> VectorStoreUpsertResult:
        return VectorStoreUpsertResult(
            backend=self.backend,
            upserted_count=0,
            skipped_count=len(chunks),
            metadata={
                "adapter_name": type(self).__name__,
                "reason": "current_adapter_is_read_through",
                "embedding_count": len(embeddings or []),
            },
        )

    def search(
        self,
        *,
        question: str | None = None,
        query: str | None = None,
        filters: VectorStoreFilters | None = None,
        query_embedding: list[float] | None = None,
        top_k: int = 5,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> VectorStoreSearchResult:
        resolved_query = _resolve_query(question=question, query=query)
        resolved_filters = filters or {}
        knowledge_scope = str(resolved_filters.get("knowledge_scope") or "mixed")
        allowed_ids = _resolve_allowed_ids(
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
            filters=resolved_filters,
        )

        if knowledge_scope == "public":
            result = self.public_retriever.search(
                question=resolved_query,
                top_k=top_k,
                knowledge_scope="public",
                region=_optional_str(resolved_filters.get("region")),
                doc_type=_optional_str(resolved_filters.get("doc_type")),
            )
        elif knowledge_scope == "private_sample":
            result = self.private_retriever.search(
                question=resolved_query,
                top_k=top_k,
                knowledge_scope="private_sample",
                allowed_knowledge_item_ids=allowed_ids,
                business_topic=_optional_str(resolved_filters.get("business_topic")),
            )
        else:
            result = self.mixed_retriever.search(
                question=resolved_query,
                top_k=top_k,
                allowed_knowledge_item_ids=allowed_ids,
            )

        return VectorStoreSearchResult(
            chunks=result.hits,
            total_hits=result.total_hits,
            backend=self.backend,
            adapter_name=type(self).__name__,
            metadata={
                "status": "ok",
                "adapter_name": type(self).__name__,
                "storage": "in_memory_bm25",
                "knowledge_scope": knowledge_scope,
                "top_k": top_k,
                "query_embedding_seen": query_embedding is not None,
                "allowed_knowledge_item_count": len(allowed_ids or set()),
            },
        )

    def delete_by_document(self, *, document_id: str) -> VectorStoreUpsertResult:
        return VectorStoreUpsertResult(
            backend=self.backend,
            upserted_count=0,
            skipped_count=0,
            metadata={
                "adapter_name": type(self).__name__,
                "reason": "current_adapter_is_read_through",
                "document_id": document_id,
            },
        )


class FakeVectorStoreAdapter:
    backend = "fake"

    def __init__(
        self,
        *,
        chunks: list[RetrievedChunk] | None = None,
        status: VectorStoreHealthStatus = "ok",
        available: bool = True,
    ) -> None:
        self.chunks = chunks or []
        self.status = status
        self.available = available

    def healthcheck(self) -> VectorStoreHealth:
        return VectorStoreHealth(
            backend=self.backend,
            status=self.status,
            available=self.available,
            reason=None if self.available else "fake_vector_store_unavailable",
            metadata={"adapter_name": type(self).__name__, "chunk_count": len(self.chunks)},
        )

    def upsert_chunks(
        self,
        *,
        chunks: list[ChunkRecord],
        embeddings: list[EmbeddingRecord] | None = None,
    ) -> VectorStoreUpsertResult:
        self.chunks.extend(_retrieved_chunk_from_chunk_record(chunk) for chunk in chunks)
        return VectorStoreUpsertResult(
            backend=self.backend,
            upserted_count=len(chunks),
            skipped_count=0,
            metadata={"adapter_name": type(self).__name__, "embedding_count": len(embeddings or [])},
        )

    def search(
        self,
        *,
        question: str | None = None,
        query: str | None = None,
        filters: VectorStoreFilters | None = None,
        query_embedding: list[float] | None = None,
        top_k: int = 5,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> VectorStoreSearchResult:
        resolved_query = _resolve_query(question=question, query=query)
        allowed_ids = _resolve_allowed_ids(
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
            filters=filters or {},
        )
        candidates = self.chunks
        if allowed_ids is not None:
            candidates = [chunk for chunk in candidates if chunk.knowledge_item_id in allowed_ids]
        selected = candidates[:top_k]
        return VectorStoreSearchResult(
            chunks=selected,
            total_hits=len(selected),
            backend=self.backend,
            adapter_name=type(self).__name__,
            metadata={
                "status": self.status,
                "adapter_name": type(self).__name__,
                "query": resolved_query,
                "query_embedding_seen": query_embedding is not None,
                "top_k": top_k,
                "allowed_knowledge_item_count": len(allowed_ids or set()),
            },
        )

    def delete_by_document(self, *, document_id: str) -> VectorStoreUpsertResult:
        before_count = len(self.chunks)
        self.chunks = [chunk for chunk in self.chunks if chunk.doc_id != document_id]
        deleted_count = before_count - len(self.chunks)
        return VectorStoreUpsertResult(
            backend=self.backend,
            upserted_count=0,
            skipped_count=0,
            metadata={"adapter_name": type(self).__name__, "deleted_count": deleted_count},
        )


def _resolve_query(*, question: str | None, query: str | None) -> str:
    resolved = (question if question is not None else query) or ""
    return resolved.strip()


def _resolve_allowed_ids(
    *,
    allowed_knowledge_item_ids: set[str] | None,
    filters: VectorStoreFilters,
) -> set[str] | None:
    if allowed_knowledge_item_ids is not None:
        return allowed_knowledge_item_ids
    raw_value = filters.get("allowed_knowledge_item_ids")
    if raw_value is None:
        return None
    if isinstance(raw_value, str):
        return {raw_value}
    if isinstance(raw_value, (list, set, tuple)):
        return {str(item) for item in raw_value if str(item).strip()}
    return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _count_retriever_chunks(retriever: object) -> int | None:
    chunks = getattr(retriever, "chunks", None)
    if chunks is None:
        return None
    return len(chunks)


def _retrieved_chunk_from_chunk_record(chunk: ChunkRecord) -> RetrievedChunk:
    library_scope = chunk.metadata.get("library_scope")
    return RetrievedChunk(
        doc_id=chunk.document_id,
        knowledge_item_id=chunk.knowledge_item_id,
        title=chunk.title,
        source_type=chunk.source_type,
        source=chunk.source or chunk.source_uri or "fake-vector-store",
        source_url=chunk.source_uri or chunk.source_url,
        region=_optional_str(chunk.metadata.get("region")),
        doc_type=_optional_str(chunk.metadata.get("doc_type")),
        sample_type=_optional_str(chunk.metadata.get("sample_type")),
        business_topic=_optional_str(chunk.metadata.get("business_topic")),
        library_scope=library_scope if library_scope in {"personal", "shared"} else None,  # type: ignore[arg-type]
        chunk_id=chunk.chunk_id,
        snippet=chunk.text,
        score=float(chunk.metadata.get("score") or 1.0),
    )
