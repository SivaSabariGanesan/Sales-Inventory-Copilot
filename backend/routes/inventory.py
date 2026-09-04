from typing import Optional, List, Dict
from fastapi import APIRouter, Query
from backend.services.inventory_risk_service import (
    InventoryRiskService,
    StockoutRiskResponse,
    DEMAND_LOOKBACK_DAYS,
)
from backend.database.connection import get_db_connection

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/stockout-risks", response_model=StockoutRiskResponse)
async def get_stockout_risks(
    store_id: Optional[int] = Query(None, description="Filter by store ID"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (HIGH, MEDIUM, ALL)"),
    lookback_days: int = Query(DEMAND_LOOKBACK_DAYS, ge=1, le=90, description="Lookback window in days"),
):
    """
    Retrieve deterministic stock-out risks with underlying quantitative evidence,
    including average daily sales velocity and estimated days of stock remaining.
    """
    return InventoryRiskService.calculate_stockout_risks(
        store_id=store_id,
        category=category,
        risk_level_filter=risk_level,
        lookback_days=lookback_days,
    )


@router.get("/metadata")
async def get_inventory_metadata():
    """Retrieve store and category options for frontend filter bars."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, store_code, store_name, city FROM stores ORDER BY store_code")
        stores = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        categories = [row["category"] for row in cursor.fetchall()]

    return {
        "stores": stores,
        "categories": categories,
    }
