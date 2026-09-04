"""Tests for CSV Data Import, Validation, Templates, and Reset Demo functionality."""

import io
import pytest
from fastapi.testclient import TestClient
from app import app
from backend.database.connection import get_db_connection

client = TestClient(app)


def test_template_download_endpoints():
    """Verify template CSV files can be downloaded."""
    for template_name in ["products", "stores", "sales", "inventory", "all"]:
        response = client.get(f"/api/import/templates/{template_name}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert f"{template_name}_template.csv" in response.headers["content-disposition"]
        assert len(response.text) > 0


def test_template_download_invalid_name():
    """Verify invalid template name returns 404."""
    response = client.get("/api/import/templates/unknown_template")
    assert response.status_code == 404


def test_import_status_endpoint():
    """Verify import status endpoint returns current database counts."""
    response = client.get("/api/import/status")
    assert response.status_code == 200
    data = response.json()
    assert "products_count" in data
    assert "stores_count" in data
    assert "sales_count" in data
    assert "inventory_count" in data
    assert data["products_count"] > 0
    assert data["stores_count"] > 0


def test_preview_products_csv_valid():
    """Verify preview for valid products CSV."""
    csv_content = (
        "sku,product_name,category,unit_price,reorder_level\n"
        "TEST-SKU-1,Test Widget Alpha,Electronics,29.99,15\n"
        "TEST-SKU-2,Test Gadget Beta,Home Goods,12.50,5\n"
    )
    files = {"file": ("products.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/import/preview?dataset=products", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_type"] == "products"
    assert data["total_rows"] == 2
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    assert len(data["sample_rows"]) == 2


def test_preview_products_csv_invalid_columns():
    """Verify preview detects missing required columns."""
    csv_content = (
        "sku,wrong_column,unit_price\n"
        "TEST-SKU-1,Wrong,29.99\n"
    )
    files = {"file": ("products.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/import/preview?dataset=products", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("Missing required column" in err["message"] for err in data["errors"])


def test_preview_products_csv_row_errors():
    """Verify preview detects row-level errors such as invalid unit price."""
    csv_content = (
        "sku,product_name,category,unit_price,reorder_level\n"
        ",No SKU Product,Electronics,29.99,15\n"
        "TEST-SKU-VALID,Valid Product,Home Goods,15.00,10\n"
        "TEST-SKU-INVALID,Negative Price,Apparel,-5.00,10\n"
    )
    files = {"file": ("products.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/import/preview?dataset=products", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["total_rows"] == 3
    assert len(data["errors"]) >= 2


def test_preview_sales_csv_missing_foreign_keys():
    """Verify sales CSV checks for non-existent store_code and sku in database."""
    csv_content = (
        "store_code,sku,date,units_sold,unit_price,revenue\n"
        "NONEXISTENT-STORE,NONEXISTENT-SKU,2026-09-01,5,19.99,99.95\n"
    )
    files = {"file": ("sales.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/import/preview?dataset=sales", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("store_code" in err["message"] for err in data["errors"])
    assert any("SKU" in err["message"] for err in data["errors"])


def test_preview_combined_all_csv():
    """Verify preview for combined all.csv file."""
    csv_content = (
        "data_type,sku,product_name,category,unit_price,reorder_level,store_code,store_name,region,date,units_sold,revenue,stock_level\n"
        "product,NEW-COMB-1,Combined Widget,Hardware,45.00,20,,,,,,,\n"
        "store,,,,,,STORE-COMB-1,Combined Flagship,Northeast,,,,\n"
        "sale,NEW-COMB-1,,,,,STORE-COMB-1,,,2026-09-01,3,135.00,\n"
        "inventory,NEW-COMB-1,,,,,STORE-COMB-1,,,,,,50\n"
    )
    files = {"file": ("all.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/import/preview-all", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["total_rows"] == 4
    assert len(data["datasets"]) == 4
    assert data["datasets"]["products"]["total_rows"] == 1
    assert data["datasets"]["stores"]["total_rows"] == 1
    assert data["datasets"]["sales"]["total_rows"] == 1
    assert data["datasets"]["inventory"]["total_rows"] == 1


def test_combined_all_csv_import_and_persistence():
    """Verify importing all.csv commits records atomically."""
    csv_content = (
        "data_type,sku,product_name,category,unit_price,reorder_level,store_code,store_name,region,date,units_sold,revenue,stock_level\n"
        "product,AUTOTEST-PROD-99,AutoTest Prod,Electronics,99.99,10,,,,,,,\n"
        "store,,,,,,AUTOTEST-STORE-99,AutoTest Store,North,,,,\n"
        "sale,AUTOTEST-PROD-99,,,,,AUTOTEST-STORE-99,,,2026-09-01,4,399.96,\n"
        "inventory,AUTOTEST-PROD-99,,,,,AUTOTEST-STORE-99,,,,,,88\n"
    )
    files = {"file": ("all.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/import/all", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["imported_counts"]["products"] == 1
    assert data["imported_counts"]["stores"] == 1
    assert data["imported_counts"]["sales"] == 1
    assert data["imported_counts"]["inventory"] == 1

    # Verify queryable from products and stores endpoints
    prod_res = client.get("/api/products?search=AUTOTEST-PROD-99")
    assert prod_res.status_code == 200
    assert prod_res.json()["total_count"] >= 1


def test_reset_demo_data():
    """Verify reset-demo restores original seeded state cleanly."""
    response = client.post("/api/import/reset-demo")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["imported_counts"]["products"] > 0
    assert data["imported_counts"]["stores"] > 0
    assert data["imported_counts"]["sales"] > 0
    assert data["imported_counts"]["inventory"] > 0
