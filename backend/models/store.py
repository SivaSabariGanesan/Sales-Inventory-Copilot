from typing import List, Optional
from pydantic import BaseModel, Field


class StoreItem(BaseModel):
    id: int
    store_code: str
    store_name: str
    city: str
    status: str = "Active"
    total_skus: Optional[int] = 0
    total_inventory_units: Optional[int] = 0
    created_at: Optional[str] = None


class StoreOverviewKPIs(BaseModel):
    total_locations: int = Field(..., description="Total active physical store locations")
    regions_covered: int = Field(..., description="Distinct cities or regions covered")
    total_skus_stocked: int = Field(0, description="Total active SKUs in inventory across all stores")
    total_inventory_units: int = Field(0, description="Total physical units in stock across all stores")


class StoreListResponse(BaseModel):
    kpis: StoreOverviewKPIs
    stores: List[StoreItem] = Field(default_factory=list, description="List of physical retail stores")
