from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies import get_db
from backend.core.config import settings
from backend.core.ai_engine import ai_engine
from backend.services.metrics_service import metrics_service

router = APIRouter(tags=["settings"])


class SettingsUpdate(BaseModel):
    zai_api_key: Optional[str] = Field(None, description="GLM-5.3 API Key")
    zai_base_url: Optional[str] = Field(None, description="API Base URL")
    model_name: Optional[str] = Field(None, description="Model Name, e.g. glm-5.3")
    reasoning_effort: Optional[str] = Field(None, description="Reasoning effort: low, high, max")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)


class ConnectionTestRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


@router.get("/ai/status")
async def get_ai_status():
    """
    Test real connection to live GLM-5.3 API.
    Used by frontend status badge and healthcheck.
    """
    return await ai_engine.test_connection()


@router.post("/ai/test")
async def test_ai_connection(req: ConnectionTestRequest):
    """
    Test specific API credentials on-demand without permanently saving them first.
    """
    return await ai_engine.test_connection(
        api_key=req.api_key,
        base_url=req.base_url,
        model_name=req.model_name
    )


@router.get("/settings")
async def get_settings():
    """Retrieve active system and LLM configuration."""
    api_key_set = bool(ai_engine.api_key or settings.ZAI_API_KEY)
    masked_key = ""
    active_key = (ai_engine.api_key or settings.ZAI_API_KEY).strip()
    if active_key:
        masked_key = active_key[:4] + "..." + active_key[-4:] if len(active_key) > 8 else "****"

    return {
        "model_name": ai_engine.model_name or settings.MODEL_NAME,
        "base_url": ai_engine.base_url or settings.ZAI_BASE_URL,
        "reasoning_effort": settings.REASONING_EFFORT,
        "temperature": settings.TEMPERATURE,
        "api_key_configured": api_key_set,
        "masked_api_key": masked_key,
        "database_url": settings.DATABASE_URL.split("///")[-1],
    }


@router.post("/settings")
async def update_settings(update: SettingsUpdate):
    """Update active LLM configuration."""
    if update.zai_api_key is not None:
        ai_engine.api_key = update.zai_api_key.strip()
        settings.ZAI_API_KEY = ai_engine.api_key
    if update.zai_base_url is not None and update.zai_base_url.strip():
        ai_engine.base_url = update.zai_base_url.strip()
        settings.ZAI_BASE_URL = ai_engine.base_url
    if update.model_name is not None and update.model_name.strip():
        ai_engine.model_name = update.model_name.strip()
        settings.MODEL_NAME = ai_engine.model_name
    if update.reasoning_effort is not None:
        settings.REASONING_EFFORT = update.reasoning_effort
    if update.temperature is not None:
        settings.TEMPERATURE = update.temperature

    # Test the newly updated key
    status = await ai_engine.test_connection()

    return {
        "message": "Settings updated successfully",
        "model": ai_engine.model_name,
        "connection_status": status
    }


@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """Retrieve real-time metrics for dashboard KPI cards."""
    return await metrics_service.get_dashboard_metrics(db)
