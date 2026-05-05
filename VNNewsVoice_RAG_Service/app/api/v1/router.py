from fastapi import APIRouter

from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.admin import router as admin_router

router = APIRouter(prefix="/api/v1")

router.include_router(chat_router)

router.include_router(health_router)

router.include_router(admin_router)
