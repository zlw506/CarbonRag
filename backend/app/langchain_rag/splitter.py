from __future__ import annotations

from app.langchain_rag.config import LangChainRagConfig
from app.langchain_rag.schemas import LangChainRagDocument

try:  # pragma: no cover - exercised when langchain-text-splitters is installed
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:  # noqa: BLE001
    RecursiveCharacterTextSplitter = None  # type: ignore[assignment]


DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", ";", "，", ",", " ", ""]


def split_documents(documents: list[LangChainRagDocument], *, config: LangChainRagConfig) -> list[LangChainRagDocument]:
    if RecursiveCharacterTextSplitter is None:
        return _fallback_split(documents, chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=DEFAULT_SEPARATORS,
    )
    split_docs: list[LangChainRagDocument] = []
    for document in documents:
        chunks = splitter.split_text(document.page_content)
        for index, chunk in enumerate(chunks):
            metadata = {**document.metadata}
            metadata["split_index"] = index
            metadata["chunk_id"] = f"{metadata.get('chunk_id') or metadata.get('knowledge_item_id')}-{index}"
            split_docs.append(LangChainRagDocument(page_content=chunk, metadata=metadata))
    return split_docs


def _fallback_split(
    documents: list[LangChainRagDocument],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[LangChainRagDocument]:
    split_docs: list[LangChainRagDocument] = []
    step = max(chunk_size - chunk_overlap, 1)
    for document in documents:
        text = document.page_content
        if len(text) <= chunk_size:
            split_docs.append(document)
            continue
        for index, start in enumerate(range(0, len(text), step)):
            chunk = text[start:start + chunk_size]
            if not chunk.strip():
                continue
            metadata = {**document.metadata, "split_index": index}
            metadata["chunk_id"] = f"{metadata.get('chunk_id') or metadata.get('knowledge_item_id')}-{index}"
            split_docs.append(LangChainRagDocument(page_content=chunk, metadata=metadata))
    return split_docs
