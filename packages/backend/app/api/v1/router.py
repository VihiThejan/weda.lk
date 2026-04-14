from fastapi import APIRouter

from app.api.v1.routes.maintenance import router as maintenance_router

router = APIRouter()
router.include_router(maintenance_router, prefix="/maintenance", tags=["maintenance"])
