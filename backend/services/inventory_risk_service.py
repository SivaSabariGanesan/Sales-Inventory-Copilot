from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from backend.database.connection import get_db_connection

logger = logging.getLogger("retail_copilot.inventory_risk")

# Configurable Deterministic Risk Thresholds
STOCKOUT_HIGH_DAYS = 3.0
STOCKOUT_MEDIUM_DAYS = 7.0
DEMAND_LOOKBACK_DAYS = 14


class StockoutRiskItem(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    store_id: int
    store_name: str
    current_stock: int
    unit_price: float = 0.0
    inventory_value: float = 0.0
    recent_quantity_sold: int
    average_daily_sales: float
    estimated_days_remaining: Optional[float] = None
    risk_level: str  # "HIGH", "MEDIUM", "LOW"
    demand_lookback_days: int = DEMAND_LOOKBACK_DAYS
    reorder_level: Optional[float] = None
    explanation: str


class StockoutSummary(BaseModel):
    high_risk_count: int
    medium_risk_count: int
    total_at_risk: int
    most_urgent_product: Optional[str] = None
    most_urgent_store: Optional[str] = None
    min_days_remaining: Optional[float] = None


class StockoutRiskResponse(BaseModel):
    generated_at: str
    lookback_days: int
    summary: StockoutSummary
    results: List[StockoutRiskItem]


class InventoryRiskService:
    """Service for deterministic calculation of stock-out risks based on recent sales demand."""

    @staticmethod
    def calculate_stockout_risks(
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        risk_level_filter: Optional[str] = None,
        lookback_days: int = DEMAND_LOOKBACK_DAYS,
    ) -> StockoutRiskResponse:
        """
        Calculate stock-out risks across all store-product combinations.
        Only HIGH (<=3 days) and MEDIUM (3-7 days) risks are included by default.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Determine reference date (latest sale date in database)
            cursor.execute("SELECT MAX(sale_date) FROM sales")
            max_date_row = cursor.fetchone()
            if not max_date_row or not max_date_row[0]:
                # Empty sales table
                return StockoutRiskResponse(
                    generated_at=datetime.utcnow().isoformat(),
                    lookback_days=lookback_days,
                    summary=StockoutSummary(
                        high_risk_count=0,
                        medium_risk_count=0,
                        total_at_risk=0,
                    ),
                    results=[],
                )

            latest_sale_date = datetime.fromisoformat(max_date_row[0]).date()
            start_date = latest_sale_date - timedelta(days=lookback_days - 1)
            start_date_str = start_date.isoformat()
            latest_date_str = latest_sale_date.isoformat()

            # 2. Query inventory records joined with sales in lookback period
            query = """
            SELECT
                i.store_id,
                st.store_name,
                i.product_id,
                p.sku,
                p.product_name,
                p.category,
                COALESCE(p.unit_price, 0.0) as unit_price,
                p.reorder_level,
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

            risk_items: List[StockoutRiskItem] = []

            for row in rows:
                c_stock = row["current_stock"]
                qty_sold = row["recent_quantity_sold"]
                u_price = float(row["unit_price"] or 0.0)
                inv_val = round(c_stock * u_price, 2)

                # Edge case: Zero demand in lookback period
                if qty_sold == 0:
                    avg_daily_sales = 0.0
                    days_remaining = None
                    risk_level = "LOW"
                else:
                    avg_daily_sales = round(qty_sold / float(lookback_days), 4)

                    # Edge case: Zero stock with positive demand
                    if c_stock == 0:
                        days_remaining = 0.0
                        risk_level = "HIGH"
                    else:
                        days_remaining = round(c_stock / avg_daily_sales, 2)
                        if days_remaining <= STOCKOUT_HIGH_DAYS:
                            risk_level = "HIGH"
                        elif days_remaining <= STOCKOUT_MEDIUM_DAYS:
                            risk_level = "MEDIUM"
                        else:
                            risk_level = "LOW"

                # Filter: Include only high/medium risks unless a specific filter is set
                if risk_level_filter:
                    if risk_level_filter.upper() != "ALL" and risk_level != risk_level_filter.upper():
                        continue
                else:
                    if risk_level not in ("HIGH", "MEDIUM"):
                        continue

                # Generate deterministic explainability text
                if days_remaining is not None:
                    if days_remaining == 0.0:
                        explanation = (
                            f"Stock is depleted (0 units). The product sold {qty_sold} units during the last "
                            f"{lookback_days} days ({avg_daily_sales:.2f} units/day). Immediate replenishment is required."
                        )
                    else:
                        explanation = (
                            f"Current stock is {c_stock} units. The product sold {qty_sold} units during the last "
                            f"{lookback_days} days, averaging {avg_daily_sales:.2f} units/day. "
                            f"At current demand rate, approximately {days_remaining:.2f} days of stock remain."
                        )
                else:
                    explanation = (
                        f"Current stock is {c_stock} units. No sales were recorded during the last {lookback_days} days."
                    )

                risk_items.append(
                    StockoutRiskItem(
                        product_id=row["product_id"],
                        sku=row["sku"],
                        product_name=row["product_name"],
                        category=row["category"],
                        store_id=row["store_id"],
                        store_name=row["store_name"],
                        current_stock=c_stock,
                        unit_price=u_price,
                        inventory_value=inv_val,
                        recent_quantity_sold=qty_sold,
                        average_daily_sales=round(avg_daily_sales, 2),
                        estimated_days_remaining=days_remaining,
                        risk_level=risk_level,
                        demand_lookback_days=lookback_days,
                        reorder_level=row["reorder_level"],
                        explanation=explanation,
                    )
                )

            # 3. Sort results: HIGH severity first, then days remaining ascending (most urgent first)
            risk_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            risk_items.sort(
                key=lambda x: (
                    risk_priority.get(x.risk_level, 99),
                    x.estimated_days_remaining if x.estimated_days_remaining is not None else 99999,
                    x.current_stock,
                )
            )

            # 4. Compute summary metrics
            high_count = sum(1 for item in risk_items if item.risk_level == "HIGH")
            medium_count = sum(1 for item in risk_items if item.risk_level == "MEDIUM")
            total_count = len(risk_items)

            most_urgent_product = risk_items[0].product_name if risk_items else None
            most_urgent_store = risk_items[0].store_name if risk_items else None
            min_days = risk_items[0].estimated_days_remaining if risk_items else None

            summary = StockoutSummary(
                high_risk_count=high_count,
                medium_risk_count=medium_count,
                total_at_risk=total_count,
                most_urgent_product=most_urgent_product,
                most_urgent_store=most_urgent_store,
                min_days_remaining=min_days,
            )

            return StockoutRiskResponse(
                generated_at=datetime.utcnow().isoformat(),
                lookback_days=lookback_days,
                summary=summary,
                results=risk_items,
            )
