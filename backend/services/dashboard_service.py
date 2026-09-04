from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from backend.database.connection import get_db_connection
from backend.models.dashboard import (
    DashboardScope,
    DashboardKPIs,
    InventoryHealthSummary,
    SalesHealthSummary,
    StorePerformanceRow,
    DashboardSummaryResponse,
)
from backend.models.recommendation import RecommendationPriorityEnum
from backend.services.inventory_risk_service import InventoryRiskService
from backend.services.overstock_service import OverstockService
from backend.services.sales_anomaly_service import SalesAnomalyService
from backend.services.recommendation_service import RecommendationService

logger = logging.getLogger("retail_copilot.dashboard")


class DashboardService:
    """Consolidated aggregation service for the Executive Manager Dashboard."""

    @classmethod
    def get_dashboard_summary(
        cls,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> DashboardSummaryResponse:
        """
        Synthesizes metrics across Features 1–6 into a unified dashboard summary.
        All calculations are strictly deterministic and grounded in SQLite data.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Store Directory & Product Catalog Counts
            cursor.execute("SELECT id, store_name, store_code FROM stores ORDER BY id ASC")
            all_stores = cursor.fetchall()
            stores_map = {row["id"]: row for row in all_stores}

            cursor.execute(
                "SELECT COUNT(*) as prod_count FROM products WHERE (? IS NULL OR category = ?)",
                (category, category),
            )
            total_prods_row = cursor.fetchone()
            total_products = total_prods_row["prod_count"] if total_prods_row else 0

            cursor.execute(
                "SELECT COUNT(*) as inv_count FROM inventory i JOIN products p ON i.product_id = p.id WHERE (? IS NULL OR i.store_id = ?) AND (? IS NULL OR p.category = ?)",
                (store_id, store_id, category, category),
            )
            inv_count_row = cursor.fetchone()
            total_inventory_records = inv_count_row["inv_count"] if inv_count_row else 0

            # Store scope resolution
            selected_store_name = stores_map[store_id]["store_name"] if store_id and store_id in stores_map else None

        # 2. Invoke Deterministic Services
        stockout_res = InventoryRiskService.calculate_stockout_risks(store_id=store_id, category=category)
        overstock_res = OverstockService.calculate_overstock(store_id=store_id, category=category)
        sales_res = SalesAnomalyService.calculate_anomalies(store_id=store_id, category=category)
        recommendations_res = RecommendationService.get_recommendations(store_id=store_id, category=category)

        # 3. Aggregate Top-Level KPIs
        high_stockouts = stockout_res.summary.high_risk_count
        med_stockouts = stockout_res.summary.medium_risk_count
        severe_overstock = overstock_res.summary.severe_overstock_count
        overstocked_items = overstock_res.summary.overstock_count
        no_demand = overstock_res.summary.no_recent_demand_count
        slow_moving = overstock_res.summary.slow_moving_count

        sales_spikes = sales_res.summary.spike_count
        sales_drops = sales_res.summary.drop_count
        total_signals = sales_spikes + sales_drops

        urgent_actions = sum(1 for item in recommendations_res.results if item.priority == RecommendationPriorityEnum.HIGH)

        kpis = DashboardKPIs(
            total_products=total_products,
            total_stores=1 if store_id else len(all_stores),
            high_stockout_risks=high_stockouts,
            medium_stockout_risks=med_stockouts,
            overstocked_items=overstocked_items,
            severe_overstock_count=severe_overstock,
            no_recent_demand_count=no_demand,
            slow_moving_count=slow_moving,
            sales_spikes=sales_spikes,
            sales_drops=sales_drops,
            total_sales_signals=total_signals,
            urgent_action_items=urgent_actions,
        )

        # 4. Inventory Health Summary
        unhealthy_count = high_stockouts + med_stockouts + overstocked_items + no_demand
        healthy_count = max(0, total_inventory_records - unhealthy_count)

        inventory_summary = InventoryHealthSummary(
            total_evaluated_skus=total_inventory_records,
            healthy_count=healthy_count,
            high_risk_count=high_stockouts,
            medium_risk_count=med_stockouts,
            overstock_count=overstocked_items,
            severe_overstock_count=severe_overstock,
            no_recent_demand_count=no_demand,
            slow_moving_count=slow_moving,
        )

        # 5. Sales Health Summary & Extrema
        spike_items = [r for r in sales_res.results if r.status == "SPIKE" and r.percentage_change is not None]
        drop_items = [r for r in sales_res.results if r.status == "DROP" and r.percentage_change is not None]

        largest_spike = None
        if spike_items:
            best_spike = max(spike_items, key=lambda x: x.percentage_change or 0)
            largest_spike = {
                "product": best_spike.product_name,
                "sku": best_spike.sku,
                "store": best_spike.store_name,
                "change_pct": best_spike.percentage_change,
                "recent_avg": best_spike.recent_average_daily_sales,
                "baseline_avg": best_spike.baseline_average_daily_sales,
            }

        largest_drop = None
        if drop_items:
            worst_drop = min(drop_items, key=lambda x: x.percentage_change or 0)
            largest_drop = {
                "product": worst_drop.product_name,
                "sku": worst_drop.sku,
                "store": worst_drop.store_name,
                "change_pct": worst_drop.percentage_change,
                "recent_avg": worst_drop.recent_average_daily_sales,
                "baseline_avg": worst_drop.baseline_average_daily_sales,
            }

        sales_summary = SalesHealthSummary(
            spike_count=sales_spikes,
            drop_count=sales_drops,
            total_signals=total_signals,
            largest_spike=largest_spike,
            largest_drop=largest_drop,
        )

        # 6. Store Network Breakdown Table
        store_rows: List[StorePerformanceRow] = []

        # If a single store filter is active, only compute that store; otherwise compute all stores
        target_stores = [stores_map[store_id]] if (store_id and store_id in stores_map) else all_stores

        for st in target_stores:
            s_id = st["id"]
            # Fetch per-store deterministic analytics
            s_stockout = InventoryRiskService.calculate_stockout_risks(store_id=s_id, category=category)
            s_overstock = OverstockService.calculate_overstock(store_id=s_id, category=category)
            s_sales = SalesAnomalyService.calculate_anomalies(store_id=s_id, category=category)
            s_recs = RecommendationService.get_recommendations(store_id=s_id, category=category)

            s_high_so = s_stockout.summary.high_risk_count
            s_med_so = s_stockout.summary.medium_risk_count
            s_os = s_overstock.summary.overstock_count
            s_severe_os = s_overstock.summary.severe_overstock_count
            s_spikes = s_sales.summary.spike_count
            s_drops = s_sales.summary.drop_count
            s_urgent = sum(1 for r in s_recs.results if r.priority == RecommendationPriorityEnum.HIGH)

            store_rows.append(
                StorePerformanceRow(
                    store_id=s_id,
                    store_name=st["store_name"],
                    store_code=st["store_code"],
                    high_stockouts=s_high_so,
                    medium_stockouts=s_med_so,
                    overstocked_items=s_os,
                    severe_overstock_count=s_severe_os,
                    sales_spikes=s_spikes,
                    sales_drops=s_drops,
                    urgent_action_count=s_urgent,
                )
            )

        # 7. Needs Attention Today (Top 6 actionable recommendations)
        top_attention = recommendations_res.results[:6]

        return DashboardSummaryResponse(
            generated_at=datetime.utcnow().isoformat(),
            scope=DashboardScope(
                store_id=store_id,
                store_name=selected_store_name,
                category=category,
            ),
            kpis=kpis,
            attention=top_attention,
            inventory_summary=inventory_summary,
            sales_summary=sales_summary,
            store_breakdown=store_rows,
        )
