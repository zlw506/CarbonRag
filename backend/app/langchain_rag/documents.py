from __future__ import annotations

from typing import Iterable

from app.knowledge import get_knowledge_service
from app.knowledge.schemas import KnowledgeChunk, KnowledgeItem, KnowledgeItemListFilters
from app.langchain_rag.schemas import LangChainRagDocument, LangChainRagScope

try:  # pragma: no cover - exercised when langchain is installed
    from langchain_core.documents import Document
except Exception:  # noqa: BLE001
    Document = None  # type: ignore[assignment]


def load_visible_documents(
    *,
    owner_user_id: str,
    knowledge_scope: LangChainRagScope,
    allowed_knowledge_item_ids: Iterable[str] | None = None,
) -> list[LangChainRagDocument]:
    service = get_knowledge_service()
    allowed_ids = [item_id for item_id in dict.fromkeys(allowed_knowledge_item_ids or []) if item_id]
    items: list[KnowledgeItem] = []

    if knowledge_scope in {"public", "mixed"}:
        items.extend(
            service.list_admin_items(
                library_scope="shared",
                source_type="public_policy_web",
                is_enabled=True,
                index_status="indexed",
            )
        )

    if knowledge_scope in {"private_sample", "mixed"} and allowed_ids:
        visible = service.list_visible_items(
            owner_user_id=owner_user_id,
            filters=KnowledgeItemListFilters(
                knowledge_item_ids=allowed_ids,
                is_enabled=True,
                index_status="indexed",
            ),
        )
        visible_by_id = {item.knowledge_item_id: item for item in visible}
        items.extend(visible_by_id[item_id] for item_id in allowed_ids if item_id in visible_by_id)

    return _documents_from_items(items)


def load_all_indexable_documents() -> list[LangChainRagDocument]:
    service = get_knowledge_service()
    items = service.list_admin_items(is_enabled=True, index_status="indexed")
    return _documents_from_items(items)


def load_file_documents(*, owner_user_id: str, file_id: str) -> list[LangChainRagDocument]:
    service = get_knowledge_service()
    items = service.list_visible_items(
        owner_user_id=owner_user_id,
        filters=KnowledgeItemListFilters(
            file_id=file_id,
            source_type="uploaded_file",
            is_enabled=True,
            index_status="indexed",
        ),
    )
    return _documents_from_items(items)


def to_langchain_documents(documents: list[LangChainRagDocument]):
    if Document is None:
        return documents
    return [Document(page_content=document.page_content, metadata=document.metadata) for document in documents]


def _documents_from_items(items: list[KnowledgeItem]) -> list[LangChainRagDocument]:
    if not items:
        return []
    service = get_knowledge_service()
    item_map = {item.knowledge_item_id: item for item in items}
    chunks = service.list_chunks(knowledge_item_ids=list(item_map))
    documents: list[LangChainRagDocument] = []
    for chunk in chunks:
        item = item_map.get(chunk.knowledge_item_id)
        if item is None:
            continue
        documents.append(_document_from_chunk(item=item, chunk=chunk))
    return documents


def _document_from_chunk(*, item: KnowledgeItem, chunk: KnowledgeChunk) -> LangChainRagDocument:
    metadata = {
        **chunk.metadata,
        "chunk_id": chunk.chunk_id,
        "knowledge_item_id": item.knowledge_item_id,
        "doc_id": item.knowledge_item_id,
        "file_id": item.file_id or chunk.metadata.get("file_id"),
        "owner_user_id": item.owner_user_id,
        "library_scope": item.library_scope,
        "source_type": _citation_source_type(item=item, chunk=chunk),
        "title": chunk.title or item.title,
        "source": chunk.source or item.source or "",
        "source_url": chunk.source_url or item.source_url,
        "page_number": _optional_int(chunk.metadata.get("page_number")),
        "sheet_name": _optional_str(chunk.metadata.get("sheet_name")),
        "slide_number": _optional_int(chunk.metadata.get("slide_number")),
        "section_title": _optional_str(chunk.metadata.get("section_title")),
        "order_index": chunk.order_index,
    }
    return LangChainRagDocument(page_content=chunk.snippet, metadata=metadata)


def _citation_source_type(*, item: KnowledgeItem, chunk: KnowledgeChunk) -> str:
    if item.source_type == "uploaded_file":
        return "private_upload"
    if item.source_type == "private_sample_repo":
        return "private_sample"
    if item.source_type == "public_policy_web":
        if item.visibility == "demo" or chunk.visibility == "demo":
            return "public_policy_demo"
        return "public_policy"
    return str(chunk.source_type or "public_policy")


def _optional_str(value) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_int(value) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
