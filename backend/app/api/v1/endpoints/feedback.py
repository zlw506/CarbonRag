from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.feedback.schemas import FeedbackRequest, FeedbackResponse
from app.feedback.service import FeedbackService, get_feedback_service

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> FeedbackResponse:
    service: FeedbackService = get_feedback_service()
    try:
        return service.submit(owner_user_id=current_user.user_id, payload=payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
