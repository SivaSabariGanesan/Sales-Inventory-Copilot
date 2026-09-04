from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import logging
from backend.models.product import ProductListResponse
from backend.services.product_service import ProductService

logger = logging.getLogger("retail_copilot.routes.products")

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def get_products(
    search: Optional[str] = Query(None, description="Search products by title or SKU"),
    category: Optional[str] = Query(None, description="Filter products by category"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Max records to return"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Retrieve master product catalog records from the database with search and category filtering.
    """
    try:
        return ProductService.get_products(
            search=search,
            category=category,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error fetching product catalog: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error fetching products: {str(e)}",
        )
