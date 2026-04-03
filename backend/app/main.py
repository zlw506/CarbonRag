from fastapi import FastAPI

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import router as api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CarbonRag stable bootstrap backend shell"
)
app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_prefix)
