import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from backend.models.value_analytics import ValueAnalyticsResponse
from backend.services.value_analytics_service import ValueAnalyticsService

logger = logging.getLogger("retail_copilot.routes.analytics")

router = APIRouter(prefix="/api/analytics", tags=["Financial & Value Analytics"])


@router.get("/value", response_model=ValueAnalyticsResponse)
def get_value_analytics(
    store_id: Optional[int] = Query(None, description="Filter by Store ID"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    product_id: Optional[int] = Query(None, description="Filter by Product ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for sales window"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for sales window"),
):
    """
    Retrieve deterministic inventory value, sales revenue, overstock tied-up value,
    and ranking breakdowns across products, stores, and categories.
    """
    try:
        return ValueAnalyticsService.get_value_analytics_summary(
            store_id=store_id,
            category=category,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        logger.error(f"Error computing value analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error computing value analytics: {str(e)}",
        )
