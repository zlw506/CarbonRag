from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.rag.schemas import RagExperimentalRetrievalStrategy
from app.rag.vector_store import VectorStoreAdapter, VectorStoreHealth, VectorStoreSearchResult
from app.retrieval.schemas import RetrievedChunk


ChunkSourceMetadata = dict[str, Any]


class RetrieverStrategyResult(BaseModel):
    strategy: RagExperimentalRetrievalStrategy
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    total_hits: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrieverStrategy(Protocol):
    name: RagExperimentalRetrievalStrategy

    def retrieve(
        self,
        *,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
        query_embedding: list[float] | None = None,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> RetrieverStrategyResult:
        ...


class BM25Retriever:
    name: RagExperimentalRetrievalStrategy = "bm25_only"

    def __init__(self, *, adapter: VectorStoreAdapter) -> None:
        self.adapter = adapter

    def retrieve(
        self,
        *,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
        query_embedding: list[float] | None = None,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> RetrieverStrategyResult:
        result = self.adapter.search(
            question=query,
            top_k=top_k,
            filters=filters or {},
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
        )
        chunk_sources = {
            chunk.chunk_id: _chunk_source_metadata(
                bm25_score=chunk.score,
                vector_score=None,
                merged_score=chunk.score,
                source_retrievers=["bm25"],
            )
            for chunk in result.chunks
        }
        return RetrieverStrategyResult(
            strategy=self.name,
            chunks=result.chunks[:top_k],
            total_hits=result.total_hits,
            metadata={
                "bm25_hit_count": result.total_hits,
                "vector_hit_count": 0,
                "chunk_sources": chunk_sources,
                "fallback_used": False,
                "fallback_reason": None,
                "bm25_backend": result.backend,
                "bm25_adapter_name": result.adapter_name,
                "bm25_metadata": result.metadata,
                "vector_status": "disabled",
                "retrieval_layer": "bm25_fallback",
            },
        )


class VectorRetriever:
    name: RagExperimentalRetrievalStrategy = "vector_only"

    def __init__(self, *, adapter: VectorStoreAdapter, health: VectorStoreHealth | None = None) -> None:
        self.adapter = adapter
        self.health = health

    def retrieve(
        self,
        *,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
        query_embedding: list[float] | None = None,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> RetrieverStrategyResult:
        health = self.health or self._safe_healthcheck()
        if not health.available:
            return self._unavailable_result(
                query=query,
                top_k=top_k,
                filters=filters,
                allowed_knowledge_item_ids=allowed_knowledge_item_ids,
                health=health,
            )

        try:
            result = self.adapter.search(
                question=query,
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters or {},
                allowed_knowledge_item_ids=allowed_knowledge_item_ids,
            )
        except Exception as exc:  # noqa: BLE001
            return RetrieverStrategyResult(
                strategy=self.name,
                chunks=[],
                total_hits=0,
                metadata={
                    "vector_status": "error",
                    "vector_hit_count": 0,
                    "fallback_used": True,
                    "fallback_reason": "vector_retrieval_error",
                    "vector_backend": health.backend,
                    "vector_backend_health": health.status,
                    "vector_adapter_name": _vector_adapter_name(health),
                    "vector_error": {"type": type(exc).__name__, "message": str(exc)},
                    "chunk_sources": {},
                    "retrieval_layer": "bm25_fallback",
                },
            )

        status = str(result.metadata.get("status") or "ok")
        vector_status = "error" if status == "error" else "queried"
        fallback_reason = _result_fallback_reason(result)
        chunk_sources = {
            chunk.chunk_id: _chunk_source_metadata(
                bm25_score=None,
                vector_score=chunk.score,
                merged_score=chunk.score,
                source_retrievers=["vector"],
            )
            for chunk in result.chunks
        }
        return RetrieverStrategyResult(
            strategy=self.name,
            chunks=result.chunks[:top_k],
            total_hits=result.total_hits,
            metadata={
                "vector_status": vector_status,
                "vector_hit_count": result.total_hits,
                "fallback_used": fallback_reason is not None,
                "fallback_reason": fallback_reason,
                "vector_backend": result.backend or health.backend,
                "vector_backend_health": health.status,
                "vector_adapter_name": result.adapter_name or _vector_adapter_name(health),
                "vector_metadata": result.metadata,
                "chunk_sources": chunk_sources,
                "retrieval_layer": "vector" if result.chunks else "bm25_fallback",
            },
        )

    def _safe_healthcheck(self) -> VectorStoreHealth:
        try:
            return self.adapter.healthcheck()
        except Exception as exc:  # noqa: BLE001
            return VectorStoreHealth(
                backend=str(getattr(self.adapter, "backend", "unknown") or "unknown"),
                status="degraded",
                available=False,
                reason=str(exc),
                metadata={"adapter_name": type(self.adapter).__name__, "error_type": type(exc).__name__},
            )

    def _unavailable_result(
        self,
        *,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None,
        allowed_knowledge_item_ids: set[str] | None,
        health: VectorStoreHealth,
    ) -> RetrieverStrategyResult:
        return RetrieverStrategyResult(
            strategy=self.name,
            chunks=[],
            total_hits=0,
            metadata={
                "vector_status": "unavailable",
                "vector_hit_count": 0,
                "fallback_used": True,
                "fallback_reason": health.reason or "vector_store_unavailable",
                "vector_backend": health.backend,
                "vector_backend_health": health.status,
                "vector_adapter_name": _vector_adapter_name(health),
                "query_length": len(query),
                "top_k": top_k,
                "filters": filters or {},
                "allowed_knowledge_item_count": len(allowed_knowledge_item_ids or set()),
                "chunk_sources": {},
                "retrieval_layer": "bm25_fallback",
            },
        )


class HybridRetriever:
    name: RagExperimentalRetrievalStrategy = "bm25_vector_hybrid"

    def __init__(self, *, bm25_retriever: BM25Retriever, vector_retriever: VectorRetriever) -> None:
        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever

    def retrieve(
        self,
        *,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
        query_embedding: list[float] | None = None,
        allowed_knowledge_item_ids: set[str] | None = None,
    ) -> RetrieverStrategyResult:
        bm25 = self.bm25_retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=filters,
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
        )
        vector = self.vector_retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=filters,
            query_embedding=query_embedding,
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
        )

        merged_chunks, chunk_sources = _merge_chunks(
            bm25_chunks=bm25.chunks,
            vector_chunks=vector.chunks,
            top_k=top_k,
        )
        vector_fallback_reason = vector.metadata.get("fallback_reason")
        return RetrieverStrategyResult(
            strategy=self.name,
            chunks=merged_chunks,
            total_hits=len(merged_chunks),
            metadata={
                "bm25_hit_count": bm25.total_hits,
                "vector_hit_count": vector.total_hits,
                "fallback_used": bool(vector.metadata.get("fallback_used")),
                "fallback_reason": vector_fallback_reason,
                "chunk_sources": chunk_sources,
                "bm25_metadata": bm25.metadata,
                "vector_metadata": vector.metadata,
                "vector_status": vector.metadata.get("vector_status", "unavailable"),
                "vector_backend": vector.metadata.get("vector_backend"),
                "vector_backend_health": vector.metadata.get("vector_backend_health"),
                "vector_adapter_name": vector.metadata.get("vector_adapter_name"),
                "retrieval_layer": "vector" if vector.chunks else "bm25_fallback",
            },
        )


def _merge_chunks(
    *,
    bm25_chunks: list[RetrievedChunk],
    vector_chunks: list[RetrievedChunk],
    top_k: int,
) -> tuple[list[RetrievedChunk], dict[str, ChunkSourceMetadata]]:
    bm25_max = max((chunk.score for chunk in bm25_chunks), default=0.0)
    vector_max = max((chunk.score for chunk in vector_chunks), default=0.0)
    records: dict[str, dict[str, Any]] = {}

    for chunk in bm25_chunks:
        records[chunk.chunk_id] = {
            "chunk": chunk,
            "bm25_score": chunk.score,
            "vector_score": None,
            "from_bm25": True,
            "from_vector": False,
            "source_retrievers": ["bm25"],
            "bm25_normalized": _normalize_score(chunk.score, bm25_max),
            "vector_normalized": 0.0,
        }

    for chunk in vector_chunks:
        record = records.get(chunk.chunk_id)
        if record is None:
            record = {
                "chunk": chunk,
                "bm25_score": None,
                "vector_score": chunk.score,
                "from_bm25": False,
                "from_vector": True,
                "source_retrievers": ["vector"],
                "bm25_normalized": 0.0,
                "vector_normalized": _normalize_score(chunk.score, vector_max),
            }
            records[chunk.chunk_id] = record
            continue

        record["vector_score"] = chunk.score
        record["from_vector"] = True
        record["vector_normalized"] = _normalize_score(chunk.score, vector_max)
        if "vector" not in record["source_retrievers"]:
            record["source_retrievers"].append("vector")

    ranked: list[tuple[float, dict[str, Any]]] = []
    for record in records.values():
        source_count = len(record["source_retrievers"])
        merged_score = (float(record["bm25_normalized"]) + float(record["vector_normalized"])) / max(source_count, 1)
        record["merged_score"] = merged_score
        ranked.append((merged_score, record))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected_records = [record for _, record in ranked[:top_k]]
    chunk_sources: dict[str, ChunkSourceMetadata] = {}
    merged_chunks: list[RetrievedChunk] = []
    for record in selected_records:
        chunk = record["chunk"].model_copy(update={"score": float(record["merged_score"])})
        merged_chunks.append(chunk)
        chunk_sources[chunk.chunk_id] = _chunk_source_metadata(
            bm25_score=record["bm25_score"],
            vector_score=record["vector_score"],
            merged_score=float(record["merged_score"]),
            source_retrievers=list(record["source_retrievers"]),
        )
    return merged_chunks, chunk_sources


def _chunk_source_metadata(
    *,
    bm25_score: float | None,
    vector_score: float | None,
    merged_score: float,
    source_retrievers: list[str],
) -> ChunkSourceMetadata:
    from_bm25 = "bm25" in source_retrievers
    from_vector = "vector" in source_retrievers
    return {
        "bm25_score": bm25_score,
        "vector_score": vector_score,
        "merged_score": merged_score,
        "from_bm25": from_bm25,
        "from_vector": from_vector,
        "source_retrievers": source_retrievers,
        "retrieval_layer": "vector" if from_vector and not from_bm25 else "bm25_fallback",
    }


def _normalize_score(score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return score / max_score


def _result_fallback_reason(result: VectorStoreSearchResult) -> str | None:
    if result.chunks:
        return None
    reason = result.metadata.get("reason")
    if isinstance(reason, str) and reason:
        return reason
    return "vector_returned_no_hits"


def _vector_adapter_name(health: VectorStoreHealth) -> str:
    adapter_name = health.metadata.get("adapter_name")
    return adapter_name if isinstance(adapter_name, str) and adapter_name else health.backend
