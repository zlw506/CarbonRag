from fastapi import APIRouter, HTTPException

from app.feedback.schemas import FeedbackRequest, FeedbackResponse
from app.feedback.service import FeedbackService, get_feedback_service

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    service: FeedbackService = get_feedback_service()
    try:
        return service.submit(payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="会话不存在。")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
