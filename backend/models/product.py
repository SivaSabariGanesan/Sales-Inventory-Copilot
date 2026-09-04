from typing import List, Optional
from pydantic import BaseModel, Field


class ProductItem(BaseModel):
    id: int
    sku: str
    product_name: str
    category: str
    unit_price: float
    reorder_level: float
    created_at: Optional[str] = None


class ProductListResponse(BaseModel):
    total_count: int = Field(..., description="Total products in master catalog")
    filtered_count: int = Field(..., description="Count matching current search and category filters")
    categories: List[str] = Field(default_factory=list, description="All available product categories")
    products: List[ProductItem] = Field(default_factory=list, description="Product catalog items")
