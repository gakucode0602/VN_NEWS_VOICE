from datetime import datetime

from fastapi import APIRouter, status

from app.models.schemas import HealthResponse

router = APIRouter(prefix="/health")


@router.get("/", status_code=status.HTTP_200_OK, response_model=HealthResponse)
def check_health():
    return HealthResponse(status="ok", version="v1", timestamp=datetime.now())
