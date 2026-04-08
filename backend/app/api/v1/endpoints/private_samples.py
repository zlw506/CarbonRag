from fastapi import APIRouter, HTTPException

from app.retrieval.private_schemas import PrivateSampleCatalogItem
from app.session.schemas import ReplaceAttachedPrivateSamplesRequest, SessionDetail
from app.session.service import get_session_service

router = APIRouter()


@router.get("/private-samples", response_model=list[PrivateSampleCatalogItem])
def list_private_samples() -> list[PrivateSampleCatalogItem]:
    return get_session_service().list_private_sample_catalog()


@router.put("/sessions/{session_id}/attached-files/private-samples", response_model=SessionDetail)
def replace_attached_private_samples(
    session_id: str,
    payload: ReplaceAttachedPrivateSamplesRequest,
) -> SessionDetail:
    session_service = get_session_service()
    try:
        session_service.replace_attached_private_samples(session_id=session_id, doc_ids=payload.doc_ids)
    except KeyError:
        raise HTTPException(status_code=404, detail="会话不存在。")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在。")
    return session
