from typing import Optional
from pydantic import BaseModel, Field


class GeminiSettingsResponse(BaseModel):
    configured: bool = Field(..., description="Whether a Gemini API key is currently configured")
    masked_key: Optional[str] = Field(None, description="Masked preview of the active API key")
    model: str = Field("gemini-2.5-flash", description="Active Gemini model identifier")


class GeminiSettingsUpdate(BaseModel):
    api_key: str = Field(..., min_length=5, max_length=200, description="Google Gemini API key")
    model: Optional[str] = Field(None, description="Gemini model identifier")


class GeminiTestResponse(BaseModel):
    success: bool = Field(..., description="Whether the Gemini API connection succeeded")
    message: str = Field(..., description="User-friendly status or error message")
    model: Optional[str] = Field(None, description="Model tested")
