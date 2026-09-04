import pytest
from fastapi.testclient import TestClient
from app import app
from backend.services.product_service import ProductService
from backend.services.store_service import StoreService
from backend.database.connection import get_db_connection

client = TestClient(app)


def test_products_api_seeded_catalog():
    """Verify products API returns seeded products and matches SQLite count."""
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        db_count = cursor.fetchone()[0]

    assert data["total_count"] == db_count
    assert data["filtered_count"] == db_count
    assert len(data["products"]) == db_count
    assert len(data["categories"]) > 0

    first_product = data["products"][0]
    assert "sku" in first_product
    assert "product_name" in first_product
    assert "category" in first_product
    assert "unit_price" in first_product
    assert "reorder_level" in first_product
    assert first_product["unit_price"] > 0


def test_products_api_search_and_category_filtering():
    """Verify search and category filtering on products."""
    # 1. Search by SKU
    sku_res = client.get("/api/products?search=ELEC-001")
    assert sku_res.status_code == 200
    sku_data = sku_res.json()
    assert sku_data["filtered_count"] >= 1
    assert any("ELEC-001" in p["sku"] for p in sku_data["products"])

    # 2. Search by Name
    name_res = client.get("/api/products?search=Headphones")
    assert name_res.status_code == 200
    name_data = name_res.json()
    assert len(name_data["products"]) >= 1
    assert all("Headphones".lower() in p["product_name"].lower() or "Headphones".lower() in p["sku"].lower() for p in name_data["products"])

    # 3. Filter by Category
    cat = sku_data["products"][0]["category"]
    cat_res = client.get(f"/api/products?category={cat}")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    assert cat_data["filtered_count"] > 0
    assert all(p["category"] == cat for p in cat_data["products"])

    # 4. Non-matching search
    empty_res = client.get("/api/products?search=NonExistentProductXYZ123")
    assert empty_res.status_code == 200
    empty_data = empty_res.json()
    assert empty_data["filtered_count"] == 0
    assert len(empty_data["products"]) == 0


def test_stores_api_seeded_locations():
    """Verify stores API returns seeded stores and matches SQLite count."""
    response = client.get("/api/stores")
    assert response.status_code == 200
    data = response.json()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT city) FROM stores")
        db_stores, db_cities = cursor.fetchone()

    assert data["kpis"]["total_locations"] == db_stores
    assert data["kpis"]["regions_covered"] == db_cities
    assert len(data["stores"]) == db_stores

    store_names = [s["store_name"] for s in data["stores"]]
    assert any("Chennai Central" in name for name in store_names)

    for store in data["stores"]:
        assert "store_code" in store
        assert "store_name" in store
        assert "city" in store
        assert "total_skus" in store
        assert "total_inventory_units" in store
        assert store["status"] == "Active"


def test_stores_api_search():
    """Verify search filtering on stores API."""
    res = client.get("/api/stores?search=Central")
    assert res.status_code == 200
    data = res.json()
    assert len(data["stores"]) >= 1
    assert any("Central" in s["store_name"] for s in data["stores"])

    # Non-existent search
    empty_res = client.get("/api/stores?search=AntarcticaLocation999")
    assert empty_res.status_code == 200
    assert len(empty_res.json()["stores"]) == 0


def test_data_consistency_across_endpoints():
    """Ensure product and store entities match consistently across inventory, sales, dashboard and products."""
    products_res = client.get("/api/products").json()
    stores_res = client.get("/api/stores").json()
    stockouts_res = client.get("/api/inventory/stockout-risks").json()
    dashboard_res = client.get("/api/dashboard/summary").json()

    product_names_catalog = {p["product_name"] for p in products_res["products"]}
    store_names_network = {s["store_name"] for s in stores_res["stores"]}

    # All stockout products must exist in master product catalog
    for item in stockouts_res["results"]:
        assert item["product_name"] in product_names_catalog
        assert item["store_name"] in store_names_network

    # Dashboard total SKUs & stores must match catalog & network
    assert dashboard_res["kpis"]["total_products"] == products_res["total_count"]
    assert dashboard_res["kpis"]["total_stores"] == stores_res["kpis"]["total_locations"]
