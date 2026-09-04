from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from backend.models.recommendation import (
    RecommendationActionEnum,
    RecommendationPriorityEnum,
    RecommendationItem,
    RecommendationSummary,
    RecommendationResponse,
    TodaysAttentionResponse,
)
from backend.services.inventory_risk_service import InventoryRiskService
from backend.services.overstock_service import OverstockService
from backend.services.sales_anomaly_service import SalesAnomalyService

logger = logging.getLogger("retail_copilot.recommendations")


class RecommendationService:
    """Deterministic recommendation engine grounded in Features 1, 2, and 3 analytics."""

    @classmethod
    def get_recommendations(
        cls,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        action: Optional[str] = None,
    ) -> RecommendationResponse:
        """
        Generates structured, prioritized recommendations with deduplication and evidence grounding.
        """
        items = cls._evaluate_all_conditions(store_id=store_id, category=category)

        # Apply filters
        if priority and priority.upper() != "ALL":
            items = [item for item in items if item.priority.value == priority.upper()]
        if action and action.upper() != "ALL":
            items = [item for item in items if item.action.value == action.upper()]

        # Sort results: HIGH -> MEDIUM -> LOW -> REVIEW
        priority_order = {
            RecommendationPriorityEnum.HIGH: 0,
            RecommendationPriorityEnum.MEDIUM: 1,
            RecommendationPriorityEnum.LOW: 2,
            RecommendationPriorityEnum.REVIEW: 3,
        }
        items.sort(key=lambda x: (priority_order.get(x.priority, 99), -float(x.evidence_metrics.get("urgency_score", 0))))

        summary = RecommendationSummary(
            high_priority_count=sum(1 for i in items if i.priority == RecommendationPriorityEnum.HIGH),
            medium_priority_count=sum(1 for i in items if i.priority == RecommendationPriorityEnum.MEDIUM),
            low_priority_count=sum(1 for i in items if i.priority == RecommendationPriorityEnum.LOW),
            review_count=sum(1 for i in items if i.priority == RecommendationPriorityEnum.REVIEW),
            total_recommendations=len(items),
        )

        return RecommendationResponse(
            generated_at=datetime.utcnow().isoformat(),
            summary=summary,
            results=items,
        )

    @classmethod
    def get_todays_attention(cls, limit: int = 5) -> TodaysAttentionResponse:
        """
        Returns top prioritized actionable items across stock-out, overstock, and anomalies.
        Used for the Executive Dashboard 'Needs Attention Today' component.
        """
        response = cls.get_recommendations()
        top_items = response.results[:limit]
        return TodaysAttentionResponse(
            generated_at=datetime.utcnow().isoformat(),
            count=len(top_items),
            results=top_items,
        )

    @classmethod
    def _evaluate_all_conditions(
        cls,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[RecommendationItem]:
        """
        Fetches underlying analytics, detects conditions, and merges multi-condition items
        following strict business precedence.
        """
        # 1. Fetch deterministic results
        stockout_res = InventoryRiskService.calculate_stockout_risks(store_id=store_id, category=category)
        overstock_res = OverstockService.calculate_overstock(store_id=store_id, category=category)
        sales_res = SalesAnomalyService.calculate_anomalies(store_id=store_id, category=category)

        # Map by (store_id, product_id)
        stockout_map = { (r.store_id, r.product_id): r for r in stockout_res.results }
        overstock_map = { (r.store_id, r.product_id): r for r in overstock_res.results }
        sales_map = { (r.store_id, r.product_id): r for r in sales_res.results }

        all_keys = set(stockout_map.keys()) | set(overstock_map.keys()) | set(sales_map.keys())
        recommendations: List[RecommendationItem] = []

        for key in all_keys:
            st_id, pr_id = key
            so_item = stockout_map.get(key)
            os_item = overstock_map.get(key)
            sa_item = sales_map.get(key)

            # Extract base item metadata
            meta = so_item or os_item or sa_item
            product_name = meta.product_name
            sku = meta.sku
            cat = meta.category
            store_name = meta.store_name
            rec_id = f"REC-{st_id}-{pr_id}"

            # --- PRECEDENCE EVALUATION ---

            # Case A: HIGH Stock-out risk (Optionally combined with Sales Spike)
            if so_item and so_item.risk_level == "HIGH":
                is_spike = (sa_item and sa_item.status == "SPIKE")
                if is_spike:
                    rec_text = "Replenish as a priority and review whether demand has shifted upward."
                    reason = (
                        f"Only {so_item.estimated_days_remaining:.1f} days of stock remain, "
                        f"compounded by a recent {sa_item.percentage_change:+.1f}% demand surge."
                    )
                    title = f"Urgent Replenishment & Demand Spike ({product_name})"
                else:
                    rec_text = "Replenish stock as a priority."
                    reason = f"Estimated stock remaining is {so_item.estimated_days_remaining:.1f} days (<= 3 days threshold)."
                    title = f"Critical Stock-Out Risk ({product_name})"

                evidence = {
                    "current_stock": so_item.current_stock,
                    "average_daily_sales": so_item.average_daily_sales,
                    "days_remaining": so_item.estimated_days_remaining,
                    "risk_level": "HIGH",
                    "urgency_score": 100 - so_item.estimated_days_remaining,
                }
                if is_spike:
                    evidence["sales_spike_pct"] = sa_item.percentage_change

                assumptions = [
                    "Demand estimated over the last 14 days of historical sales.",
                    "High risk defined as 3 or fewer estimated days of stock.",
                ]
                if is_spike:
                    assumptions.append("Sales spike defined as recent 7-day velocity >= 50% above 30-day baseline.")

                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.REPLENISH_NOW,
                        priority=RecommendationPriorityEnum.HIGH,
                        title=title,
                        recommendation=rec_text,
                        reason=reason,
                        evidence_metrics=evidence,
                        assumptions=assumptions,
                        needs_human_review=False,
                        confidence="HIGH",
                    )
                )
                continue

            # Case B: MEDIUM Stock-out risk
            if so_item and so_item.risk_level == "MEDIUM":
                is_spike = (sa_item and sa_item.status == "SPIKE")
                rec_text = "Plan replenishment soon and monitor demand."
                reason = f"Estimated stock remaining is {so_item.estimated_days_remaining:.1f} days (between 3 and 7 days)."
                title = f"Impending Stock Depletion ({product_name})"

                evidence = {
                    "current_stock": so_item.current_stock,
                    "average_daily_sales": so_item.average_daily_sales,
                    "days_remaining": so_item.estimated_days_remaining,
                    "risk_level": "MEDIUM",
                    "urgency_score": 50 - so_item.estimated_days_remaining,
                }
                assumptions = [
                    "Demand estimated over the last 14 days of sales.",
                    "Medium risk defined as between 3 and 7 estimated days of stock.",
                ]

                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.PLAN_REPLENISHMENT,
                        priority=RecommendationPriorityEnum.MEDIUM,
                        title=title,
                        recommendation=rec_text,
                        reason=reason,
                        evidence_metrics=evidence,
                        assumptions=assumptions,
                        needs_human_review=False,
                        confidence="HIGH",
                    )
                )
                continue

            # Case C: SEVERE OVERSTOCK (Optionally combined with Sales Drop)
            if os_item and os_item.status == "SEVERE_OVERSTOCK":
                is_drop = (sa_item and sa_item.status == "DROP")
                if is_drop:
                    rec_text = "Halt upcoming replenishment and investigate recent sales drop."
                    reason = (
                        f"Excess inventory ({os_item.days_of_stock:.1f} days of supply) is compounded by a "
                        f"{abs(sa_item.percentage_change):.1f}% sales decline."
                    )
                    title = f"Severe Overstock & Sales Contraction ({product_name})"
                    needs_human_review = True
                else:
                    rec_text = "Review purchasing and consider reducing future replenishment."
                    reason = f"Estimated stock is {os_item.days_of_stock:.1f} days, exceeding the 60-day severe overstock threshold."
                    title = f"Severe Overstock Alert ({product_name})"
                    needs_human_review = False

                evidence = {
                    "current_stock": os_item.current_stock,
                    "average_daily_sales": os_item.average_daily_sales,
                    "days_of_stock": os_item.days_of_stock,
                    "status": "SEVERE_OVERSTOCK",
                    "urgency_score": 40 + min(50, os_item.days_of_stock / 2),
                }
                if is_drop:
                    evidence["sales_drop_pct"] = sa_item.percentage_change

                assumptions = [
                    "Overstock demand modeled over last 30 calendar days.",
                    "Severe overstock defined as exceeding 60 days of stock on hand.",
                ]

                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.REDUCE_FUTURE_REPLENISHMENT,
                        priority=RecommendationPriorityEnum.MEDIUM,
                        title=title,
                        recommendation=rec_text,
                        reason=reason,
                        evidence_metrics=evidence,
                        assumptions=assumptions,
                        needs_human_review=needs_human_review,
                        confidence="HIGH",
                    )
                )
                continue

            # Case D: Isolated Sales Drop
            if sa_item and sa_item.status == "DROP":
                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.INVESTIGATE_SALES_DECLINE,
                        priority=RecommendationPriorityEnum.MEDIUM,
                        title=f"Significant Sales Drop ({product_name})",
                        recommendation="Investigate the sales decline before increasing inventory.",
                        reason=f"Sales velocity contracted by {abs(sa_item.percentage_change):.1f}% ({sa_item.recent_average_daily_sales:.2f}/day recent vs {sa_item.baseline_average_daily_sales:.2f}/day baseline).",
                        evidence_metrics={
                            "recent_avg_sales": sa_item.recent_average_daily_sales,
                            "baseline_avg_sales": sa_item.baseline_average_daily_sales,
                            "percentage_change": sa_item.percentage_change,
                            "urgency_score": 35 + abs(sa_item.percentage_change) / 5,
                        },
                        assumptions=[
                            "Sales anomaly compares recent 7 days against 30-day baseline.",
                            "Sales drop defined as velocity decline >= 40% with baseline >= 2 units/day.",
                        ],
                        needs_human_review=True,
                        confidence="MEDIUM",
                    )
                )
                continue

            # Case E: Isolated Sales Spike
            if sa_item and sa_item.status == "SPIKE":
                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.REVIEW_SALES_SPIKE,
                        priority=RecommendationPriorityEnum.MEDIUM,
                        title=f"Demand Surge ({product_name})",
                        recommendation="Review inventory availability and consider whether additional replenishment is needed.",
                        reason=f"Sales velocity increased by {sa_item.percentage_change:+.1f}% ({sa_item.recent_average_daily_sales:.2f}/day recent vs {sa_item.baseline_average_daily_sales:.2f}/day baseline).",
                        evidence_metrics={
                            "recent_avg_sales": sa_item.recent_average_daily_sales,
                            "baseline_avg_sales": sa_item.baseline_average_daily_sales,
                            "percentage_change": sa_item.percentage_change,
                            "urgency_score": 30 + sa_item.percentage_change / 5,
                        },
                        assumptions=[
                            "Sales anomaly compares recent 7 days against 30-day baseline.",
                            "Sales spike defined as velocity increase >= 50% with baseline >= 2 units/day.",
                        ],
                        needs_human_review=False,
                        confidence="HIGH",
                    )
                )
                continue

            # Case F: Moderate OVERSTOCK
            if os_item and os_item.status == "OVERSTOCK":
                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.REVIEW_INVENTORY,
                        priority=RecommendationPriorityEnum.MEDIUM,
                        title=f"Inventory Overstock ({product_name})",
                        recommendation="Review inventory levels and consider reducing upcoming replenishment.",
                        reason=f"Estimated stock is {os_item.days_of_stock:.1f} days, exceeding the 30-day overstock threshold.",
                        evidence_metrics={
                            "current_stock": os_item.current_stock,
                            "average_daily_sales": os_item.average_daily_sales,
                            "days_of_stock": os_item.days_of_stock,
                            "urgency_score": 25 + os_item.days_of_stock / 3,
                        },
                        assumptions=[
                            "Demand modeled over 30 calendar days.",
                            "Overstock defined as exceeding 30 days of inventory supply.",
                        ],
                        needs_human_review=False,
                        confidence="HIGH",
                    )
                )
                continue

            # Case G: NO RECENT DEMAND
            if os_item and os_item.status == "NO_RECENT_DEMAND":
                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.HUMAN_REVIEW,
                        priority=RecommendationPriorityEnum.REVIEW,
                        title=f"Zero Recent Demand ({product_name})",
                        recommendation="Review whether this inventory should continue to be replenished.",
                        reason=f"{os_item.current_stock} units currently held in stock, but zero sales were recorded over the last 30 days.",
                        evidence_metrics={
                            "current_stock": os_item.current_stock,
                            "recent_sales": 0,
                            "urgency_score": 20 + min(20, os_item.current_stock / 5),
                        },
                        assumptions=[
                            "No recent demand indicates 0 sales in 30 days with stock > 0.",
                            "No recent demand alone is not sufficient evidence for product discontinuation.",
                        ],
                        needs_human_review=True,
                        confidence="REVIEW",
                    )
                )
                continue

            # Case H: SLOW MOVING
            if os_item and (os_item.is_slow_moving or os_item.status == "SLOW_MOVING"):
                recommendations.append(
                    RecommendationItem(
                        id=rec_id,
                        product_id=pr_id,
                        sku=sku,
                        product_name=product_name,
                        category=cat,
                        store_id=st_id,
                        store_name=store_name,
                        action=RecommendationActionEnum.MONITOR_DEMAND,
                        priority=RecommendationPriorityEnum.LOW,
                        title=f"Slow-Moving SKU ({product_name})",
                        recommendation="Monitor demand and avoid unnecessary additional replenishment.",
                        reason=f"Sales velocity is {os_item.average_daily_sales:.2f} units/day (<= 1.0 unit/day threshold).",
                        evidence_metrics={
                            "current_stock": os_item.current_stock,
                            "average_daily_sales": os_item.average_daily_sales,
                            "days_of_stock": os_item.days_of_stock,
                            "urgency_score": 10,
                        },
                        assumptions=[
                            "Slow moving defined as average daily sales <= 1.0 unit/day over 30 days.",
                        ],
                        needs_human_review=False,
                        confidence="HIGH",
                    )
                )

        return recommendations
