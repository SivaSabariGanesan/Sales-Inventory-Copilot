from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from backend.database.connection import get_db_connection

logger = logging.getLogger("retail_copilot.overstock")

# Configurable Deterministic Overstock Thresholds
DEMAND_LOOKBACK_DAYS = 30
SLOW_MOVING_MAX_DAILY_SALES = 1.0
OVERSTOCK_DAYS = 30.0
SEVERE_OVERSTOCK_DAYS = 60.0


class OverstockItem(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    store_id: int
    store_name: str
    current_stock: int
    recent_quantity_sold: int
    average_daily_sales: float
    days_of_stock: Optional[float] = None
    lookback_days: int = DEMAND_LOOKBACK_DAYS
    status: str  # "SEVERE_OVERSTOCK", "OVERSTOCK", "NO_RECENT_DEMAND", "SLOW_MOVING"
    is_slow_moving: bool = False
    is_overstocked: bool = False
    is_severely_overstocked: bool = False
    is_no_demand: bool = False
    explanation: str


class OverstockSummary(BaseModel):
    overstock_count: int
    severe_overstock_count: int
    no_recent_demand_count: int
    slow_moving_count: int
    total_attention_items: int


class OverstockResponse(BaseModel):
    generated_at: str
    lookback_days: int
    summary: OverstockSummary
    results: List[OverstockItem]


class OverstockService:
    """Service for deterministic detection of overstocked and slow-moving inventory."""

    @staticmethod
    def calculate_overstock(
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        lookback_days: int = DEMAND_LOOKBACK_DAYS,
    ) -> OverstockResponse:
        """
        Calculate overstock and slow-moving inventory across store-product pairs.
        Returns results ranked by business urgency.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Determine reference date (latest sale date in database)
            cursor.execute("SELECT MAX(sale_date) FROM sales")
            max_date_row = cursor.fetchone()
            if not max_date_row or not max_date_row[0]:
                return OverstockResponse(
                    generated_at=datetime.utcnow().isoformat(),
                    lookback_days=lookback_days,
                    summary=OverstockSummary(
                        overstock_count=0,
                        severe_overstock_count=0,
                        no_recent_demand_count=0,
                        slow_moving_count=0,
                        total_attention_items=0,
                    ),
                    results=[],
                )

            latest_sale_date = datetime.fromisoformat(max_date_row[0]).date()
            start_date = latest_sale_date - timedelta(days=lookback_days - 1)
            start_date_str = start_date.isoformat()
            latest_date_str = latest_sale_date.isoformat()

            # 2. Query inventory joined with sales in 30-day window
            query = """
            SELECT
                i.store_id,
                st.store_name,
                i.product_id,
                p.sku,
                p.product_name,
                p.category,
                p.unit_price,
                i.stock_quantity as current_stock,
                COALESCE(SUM(s.quantity), 0) as recent_quantity_sold
            FROM inventory i
            JOIN stores st ON i.store_id = st.id
            JOIN products p ON i.product_id = p.id
            LEFT JOIN sales s ON s.store_id = i.store_id
                             AND s.product_id = i.product_id
                             AND s.sale_date >= ?
                             AND s.sale_date <= ?
            WHERE (? IS NULL OR i.store_id = ?)
              AND (? IS NULL OR p.category = ?)
            GROUP BY i.store_id, i.product_id
            """

            cursor.execute(
                query,
                (start_date_str, latest_date_str, store_id, store_id, category, category),
            )
            rows = cursor.fetchall()

            flagged_items: List[OverstockItem] = []

            for row in rows:
                c_stock = max(0, int(row["current_stock"]))
                qty_sold = max(0, int(row["recent_quantity_sold"]))

                # Edge case: Zero inventory has no excess stock
                if c_stock == 0:
                    continue

                # Case A: Zero demand with positive inventory
                if qty_sold == 0:
                    avg_daily_sales = 0.0
                    days_of_stock = None
                    status = "NO_RECENT_DEMAND"
                    is_no_demand = True
                    is_slow_moving = False
                    is_overstocked = False
                    is_severely_overstocked = False
                    explanation = (
                        f"{c_stock} units are currently in stock, but the product recorded no sales during the last "
                        f"{lookback_days} days. There is not enough recent demand evidence to estimate days of stock."
                    )
                else:
                    # Case B: Positive demand with positive inventory
                    raw_daily_sales = qty_sold / float(lookback_days)
                    avg_daily_sales = round(raw_daily_sales, 2)
                    days_of_stock = round(c_stock / raw_daily_sales, 2)

                    is_no_demand = False
                    is_slow_moving = (raw_daily_sales <= SLOW_MOVING_MAX_DAILY_SALES)
                    is_severely_overstocked = (days_of_stock > SEVERE_OVERSTOCK_DAYS)
                    is_overstocked = (days_of_stock > OVERSTOCK_DAYS and not is_severely_overstocked)

                    # Determine primary status
                    if is_severely_overstocked:
                        status = "SEVERE_OVERSTOCK"
                        explanation = (
                            f"{c_stock} units are currently in stock. The product sold {qty_sold} units during the last "
                            f"{lookback_days} days, averaging {avg_daily_sales:.2f} units/day. "
                            f"At current sales rate, approximately {days_of_stock:.1f} days of inventory remain (severe overstock)."
                        )
                    elif is_overstocked:
                        status = "OVERSTOCK"
                        explanation = (
                            f"{c_stock} units are currently in stock. The product sold {qty_sold} units during the last "
                            f"{lookback_days} days, averaging {avg_daily_sales:.2f} units/day. "
                            f"At current sales rate, approximately {days_of_stock:.1f} days of inventory remain (overstocked)."
                        )
                    elif is_slow_moving:
                        status = "SLOW_MOVING"
                        explanation = (
                            f"{c_stock} units are currently in stock. Sales velocity is low ({qty_sold} units in {lookback_days} days, "
                            f"averaging {avg_daily_sales:.2f} units/day), with {days_of_stock:.1f} days of stock on hand."
                        )
                    else:
                        # Normal inventory - healthy stock turnover
                        continue

                # Status filtering
                if status_filter and status_filter.upper() != "ALL":
                    if status != status_filter.upper():
                        continue

                flagged_items.append(
                    OverstockItem(
                        product_id=row["product_id"],
                        sku=row["sku"],
                        product_name=row["product_name"],
                        category=row["category"],
                        store_id=row["store_id"],
                        store_name=row["store_name"],
                        current_stock=c_stock,
                        recent_quantity_sold=qty_sold,
                        average_daily_sales=round(avg_daily_sales, 2),
                        days_of_stock=days_of_stock,
                        lookback_days=lookback_days,
                        status=status,
                        is_slow_moving=is_slow_moving,
                        is_overstocked=is_overstocked,
                        is_severely_overstocked=is_severely_overstocked,
                        is_no_demand=is_no_demand,
                        explanation=explanation,
                    )
                )

            # 3. Ranking / Sorting by business urgency
            # Urgency order: SEVERE_OVERSTOCK (0) > NO_RECENT_DEMAND (1) > OVERSTOCK (2) > SLOW_MOVING (3)
            status_priority = {
                "SEVERE_OVERSTOCK": 0,
                "NO_RECENT_DEMAND": 1,
                "OVERSTOCK": 2,
                "SLOW_MOVING": 3,
            }

            flagged_items.sort(
                key=lambda item: (
                    status_priority.get(item.status, 99),
                    -(item.days_of_stock if item.days_of_stock is not None else -1),
                    -item.current_stock,
                )
            )

            # 4. Compute summary metrics
            severe_count = sum(1 for item in flagged_items if item.status == "SEVERE_OVERSTOCK")
            overstock_count = sum(1 for item in flagged_items if item.status in ("OVERSTOCK", "SEVERE_OVERSTOCK"))
            no_demand_count = sum(1 for item in flagged_items if item.status == "NO_RECENT_DEMAND")
            slow_moving_count = sum(1 for item in flagged_items if item.is_slow_moving or item.status == "SLOW_MOVING")
            total_attention = len(flagged_items)

            summary = OverstockSummary(
                overstock_count=overstock_count,
                severe_overstock_count=severe_count,
                no_recent_demand_count=no_demand_count,
                slow_moving_count=slow_moving_count,
                total_attention_items=total_attention,
            )

            return OverstockResponse(
                generated_at=datetime.utcnow().isoformat(),
                lookback_days=lookback_days,
                summary=summary,
                results=flagged_items,
            )
