import httpx
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.schemas import HealthResponse

router = APIRouter()

@router.get("", response_model=HealthResponse)
async def health():
    ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ok = r.status_code == 200
    except Exception:
        pass
    return HealthResponse(status="healthy" if ok else "degraded",
                          ollama_connected=ok, model=settings.OLLAMA_MODEL,
                          version=settings.VERSION)

@router.get("/live")
async def live():
    return {"status": "alive"}
