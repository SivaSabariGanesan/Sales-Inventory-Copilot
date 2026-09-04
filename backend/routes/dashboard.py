from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import logging

from backend.models.dashboard import DashboardSummaryResponse
from backend.services.dashboard_service import DashboardService

logger = logging.getLogger("retail_copilot.routes.dashboard")

router = APIRouter(prefix="/api/dashboard", tags=["Executive Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    store_id: Optional[int] = Query(None, description="Filter dashboard metrics by store ID"),
    category: Optional[str] = Query(None, description="Filter dashboard metrics by product category"),
):
    """
    Get consolidated executive dashboard metrics, actionable attention items,
    inventory and sales health summaries, and store breakdown matrix.
    """
    try:
        response = DashboardService.get_dashboard_summary(
            store_id=store_id,
            category=category,
        )
        return response
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error generating dashboard summary: {str(e)}",
        )
