from fastapi import APIRouter
from pydantic import BaseModel
import time
from datetime import datetime, timezone

router = APIRouter()

START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: int
    timestamp: str
    components: dict


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    now = datetime.now(timezone.utc).isoformat()
    uptime = int(time.time() - START_TIME)
    components = {
        "llm_service": {"ok": True, "note": "placeholder"},
        "sports_api": {"ok": True, "note": "placeholder"},
    }
    return HealthResponse(
        status="ok", uptime_seconds=uptime, timestamp=now, components=components
    )
