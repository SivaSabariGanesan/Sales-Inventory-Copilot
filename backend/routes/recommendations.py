from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import logging

from backend.models.recommendation import (
    RecommendationResponse,
    TodaysAttentionResponse,
)
from backend.services.recommendation_service import RecommendationService

logger = logging.getLogger("retail_copilot.routes.recommendations")

router = APIRouter(prefix="/api/recommendations", tags=["Action Recommendations"])


@router.get("", response_model=RecommendationResponse)
async def get_recommendations(
    store_id: Optional[int] = Query(None, description="Filter recommendations by store ID"),
    category: Optional[str] = Query(None, description="Filter recommendations by product category"),
    priority: Optional[str] = Query(None, description="Filter by priority: HIGH, MEDIUM, LOW, REVIEW, ALL"),
    action: Optional[str] = Query(None, description="Filter by action enum"),
):
    """
    Get grounded, prioritized business action recommendations derived from
    stockout risks, overstock inventory, and sales anomalies.
    """
    try:
        response = RecommendationService.get_recommendations(
            store_id=store_id,
            category=category,
            priority=priority,
            action=action,
        )
        return response
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error generating recommendations: {str(e)}",
        )


@router.get("/today", response_model=TodaysAttentionResponse)
async def get_todays_attention(
    limit: int = Query(5, ge=1, le=50, description="Max number of urgent attention items to return"),
):
    """
    Get highest priority actionable items for the Executive Dashboard 'Needs Attention Today' component.
    """
    try:
        response = RecommendationService.get_todays_attention(limit=limit)
        return response
    except Exception as e:
        logger.error(f"Error fetching today's attention items: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error fetching today's attention: {str(e)}",
        )
