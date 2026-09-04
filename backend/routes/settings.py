from fastapi import APIRouter, HTTPException
import logging
from backend.models.settings import (
    GeminiSettingsResponse,
    GeminiSettingsUpdate,
    GeminiTestResponse,
)
from backend.services.gemini_service import GeminiService

logger = logging.getLogger("retail_copilot.routes.settings")

router = APIRouter(prefix="/api/settings", tags=["Settings & AI Configuration"])


@router.get("/gemini", response_model=GeminiSettingsResponse)
async def get_gemini_settings():
    """
    Retrieve current Gemini AI configuration status and masked API key.
    Never exposes the full API key to the client.
    """
    return GeminiSettingsResponse(
        configured=GeminiService.is_configured(),
        masked_key=GeminiService.get_masked_key(),
        model=GeminiService.get_active_model(),
    )


@router.post("/gemini", response_model=GeminiSettingsResponse)
async def update_gemini_settings(payload: GeminiSettingsUpdate):
    """
    Configure or update the Gemini API key on the backend.
    """
    clean_key = payload.api_key.strip()
    if not clean_key or len(clean_key) < 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid Gemini API key provided. Key must be at least 5 characters.",
        )

    # Store user-configured key in backend service
    GeminiService.set_configured_key(api_key=clean_key, model=payload.model)

    return GeminiSettingsResponse(
        configured=True,
        masked_key=GeminiService.get_masked_key(),
        model=GeminiService.get_active_model(),
    )


@router.post("/gemini/test", response_model=GeminiTestResponse)
async def test_gemini_settings():
    """
    Test the active Gemini API key connection with a minimal request.
    """
    result = GeminiService.test_connection()
    return GeminiTestResponse(
        success=result["success"],
        message=result["message"],
        model=result.get("model"),
    )
