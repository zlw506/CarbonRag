from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.providers.factory import get_model_provider
from app.schemas.system import SystemInfoResponse

router = APIRouter()


@router.get("/system/info", response_model=SystemInfoResponse)
def get_system_info() -> SystemInfoResponse:
    settings = get_settings()
    provider = get_model_provider()
    descriptor = provider.describe()

    return SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
        api_prefix=settings.api_prefix,
        model_provider_mode=descriptor.mode,
        model_name=descriptor.default_model,
        timestamp=datetime.now(timezone.utc)
    )
