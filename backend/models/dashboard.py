from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.models.recommendation import RecommendationItem


class DashboardScope(BaseModel):
    store_id: Optional[int] = None
    store_name: Optional[str] = None
    category: Optional[str] = None


class DashboardKPIs(BaseModel):
    total_products: int
    total_stores: int
    high_stockout_risks: int
    medium_stockout_risks: int
    overstocked_items: int
    severe_overstock_count: int
    no_recent_demand_count: int
    slow_moving_count: int
    sales_spikes: int
    sales_drops: int
    total_sales_signals: int
    urgent_action_items: int


class InventoryHealthSummary(BaseModel):
    total_evaluated_skus: int
    healthy_count: int
    high_risk_count: int
    medium_risk_count: int
    overstock_count: int
    severe_overstock_count: int
    no_recent_demand_count: int
    slow_moving_count: int


class SalesHealthSummary(BaseModel):
    spike_count: int
    drop_count: int
    total_signals: int
    largest_spike: Optional[Dict[str, Any]] = None
    largest_drop: Optional[Dict[str, Any]] = None


class StorePerformanceRow(BaseModel):
    store_id: int
    store_name: str
    store_code: str
    high_stockouts: int
    medium_stockouts: int
    overstocked_items: int
    severe_overstock_count: int
    sales_spikes: int
    sales_drops: int
    urgent_action_count: int


class DashboardSummaryResponse(BaseModel):
    generated_at: str
    scope: DashboardScope
    kpis: DashboardKPIs
    attention: List[RecommendationItem] = Field(default_factory=list)
    inventory_summary: InventoryHealthSummary
    sales_summary: SalesHealthSummary
    store_breakdown: List[StorePerformanceRow] = Field(default_factory=list)
