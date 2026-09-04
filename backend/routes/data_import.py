from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
import logging
from backend.models.import_data import (
    DatasetPreview,
    CombinedPreviewResponse,
    ImportSummaryResponse,
    ImportStatusResponse,
)
from backend.services.import_service import ImportService

logger = logging.getLogger("retail_copilot.routes.import")

router = APIRouter(prefix="/api/import", tags=["Data Import"])


@router.get("/status", response_model=ImportStatusResponse)
async def get_import_status():
    """Retrieve current database record counts."""
    return ImportService.get_status()


@router.post("/preview", response_model=DatasetPreview)
async def preview_csv(
    file: UploadFile = File(...),
    dataset_type: Optional[str] = Form(None, description="Dataset type: products, stores, sales, or inventory"),
    dataset: Optional[str] = None,
):
    """
    Validate and preview a single dataset CSV file without modifying database records.
    """
    target_type = dataset_type or dataset
    if not target_type:
        raise HTTPException(status_code=400, detail="dataset_type form field or query parameter is required.")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        return ImportService.preview_single_csv(content, file.filename or "upload.csv", target_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error processing CSV: {str(e)}")


@router.post("/preview-all", response_model=CombinedPreviewResponse)
async def preview_all_csv(
    file: UploadFile = File(...),
):
    """
    Validate and preview combined all.csv file with cross-dataset relationship checks.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        return ImportService.preview_all_csv(content, file.filename or "all.csv")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing all.csv: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error processing all.csv: {str(e)}")


@router.post("/products", response_model=ImportSummaryResponse)
async def import_products(
    file: UploadFile = File(...),
):
    """Import product catalog from CSV."""
    try:
        content = await file.read()
        return ImportService.import_single_dataset(content, file.filename or "products.csv", "products")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/stores", response_model=ImportSummaryResponse)
async def import_stores(
    file: UploadFile = File(...),
):
    """Import store network from CSV."""
    try:
        content = await file.read()
        return ImportService.import_single_dataset(content, file.filename or "stores.csv", "stores")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing stores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/sales", response_model=ImportSummaryResponse)
async def import_sales(
    file: UploadFile = File(...),
):
    """Import historical sales transactions from CSV."""
    try:
        content = await file.read()
        return ImportService.import_single_dataset(content, file.filename or "sales.csv", "sales")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing sales: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/inventory", response_model=ImportSummaryResponse)
async def import_inventory(
    file: UploadFile = File(...),
):
    """Import inventory stock levels from CSV."""
    try:
        content = await file.read()
        return ImportService.import_single_dataset(content, file.filename or "inventory.csv", "inventory")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing inventory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/all", response_model=ImportSummaryResponse)
async def import_all(
    file: UploadFile = File(...),
):
    """Import Products, Stores, Sales, and Inventory from combined all.csv atomically."""
    try:
        content = await file.read()
        return ImportService.import_all_combined(content, file.filename or "all.csv")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing combined import: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/templates/{template_name}")
async def download_template(template_name: str):
    """Download starter CSV template."""
    try:
        filename, content = ImportService.get_template(template_name)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reset-demo", response_model=ImportSummaryResponse)
async def reset_demo_dataset():
    """Reset database back to the baseline seeded synthetic dataset."""
    try:
        return ImportService.reset_demo_data()
    except Exception as e:
        logger.error(f"Error resetting demo database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")
