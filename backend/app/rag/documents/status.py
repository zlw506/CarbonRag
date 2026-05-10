from __future__ import annotations

from typing import Literal


RAG_DOCUMENT_STATUSES = ("uploaded", "parsed", "chunked", "indexed", "failed")
RagDocumentStatus = Literal["uploaded", "parsed", "chunked", "indexed", "failed"]


def resolve_document_status(*, parse_status: str, chunk_status: str, index_status: str) -> RagDocumentStatus:
    if "failed" in {parse_status, chunk_status, index_status} or "error" in {parse_status, chunk_status, index_status}:
        return "failed"
    if index_status == "indexed":
        return "indexed"
    if chunk_status == "chunked":
        return "chunked"
    if parse_status == "parsed":
        return "parsed"
    return "uploaded"

