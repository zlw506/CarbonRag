from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.rag.kb.models import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, RagChunk, RagDocument, RagDocumentCreate
from app.rag.spine import get_rag_spine_service

router = APIRouter(prefix="/kb")
logger = logging.getLogger(__name__)


@router.get("", response_model=list[KnowledgeBase])
def list_knowledge_bases(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> list[KnowledgeBase]:
    return get_rag_spine_service().list_kbs(owner_user_id=current_user.user_id)


@router.post("", response_model=KnowledgeBase)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> KnowledgeBase:
    return get_rag_spine_service().create_kb(owner_user_id=current_user.user_id, payload=payload)


@router.get("/{kb_id}", response_model=KnowledgeBase)
def get_knowledge_base(
    kb_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> KnowledgeBase:
    try:
        return get_rag_spine_service().get_kb(owner_user_id=current_user.user_id, kb_id=kb_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="knowledge base not found") from exc


@router.patch("/{kb_id}", response_model=KnowledgeBase)
def update_knowledge_base(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> KnowledgeBase:
    try:
        return get_rag_spine_service().update_kb(owner_user_id=current_user.user_id, kb_id=kb_id, payload=payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="knowledge base not found") from exc


@router.delete("/{kb_id}")
def delete_knowledge_base(
    kb_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict[str, str]:
    get_rag_spine_service().delete_kb(owner_user_id=current_user.user_id, kb_id=kb_id)
    return {"status": "deleted", "kb_id": kb_id}


@router.post("/{kb_id}/documents", response_model=RagDocument)
def create_document(
    kb_id: str,
    payload: RagDocumentCreate,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagDocument:
    try:
        return get_rag_spine_service().create_document(owner_user_id=current_user.user_id, kb_id=kb_id, payload=payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="knowledge base or source document not found") from exc


@router.get("/{kb_id}/documents", response_model=list[RagDocument])
def list_documents(
    kb_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[RagDocument]:
    try:
        return get_rag_spine_service().list_documents(owner_user_id=current_user.user_id, kb_id=kb_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="knowledge base not found") from exc


@router.get("/{kb_id}/documents/{doc_id}", response_model=RagDocument)
def get_document(
    kb_id: str,
    doc_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagDocument:
    try:
        return get_rag_spine_service().get_document(owner_user_id=current_user.user_id, kb_id=kb_id, doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc


@router.post("/{kb_id}/documents/{doc_id}/parse", response_model=RagDocument)
def parse_document(
    kb_id: str,
    doc_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagDocument:
    try:
        return get_rag_spine_service().parse_document(owner_user_id=current_user.user_id, kb_id=kb_id, doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc


@router.post("/{kb_id}/documents/{doc_id}/chunk", response_model=RagDocument)
def chunk_document(
    kb_id: str,
    doc_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagDocument:
    try:
        return get_rag_spine_service().chunk_document(owner_user_id=current_user.user_id, kb_id=kb_id, doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc


@router.post("/{kb_id}/documents/{doc_id}/index", response_model=RagDocument)
def index_document(
    kb_id: str,
    doc_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RagDocument:
    try:
        return get_rag_spine_service().index_document(owner_user_id=current_user.user_id, kb_id=kb_id, doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc


@router.get("/{kb_id}/documents/{doc_id}/chunks", response_model=list[RagChunk])
def list_document_chunks(
    kb_id: str,
    doc_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[RagChunk]:
    try:
        return get_rag_spine_service().list_chunks(owner_user_id=current_user.user_id, kb_id=kb_id, doc_id=doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc

