from fastapi import APIRouter
from app.core.config import get_settings
router = APIRouter()
@router.get("/health")
async def health():
    settings = get_settings()
    return {"status": "ok", "service": "truthlens-api", "huggingface_configured": bool(settings.hf_token), "huggingface_model": settings.hf_model_id, "mongodb_configured": bool(settings.mongodb_uri)}
