from typing import Optional, List, Dict
from fastapi import APIRouter, Query
from backend.services.inventory_risk_service import (
    InventoryRiskService,
    StockoutRiskResponse,
    DEMAND_LOOKBACK_DAYS as STOCKOUT_LOOKBACK_DAYS,
)
from backend.services.overstock_service import (
    OverstockService,
    OverstockResponse,
    DEMAND_LOOKBACK_DAYS as OVERSTOCK_LOOKBACK_DAYS,
)
from backend.database.connection import get_db_connection

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("")
@router.get("/")
async def get_all_inventory(
    store_id: Optional[int] = Query(None, description="Filter by store ID"),
    category: Optional[str] = Query(None, description="Filter by product category"),
):
    """Retrieve full inventory list with current stock quantities."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                i.id,
                i.store_id,
                s.store_name,
                s.store_code,
                i.product_id,
                p.sku,
                p.product_name,
                p.category,
                p.unit_price,
                p.reorder_level,
                i.stock_quantity,
                i.updated_at
            FROM inventory i
            JOIN stores s ON i.store_id = s.id
            JOIN products p ON i.product_id = p.id
            WHERE 1=1
        """
        params = []
        if store_id:
            query += " AND i.store_id = ?"
            params.append(store_id)
        if category and category.upper() != "ALL":
            query += " AND p.category = ?"
            params.append(category)
        query += " ORDER BY s.store_name, p.product_name"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
    return {"total_count": len(rows), "inventory": rows}


@router.get("/stockout-risks", response_model=StockoutRiskResponse)
async def get_stockout_risks(
    store_id: Optional[int] = Query(None, description="Filter by store ID"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (HIGH, MEDIUM, ALL)"),
    lookback_days: int = Query(STOCKOUT_LOOKBACK_DAYS, ge=1, le=90, description="Lookback window in days"),
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


@router.get("/overstock", response_model=OverstockResponse)
async def get_overstock_inventory(
    store_id: Optional[int] = Query(None, description="Filter by store ID"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    status: Optional[str] = Query(None, description="Filter by status (SEVERE_OVERSTOCK, OVERSTOCK, NO_RECENT_DEMAND, SLOW_MOVING, ALL)"),
    lookback_days: int = Query(OVERSTOCK_LOOKBACK_DAYS, ge=1, le=90, description="Lookback window in days"),
):
    """
    Retrieve deterministic overstocked and slow-moving inventory with evidence,
    including 30-day sales volume, daily velocity, and days of stock remaining.
    """
    return OverstockService.calculate_overstock(
        store_id=store_id,
        category=category,
        status_filter=status,
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
