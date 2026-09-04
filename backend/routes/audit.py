from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.models.audit import AuditLogsResponse, AuditLogDetail, GeminiUsageResponse
from backend.services.audit_service import AuditService

router = APIRouter(tags=["Audit & Governance"])


@router.get("/api/audit", response_model=AuditLogsResponse)
def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query in question"),
    intent: Optional[str] = Query(None, description="Filter by classified intent"),
    status: Optional[str] = Query(None, description="Filter by status (success, fallback, human_review, error)"),
    cache_hit: Optional[bool] = Query(None, description="Filter by cache hit boolean"),
    needs_human_review: Optional[bool] = Query(None, description="Filter by human review requirement"),
):
    """
    Retrieve paginated audit logs for Copilot interactions with comprehensive filtering.
    """
    try:
        return AuditService.get_audit_logs(
            page=page,
            page_size=page_size,
            search=search,
            intent=intent,
            status=status,
            cache_hit=cache_hit,
            needs_human_review=needs_human_review,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {str(e)}")


@router.get("/api/audit/{log_id}", response_model=AuditLogDetail)
def get_audit_log_detail(log_id: int):
    """
    Retrieve full execution trace and evidence for a specific Copilot audit log.
    """
    log_detail = AuditService.get_audit_log_by_id(log_id)
    if not log_detail:
        raise HTTPException(status_code=404, detail=f"Audit log #{log_id} not found")
    return log_detail


@router.get("/api/usage", response_model=GeminiUsageResponse)
def get_gemini_usage():
    """
    Retrieve aggregate Gemini API telemetry, token consumption, cache performance, and cost transparency.
    """
    try:
        return AuditService.get_usage_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate usage metrics: {str(e)}")
