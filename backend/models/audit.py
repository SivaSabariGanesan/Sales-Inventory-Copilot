from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AuditExecutionStep(BaseModel):
    step_name: str
    status: str
    details: Optional[Dict[str, Any]] = None


class AuditLogItem(BaseModel):
    id: int
    timestamp: str
    user_id: Optional[str] = None
    question: str
    normalized_question: str
    intent: str
    confidence: float
    status: str
    cache_hit: bool
    cache_key: Optional[str] = None
    gemini_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: Optional[float] = None
    action_recommendation: Optional[str] = None
    needs_human_review: bool
    prompt_version: str
    model: str
    data_version: int
    error_message: Optional[str] = None


class AuditLogDetail(AuditLogItem):
    execution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    parsed_execution_steps: Optional[List[Dict[str, Any]]] = None
    parsed_evidence: Optional[Dict[str, Any]] = None
    copilot_response: Optional[str] = None
    fallback_reason: Optional[str] = None


class AuditLogsResponse(BaseModel):
    total_count: int
    total: int
    page: int
    page_size: int
    total_pages: int
    logs: List[AuditLogItem]


class GeminiUsageResponse(BaseModel):
    total_copilot_requests: int
    total_interactions: int
    total_gemini_calls: int
    cache_hits: int
    total_cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    cache_hit_rate_pct: float
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    active_cached_entries: int = 0
    estimated_cost_display: str = "Cost unavailable"
    cost_note: str = "Live Gemini billing API is unavailable; exact verified token counts are tracked."
    data_version: int
    current_data_version: int
