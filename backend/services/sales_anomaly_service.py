from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from backend.database.connection import get_db_connection

logger = logging.getLogger("retail_copilot.sales_anomaly")

# Configurable Deterministic Sales Anomaly Thresholds
RECENT_DAYS = 7
BASELINE_DAYS = 30
SPIKE_PERCENT_THRESHOLD = 50.0
DROP_PERCENT_THRESHOLD = -40.0
MIN_BASELINE_DAILY_SALES = 2.0


class SalesAnomalyItem(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    store_id: int
    store_name: str
    recent_days: int = RECENT_DAYS
    baseline_days: int = BASELINE_DAYS
    recent_quantity_sold: int
    baseline_quantity_sold: int
    recent_average_daily_sales: float
    baseline_average_daily_sales: float
    absolute_change: float
    percentage_change: Optional[float] = None
    status: str  # "SPIKE", "DROP", "NORMAL", "INSUFFICIENT_BASELINE"
    explanation: str


class SalesAnomalySummary(BaseModel):
    spike_count: int
    drop_count: int
    total_signals: int
    largest_change_pct: Optional[float] = None
    insufficient_baseline_count: int


class SalesAnomalyResponse(BaseModel):
    generated_at: str
    recent_days: int
    baseline_days: int
    recent_start_date: str
    recent_end_date: str
    baseline_start_date: str
    baseline_end_date: str
    summary: SalesAnomalySummary
    results: List[SalesAnomalyItem]


class SalesAnomalyService:
    """Service for deterministic detection of sales velocity spikes and drops."""

    @staticmethod
    def calculate_anomalies(
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        recent_days: int = RECENT_DAYS,
        baseline_days: int = BASELINE_DAYS,
    ) -> SalesAnomalyResponse:
        """
        Calculates sales anomalies by comparing recent period (last `recent_days`)
        with preceding baseline period (`baseline_days` prior to recent period).
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Determine reference date (latest sale date in database)
            cursor.execute("SELECT MAX(sale_date) FROM sales")
            max_date_row = cursor.fetchone()
            if not max_date_row or not max_date_row[0]:
                return SalesAnomalyResponse(
                    generated_at=datetime.utcnow().isoformat(),
                    recent_days=recent_days,
                    baseline_days=baseline_days,
                    recent_start_date="",
                    recent_end_date="",
                    baseline_start_date="",
                    baseline_end_date="",
                    summary=SalesAnomalySummary(
                        spike_count=0,
                        drop_count=0,
                        total_signals=0,
                        largest_change_pct=None,
                        insufficient_baseline_count=0,
                    ),
                    results=[],
                )

            latest_sale_date = datetime.fromisoformat(max_date_row[0]).date()

            # Non-overlapping date windows
            # Recent: [latest_sale_date - (recent_days - 1), latest_sale_date]
            # Baseline: [latest_sale_date - (recent_days + baseline_days - 1), latest_sale_date - recent_days]
            recent_end = latest_sale_date
            recent_start = latest_sale_date - timedelta(days=recent_days - 1)

            baseline_end = latest_sale_date - timedelta(days=recent_days)
            baseline_start = latest_sale_date - timedelta(days=recent_days + baseline_days - 1)

            recent_start_str = recent_start.isoformat()
            recent_end_str = recent_end.isoformat()
            baseline_start_str = baseline_start.isoformat()
            baseline_end_str = baseline_end.isoformat()

            # 2. Query stores, products, and sales aggregations for both periods
            query = """
            SELECT
                st.id as store_id,
                st.store_name,
                p.id as product_id,
                p.sku,
                p.product_name,
                p.category,
                COALESCE(recent.qty_sold, 0) as recent_qty_sold,
                COALESCE(baseline.qty_sold, 0) as baseline_qty_sold
            FROM stores st
            CROSS JOIN products p
            LEFT JOIN (
                SELECT store_id, product_id, SUM(quantity) as qty_sold
                FROM sales
                WHERE sale_date >= ? AND sale_date <= ?
                GROUP BY store_id, product_id
            ) recent ON recent.store_id = st.id AND recent.product_id = p.id
            LEFT JOIN (
                SELECT store_id, product_id, SUM(quantity) as qty_sold
                FROM sales
                WHERE sale_date >= ? AND sale_date <= ?
                GROUP BY store_id, product_id
            ) baseline ON baseline.store_id = st.id AND baseline.product_id = p.id
            WHERE (? IS NULL OR st.id = ?)
              AND (? IS NULL OR p.category = ?)
            """

            cursor.execute(
                query,
                (
                    recent_start_str,
                    recent_end_str,
                    baseline_start_str,
                    baseline_end_str,
                    store_id,
                    store_id,
                    category,
                    category,
                ),
            )
            rows = cursor.fetchall()

            all_items: List[SalesAnomalyItem] = []

            for row in rows:
                r_qty = max(0, int(row["recent_qty_sold"]))
                b_qty = max(0, int(row["baseline_qty_sold"]))

                # Skip store/product combos with zero sales in both periods (no sales history)
                if r_qty == 0 and b_qty == 0:
                    continue

                r_avg = r_qty / float(recent_days)
                b_avg = b_qty / float(baseline_days)
                abs_change = r_avg - b_avg

                # Status & percentage determination
                if b_avg == 0:
                    pct_change = None
                    status = "INSUFFICIENT_BASELINE"
                    explanation = (
                        f"Sales averaged {r_avg:.2f} units/day ({r_qty} units) in the last {recent_days} days, "
                        f"but zero sales were recorded in the previous {baseline_days}-day baseline. "
                        f"There is not enough historical demand to make a reliable sales comparison."
                    )
                elif b_avg < MIN_BASELINE_DAILY_SALES:
                    pct_change = round(((r_avg - b_avg) / b_avg) * 100.0, 2)
                    status = "INSUFFICIENT_BASELINE"
                    explanation = (
                        f"Sales averaged {r_avg:.2f} units/day ({r_qty} units) in the last {recent_days} days compared with "
                        f"{b_avg:.2f} units/day ({b_qty} units) in the {baseline_days}-day baseline. "
                        f"Baseline demand is below the {MIN_BASELINE_DAILY_SALES:.1f} units/day minimum threshold for a reliable signal."
                    )
                else:
                    pct_change = round(((r_avg - b_avg) / b_avg) * 100.0, 2)
                    if pct_change >= SPIKE_PERCENT_THRESHOLD:
                        status = "SPIKE"
                        explanation = (
                            f"Sales averaged {r_avg:.2f} units/day during the last {recent_days} days compared with "
                            f"{b_avg:.2f} units/day during the previous {baseline_days}-day baseline, "
                            f"an increase of {abs(pct_change):.2f}%."
                        )
                    elif pct_change <= DROP_PERCENT_THRESHOLD:
                        status = "DROP"
                        explanation = (
                            f"Sales averaged {r_avg:.2f} units/day during the last {recent_days} days compared with "
                            f"{b_avg:.2f} units/day during the previous {baseline_days}-day baseline, "
                            f"a decrease of {abs(pct_change):.2f}%."
                        )
                    else:
                        status = "NORMAL"
                        explanation = (
                            f"Sales averaged {r_avg:.2f} units/day in the last {recent_days} days compared with "
                            f"{b_avg:.2f} units/day in the {baseline_days}-day baseline (change: {pct_change:+.2f}%)."
                        )

                # Filter status if requested
                if status_filter and status_filter.upper() != "ALL":
                    if status != status_filter.upper():
                        continue

                all_items.append(
                    SalesAnomalyItem(
                        product_id=row["product_id"],
                        sku=row["sku"],
                        product_name=row["product_name"],
                        category=row["category"],
                        store_id=row["store_id"],
                        store_name=row["store_name"],
                        recent_days=recent_days,
                        baseline_days=baseline_days,
                        recent_quantity_sold=r_qty,
                        baseline_quantity_sold=b_qty,
                        recent_average_daily_sales=round(r_avg, 2),
                        baseline_average_daily_sales=round(b_avg, 2),
                        absolute_change=round(abs_change, 2),
                        percentage_change=pct_change,
                        status=status,
                        explanation=explanation,
                    )
                )

            # 3. Ranking & Sorting
            # Urgency Priority: SPIKE (0) & DROP (0) > INSUFFICIENT_BASELINE (1) > NORMAL (2)
            # Within signals, sort by absolute percentage change magnitude descending
            def sort_key(item: SalesAnomalyItem):
                priority = 0 if item.status in ("SPIKE", "DROP") else (1 if item.status == "INSUFFICIENT_BASELINE" else 2)
                mag = abs(item.percentage_change) if item.percentage_change is not None else -1.0
                return (priority, -mag, -abs(item.absolute_change))

            all_items.sort(key=sort_key)

            # 4. Summary metrics
            spike_count = sum(1 for item in all_items if item.status == "SPIKE")
            drop_count = sum(1 for item in all_items if item.status == "DROP")
            insufficient_count = sum(1 for item in all_items if item.status == "INSUFFICIENT_BASELINE")
            total_signals = spike_count + drop_count

            # Find largest absolute percentage change among valid signals
            signal_pcts = [abs(item.percentage_change) for item in all_items if item.status in ("SPIKE", "DROP") and item.percentage_change is not None]
            largest_change = max(signal_pcts) if signal_pcts else None

            summary = SalesAnomalySummary(
                spike_count=spike_count,
                drop_count=drop_count,
                total_signals=total_signals,
                largest_change_pct=largest_change,
                insufficient_baseline_count=insufficient_count,
            )

            return SalesAnomalyResponse(
                generated_at=datetime.utcnow().isoformat(),
                recent_days=recent_days,
                baseline_days=baseline_days,
                recent_start_date=recent_start_str,
                recent_end_date=recent_end_str,
                baseline_start_date=baseline_start_str,
                baseline_end_date=baseline_end_str,
                summary=summary,
                results=all_items,
            )
