from fastapi import APIRouter

from app.api.v1.endpoints.ask import router as ask_router
from app.api.v1.endpoints.system import router as system_router

router = APIRouter()
router.include_router(ask_router, tags=["ask"])
router.include_router(system_router, tags=["system"])
