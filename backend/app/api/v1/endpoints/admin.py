from fastapi import APIRouter, Depends, HTTPException

from app.admin.schemas import (
    AdminFeedbackOverview,
    AdminPrivateSampleItem,
    AdminSystemStatus,
    AdminUserSummary,
    KnowledgeRefreshTask,
    TriggerKnowledgeRefreshRequest,
    UpdateAdminPrivateSampleRequest,
    UpdateAdminUserRequest,
)
from app.admin.service import get_admin_service
from app.auth.dependencies import require_admin
from app.auth.schemas import AuthenticatedUser, ResetPasswordResponse

router = APIRouter(prefix="/admin")


@router.get("/system/status", response_model=AdminSystemStatus)
def get_admin_system_status(
    current_user: AuthenticatedUser = Depends(require_admin),
) -> AdminSystemStatus:
    del current_user
    return get_admin_service().get_system_status()


@router.get("/users", response_model=list[AdminUserSummary])
def list_admin_users(
    current_user: AuthenticatedUser = Depends(require_admin),
) -> list[AdminUserSummary]:
    del current_user
    return get_admin_service().list_users()


@router.patch("/users/{user_id}", response_model=AdminUserSummary)
def update_admin_user(
    user_id: str,
    payload: UpdateAdminUserRequest,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> AdminUserSummary:
    del current_user
    try:
        get_admin_service().update_user(user_id=user_id, role=payload.role, is_active=payload.is_active)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found.")
    return next(item for item in get_admin_service().list_users() if item.user_id == user_id)


@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
def reset_admin_user_password(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> ResetPasswordResponse:
    del current_user
    try:
        temporary_password = get_admin_service().reset_password(user_id=user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found.")
    return ResetPasswordResponse(temporary_password=temporary_password)


@router.get("/feedback/overview", response_model=AdminFeedbackOverview)
def get_admin_feedback_overview(
    current_user: AuthenticatedUser = Depends(require_admin),
) -> AdminFeedbackOverview:
    del current_user
    return get_admin_service().get_feedback_overview()


@router.get("/private-samples", response_model=list[AdminPrivateSampleItem])
def list_admin_private_samples(
    current_user: AuthenticatedUser = Depends(require_admin),
) -> list[AdminPrivateSampleItem]:
    del current_user
    return get_admin_service().list_private_samples()


@router.patch("/private-samples/{doc_id}", response_model=AdminPrivateSampleItem)
def update_admin_private_sample(
    doc_id: str,
    payload: UpdateAdminPrivateSampleRequest,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> AdminPrivateSampleItem:
    try:
        return get_admin_service().update_private_sample(
            doc_id=doc_id,
            is_enabled=payload.is_enabled,
            session_attachable=payload.session_attachable,
            updated_by_user_id=current_user.user_id,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Private sample not found.")


@router.get("/knowledge-refresh-tasks", response_model=list[KnowledgeRefreshTask])
def list_knowledge_refresh_tasks(
    current_user: AuthenticatedUser = Depends(require_admin),
) -> list[KnowledgeRefreshTask]:
    del current_user
    return get_admin_service().list_knowledge_refresh_tasks()


@router.post("/knowledge-refresh-tasks", response_model=KnowledgeRefreshTask)
def trigger_knowledge_refresh_task(
    payload: TriggerKnowledgeRefreshRequest,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> KnowledgeRefreshTask:
    try:
        return get_admin_service().trigger_knowledge_refresh(
            scope=payload.scope,
            requested_by_user_id=current_user.user_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
