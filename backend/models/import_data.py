from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ValidationErrorItem(BaseModel):
    row_number: int = Field(..., description="1-indexed row number in the uploaded CSV")
    field: Optional[str] = Field(None, description="Column or attribute that failed validation")
    message: str = Field(..., description="Human-readable explanation of the validation failure")
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="Row values for debugging context")


class DatasetPreview(BaseModel):
    dataset_type: str = Field(..., description="Type of dataset: products, stores, sales, or inventory")
    filename: str = Field(..., description="Uploaded filename")
    total_rows: int = Field(..., description="Total data rows detected in the CSV")
    columns: List[str] = Field(default_factory=list, description="Detected column names")
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list, description="First 5 sample rows")
    valid: bool = Field(..., description="Whether all rows passed validation")
    errors: List[ValidationErrorItem] = Field(default_factory=list, description="List of row-level validation errors")


class CombinedPreviewResponse(BaseModel):
    filename: str = Field(..., description="Uploaded filename")
    total_rows: int = Field(..., description="Total rows in combined file")
    datasets: Dict[str, DatasetPreview] = Field(default_factory=dict, description="Previews per dataset type")
    valid: bool = Field(..., description="Whether the entire batch passed validation")
    errors: List[ValidationErrorItem] = Field(default_factory=list, description="All validation errors across datasets")


class ImportSummaryResponse(BaseModel):
    success: bool = Field(..., description="Whether the import transaction committed successfully")
    message: str = Field(..., description="User-facing summary message")
    imported_counts: Dict[str, int] = Field(default_factory=dict, description="Records inserted/updated per entity")
    timestamp: str = Field(..., description="ISO timestamp of the import event")


class ImportStatusResponse(BaseModel):
    stores_count: int
    products_count: int
    sales_count: int
    inventory_count: int
