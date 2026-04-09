from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.retrieval.private_schemas import PrivateSampleCatalogItem
from app.session.schemas import ReplaceAttachedPrivateSamplesRequest, SessionDetail
from app.session.service import get_session_service

router = APIRouter()


@router.get("/private-samples", response_model=list[PrivateSampleCatalogItem])
def list_private_samples(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[PrivateSampleCatalogItem]:
    return get_session_service().list_private_sample_catalog()


@router.put("/sessions/{session_id}/attached-files/private-samples", response_model=SessionDetail)
def replace_attached_private_samples(
    session_id: str,
    payload: ReplaceAttachedPrivateSamplesRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> SessionDetail:
    session_service = get_session_service()
    try:
        knowledge_item_ids = payload.knowledge_item_ids or payload.doc_ids
        session_service.replace_attached_knowledge_items(
            owner_user_id=current_user.user_id,
            session_id=session_id,
            knowledge_item_ids=knowledge_item_ids,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    session = session_service.get_session(owner_user_id=current_user.user_id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session
