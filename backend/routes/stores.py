from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import logging
from backend.models.store import StoreListResponse
from backend.services.store_service import StoreService

logger = logging.getLogger("retail_copilot.routes.stores")

router = APIRouter(prefix="/api/stores", tags=["Stores"])


@router.get("", response_model=StoreListResponse)
async def get_stores(
    search: Optional[str] = Query(None, description="Search stores by name, city, or store code"),
):
    """
    Retrieve store network locations and overview KPIs from the database.
    """
    try:
        return StoreService.get_stores(search=search)
    except Exception as e:
        logger.error(f"Error fetching stores: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error fetching stores: {str(e)}",
        )
