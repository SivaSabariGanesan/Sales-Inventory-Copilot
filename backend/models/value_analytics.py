from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProductValueSummary(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    unit_price: float
    total_stock_quantity: int
    inventory_value: float
    total_sales_quantity: int = 0
    total_revenue: float = 0.0


class StoreValueSummary(BaseModel):
    store_id: int
    store_name: str
    store_code: str
    total_inventory_value: float
    total_revenue: float
    total_stock_units: int
    total_sales_units: int


class CategoryValueSummary(BaseModel):
    category: str
    total_inventory_value: float
    total_revenue: float
    total_stock_units: int
    total_sales_units: int


class OverstockValueSummary(BaseModel):
    total_overstock_inventory_value: float
    products_affected_count: int
    stores_affected_count: int
    severe_overstock_value: float
    moderate_overstock_value: float
    no_demand_value: float
    slow_moving_value: float
    top_contributing_product: Optional[Dict[str, Any]] = None


class ValueAnalyticsResponse(BaseModel):
    total_inventory_value: float
    total_sales_revenue: float
    overstock_inventory_value: float
    total_stock_units: int
    total_sales_units: int
    top_products_by_revenue: List[ProductValueSummary]
    top_stores_by_revenue: List[StoreValueSummary]
    top_inventory_value_products: List[ProductValueSummary]
    stores_summary: List[StoreValueSummary]
    category_summary: List[CategoryValueSummary]
    overstock_summary: OverstockValueSummary
