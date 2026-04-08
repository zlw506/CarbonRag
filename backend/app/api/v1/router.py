from fastapi import APIRouter

from app.api.v1.endpoints.calc_carbon import router as calc_carbon_router
from app.api.v1.endpoints.feedback import router as feedback_router
from app.api.v1.endpoints.files import router as files_router
from app.api.v1.endpoints.private_samples import router as private_samples_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.system import router as system_router

router = APIRouter()
router.include_router(calc_carbon_router, tags=["calc-carbon"])
router.include_router(feedback_router, tags=["feedback"])
router.include_router(files_router, tags=["files"])
router.include_router(private_samples_router, tags=["private-samples"])
router.include_router(sessions_router, tags=["sessions"])
router.include_router(system_router, tags=["system"])
