from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.rag.embeddings import RagEmbeddingUnavailable, embed_documents, embed_query
from app.rag.kb.models import RagChunk
from app.rag.vector_backend.base import BaseVectorStore, VectorIndexResult, VectorSearchHit, VectorSearchResult


class MilvusVectorStoreAdapter(BaseVectorStore):
    """Milvus Lite/Milvus adapter migrated from the RAG-Pro vector-store spine."""

    backend_name = "milvus_lite"
    dense_dim = 1024

    def index_chunks(self, *, chunks: list[RagChunk], embeddings=None) -> VectorIndexResult:
        if not chunks:
            return VectorIndexResult(indexed_count=0, backend=self.backend_name, available=True)
        try:
            client = _milvus_client()
            embeddings = embeddings or embed_documents([chunk.text for chunk in chunks])
            if not embeddings.dense:
                return VectorIndexResult(
                    indexed_count=0,
                    backend=self.backend_name,
                    available=False,
                    degraded=True,
                    warning="BGE-M3 returned no dense vectors.",
                )
            chunk_index = {chunk.rag_chunk_id: index for index, chunk in enumerate(chunks)}
            indexed_count = 0
            for kb_id, kb_chunks in _group_by_kb(chunks).items():
                collection_name = _collection_name(kb_id)
                _ensure_collection(client, collection_name, len(embeddings.dense[0]))
                rows: list[dict[str, Any]] = []
                for chunk in kb_chunks:
                    index = chunk_index[chunk.rag_chunk_id]
                    rows.append(
                        {
                            "id": chunk.rag_chunk_id,
                            "chunk_id": chunk.rag_chunk_id,
                            "doc_id": chunk.doc_id,
                            "kb_id": chunk.kb_id,
                            "owner_user_id": chunk.owner_user_id or "",
                            "source_type": str(chunk.metadata.get("source_type") or "private_upload")[:64],
                            "title": str(chunk.metadata.get("title") or chunk.metadata.get("source") or "RAG 文档")[:512],
                            "content": chunk.text[:8000],
                            "dense_vector": embeddings.dense[index],
                            "page_number": int(chunk.page_number or 0),
                            "sheet_name": str(chunk.sheet_name or "")[:256],
                            "slide_number": int(chunk.slide_number or 0),
                        }
                    )
                try:
                    client.delete(collection_name=collection_name, filter=f'doc_id == "{_escape_filter_value(kb_chunks[0].doc_id)}"')
                except Exception:
                    pass
                client.insert(collection_name=collection_name, data=rows)
                indexed_count += len(rows)
            return VectorIndexResult(indexed_count=indexed_count, backend=self.backend_name, available=True)
        except RagEmbeddingUnavailable as exc:
            return VectorIndexResult(indexed_count=0, backend=self.backend_name, available=False, degraded=True, warning=str(exc))
        except Exception as exc:  # noqa: BLE001
            return VectorIndexResult(
                indexed_count=0,
                backend=self.backend_name,
                available=False,
                degraded=True,
                warning=f"Milvus Lite/Milvus runtime unavailable: {exc}",
            )

    def search(self, *, query: str, chunks: list[RagChunk], top_k: int) -> VectorSearchResult:
        if not chunks:
            return VectorSearchResult(hits=[], backend=self.backend_name, available=True)
        try:
            client = _milvus_client()
            dense_query, _ = embed_query(query)
            chunk_map = {chunk.rag_chunk_id: chunk for chunk in chunks}
            hits: list[VectorSearchHit] = []
            for kb_id in sorted({chunk.kb_id for chunk in chunks}):
                collection_name = _collection_name(kb_id)
                if not client.has_collection(collection_name):
                    continue
                results = client.search(
                    collection_name=collection_name,
                    data=[dense_query],
                    anns_field="dense_vector",
                    limit=max(top_k, 1),
                    output_fields=["chunk_id"],
                )
                for row in results[0] if results else []:
                    entity = row.get("entity") or {}
                    chunk_id = str(entity.get("chunk_id") or row.get("id") or "")
                    chunk = chunk_map.get(chunk_id)
                    if chunk is None:
                        continue
                    score = float(row.get("distance") or row.get("score") or 0.0)
                    hits.append(VectorSearchHit(chunk=chunk, score=score))
            hits.sort(key=lambda item: item.score, reverse=True)
            return VectorSearchResult(hits=hits[:top_k], backend=self.backend_name, available=True)
        except RagEmbeddingUnavailable as exc:
            return VectorSearchResult(hits=[], backend=self.backend_name, available=False, degraded=True, warning=str(exc))
        except Exception as exc:  # noqa: BLE001
            return VectorSearchResult(
                hits=[],
                backend=self.backend_name,
                available=False,
                degraded=True,
                warning=f"Milvus Lite/Milvus runtime unavailable: {exc}",
            )


def _milvus_client():
    try:
        from pymilvus import MilvusClient
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("pymilvus is not installed.") from exc
    settings = get_settings()
    uri = settings.rag_milvus_uri
    if uri and not uri.startswith(("http://", "https://", "tcp://")):
        Path(uri).parent.mkdir(parents=True, exist_ok=True)
    return MilvusClient(uri=uri)


def _ensure_collection(client, collection_name: str, dim: int) -> None:
    if client.has_collection(collection_name):
        return
    try:
        from pymilvus import DataType

        schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=96, is_primary=True)
        schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, max_length=96)
        schema.add_field(field_name="doc_id", datatype=DataType.VARCHAR, max_length=96)
        schema.add_field(field_name="kb_id", datatype=DataType.VARCHAR, max_length=96)
        schema.add_field(field_name="owner_user_id", datatype=DataType.VARCHAR, max_length=96)
        schema.add_field(field_name="source_type", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=512)
        schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=8192)
        schema.add_field(field_name="page_number", datatype=DataType.INT64)
        schema.add_field(field_name="sheet_name", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="slide_number", datatype=DataType.INT64)
        schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=dim)
        index_params = client.prepare_index_params()
        index_params.add_index(field_name="dense_vector", index_type="FLAT", metric_type="COSINE")
        client.create_collection(collection_name=collection_name, schema=schema, index_params=index_params)
    except Exception:
        client.create_collection(collection_name=collection_name, dimension=dim, metric_type="COSINE", auto_id=False)


def _collection_name(kb_id: str) -> str:
    prefix = re.sub(r"[^A-Za-z0-9_]", "_", get_settings().rag_milvus_collection_prefix or "carbonrag")
    safe_kb = re.sub(r"[^A-Za-z0-9_]", "_", kb_id)
    candidate = f"{prefix}_{safe_kb}"
    if not candidate[0].isalpha() and candidate[0] != "_":
        candidate = f"c_{candidate}"
    return candidate[:255]


def _group_by_kb(chunks: list[RagChunk]) -> dict[str, list[RagChunk]]:
    grouped: dict[str, list[RagChunk]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk.kb_id, []).append(chunk)
    return grouped


def _escape_filter_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
