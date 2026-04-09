from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.ai_runtime.providers.factory import get_chat_provider
from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.core.config import get_settings
from app.schemas.system import SystemInfoResponse

router = APIRouter()


@router.get("/system/info", response_model=SystemInfoResponse)
def get_system_info(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> SystemInfoResponse:
    settings = get_settings()
    provider = get_chat_provider()
    descriptor = provider.describe()

    return SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
        api_prefix=settings.api_prefix,
        model_provider_mode=descriptor.mode,
        model_name=descriptor.default_model,
        timestamp=datetime.now(timezone.utc),
    )
