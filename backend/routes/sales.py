from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import logging

from backend.services.sales_anomaly_service import (
    SalesAnomalyService,
    SalesAnomalyResponse,
    RECENT_DAYS,
    BASELINE_DAYS,
)

logger = logging.getLogger("retail_copilot.routes.sales")

router = APIRouter(prefix="/api/sales", tags=["Sales Analytics"])


@router.get("/anomalies", response_model=SalesAnomalyResponse)
async def get_sales_anomalies(
    store_id: Optional[int] = Query(None, description="Filter anomalies by store ID"),
    category: Optional[str] = Query(None, description="Filter anomalies by product category"),
    status: Optional[str] = Query(None, description="Filter by status: SPIKE, DROP, INSUFFICIENT_BASELINE, NORMAL, ALL"),
    recent_days: int = Query(RECENT_DAYS, ge=1, le=90, description="Recent demand window in calendar days"),
    baseline_days: int = Query(BASELINE_DAYS, ge=1, le=180, description="Baseline demand window in calendar days"),
):
    """
    Get detected sales velocity anomalies (spikes and drops) comparing
    the recent period with the preceding baseline window.
    """
    try:
        response = SalesAnomalyService.calculate_anomalies(
            store_id=store_id,
            category=category,
            status_filter=status,
            recent_days=recent_days,
            baseline_days=baseline_days,
        )
        return response
    except Exception as e:
        logger.error(f"Error calculating sales anomalies: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error calculating sales anomalies: {str(e)}",
        )
