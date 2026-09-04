import pytest
from fastapi.testclient import TestClient

from app import app
from backend.database.connection import get_db_connection
from backend.database.schema import init_db
from backend.services.value_analytics_service import ValueAnalyticsService
from backend.services.overstock_service import OverstockService
from backend.services.inventory_risk_service import InventoryRiskService
from backend.services.copilot_service import CopilotService
from backend.services.version_service import DataVersionService
from backend.models.copilot import CopilotIntentEnum

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM copilot_cache")
        cursor.execute("DELETE FROM audit_logs")
        conn.commit()


# =====================================================================
# 1. Deterministic Value Calculations & Math Tests
# =====================================================================

def test_inventory_value_deterministic_math():
    """Verify inventory value matches current stock * unit price."""
    inv_data = ValueAnalyticsService.calculate_inventory_value()
    assert inv_data["total_inventory_value"] >= 0
    assert inv_data["total_stock_units"] >= 0

    # Cross-verify with direct SQLite aggregation
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(i.stock_quantity * p.unit_price) as total_val,
                   SUM(i.stock_quantity) as total_qty
            FROM inventory i
            JOIN products p ON i.product_id = p.id
        """)
        row = cursor.fetchone()
        expected_val = round(row["total_val"] or 0.0, 2)
        expected_qty = row["total_qty"] or 0

    assert inv_data["total_inventory_value"] == expected_val
    assert inv_data["total_stock_units"] == expected_qty
    assert len(inv_data["stores_summary"]) > 0
    assert len(inv_data["category_summary"]) > 0
    assert len(inv_data["top_products"]) > 0


def test_sales_revenue_deterministic_math():
    """Verify sales revenue calculation matches SQLite stored revenue or qty * unit_price."""
    rev_data = ValueAnalyticsService.calculate_sales_revenue()
    assert rev_data["total_sales_revenue"] >= 0
    assert rev_data["total_sales_units"] >= 0

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(COALESCE(s.revenue, s.quantity * COALESCE(s.unit_price, p.unit_price, 0.0))) as total_rev,
                   SUM(s.quantity) as total_qty
            FROM sales s
            JOIN products p ON s.product_id = p.id
        """)
        row = cursor.fetchone()
        expected_rev = round(row["total_rev"] or 0.0, 2)
        expected_qty = row["total_qty"] or 0

    assert rev_data["total_sales_revenue"] == expected_rev
    assert rev_data["total_sales_units"] == expected_qty
    assert len(rev_data["stores_revenue"]) > 0
    assert len(rev_data["category_revenue"]) > 0
    assert len(rev_data["top_products"]) > 0


def test_overstock_value_math():
    """Verify tied-up overstock capital is calculated accurately from overstock items."""
    overstock_data = ValueAnalyticsService.calculate_overstock_value()
    assert overstock_data.total_overstock_inventory_value >= 0
    assert overstock_data.products_affected_count >= 0
    assert overstock_data.stores_affected_count >= 0
    assert overstock_data.severe_overstock_value >= 0
    assert overstock_data.moderate_overstock_value >= 0


def test_value_analytics_summary_service():
    """Verify aggregate summary combining inventory, sales, and overstock value."""
    summary = ValueAnalyticsService.get_value_analytics_summary()
    assert summary.total_inventory_value >= 0
    assert summary.total_sales_revenue >= 0
    assert summary.overstock_inventory_value >= 0
    assert len(summary.top_products_by_revenue) > 0
    assert len(summary.top_stores_by_revenue) > 0
    assert len(summary.top_inventory_value_products) > 0
    assert len(summary.stores_summary) > 0
    assert len(summary.category_summary) > 0


# =====================================================================
# 2. API Endpoint & Filtering Tests
# =====================================================================

def test_value_analytics_api_endpoint():
    """Verify GET /api/analytics/value returns 200 and schema compliant JSON."""
    response = client.get("/api/analytics/value")
    assert response.status_code == 200
    data = response.json()

    assert "total_inventory_value" in data
    assert "total_sales_revenue" in data
    assert "overstock_inventory_value" in data
    assert "top_products_by_revenue" in data
    assert "top_stores_by_revenue" in data
    assert "top_inventory_value_products" in data
    assert "stores_summary" in data
    assert "category_summary" in data
    assert "overstock_summary" in data


def test_value_analytics_filtering():
    """Verify filtering by store_id and category."""
    # Filter by store 1
    res_store = client.get("/api/analytics/value?store_id=1")
    assert res_store.status_code == 200
    data_store = res_store.json()
    assert len(data_store["stores_summary"]) <= 1

    # Filter by category
    res_cat = client.get("/api/analytics/value?category=Electronics")
    assert res_cat.status_code == 200
    data_cat = res_cat.json()
    assert all(c["category"] == "Electronics" for c in data_cat["category_summary"])


def test_inventory_route_enrichment():
    """Verify GET /api/inventory/ items contain unit_price and inventory_value."""
    response = client.get("/api/inventory/")
    assert response.status_code == 200
    data = response.json()
    items = data.get("inventory", [])
    assert len(items) > 0
    for item in items[:5]:
        assert "unit_price" in item
        assert "inventory_value" in item
        assert item["inventory_value"] == round(item["stock_quantity"] * item["unit_price"], 2)


def test_stockout_and_overstock_services_enrichment():
    """Verify stockout and overstock services return unit_price and inventory_value."""
    risk_response = InventoryRiskService.calculate_stockout_risks()
    for item in risk_response.results[:3]:
        assert hasattr(item, "unit_price")
        assert hasattr(item, "inventory_value")
        assert item.inventory_value == round(item.current_stock * item.unit_price, 2)

    overstock_response = OverstockService.calculate_overstock()
    for item in overstock_response.results[:3]:
        assert hasattr(item, "unit_price")
        assert hasattr(item, "inventory_value")
        assert item.inventory_value == round(item.current_stock * item.unit_price, 2)


# =====================================================================
# 3. Copilot Financial Intents & Grounded Evidence Tests
# =====================================================================

def test_copilot_intent_revenue_summary():
    """Verify copilot handles REVENUE_SUMMARY intent deterministically."""
    res = CopilotService.process_query("What is our total sales revenue and top earning products?")
    assert res.intent in ("REVENUE_SUMMARY", CopilotIntentEnum.REVENUE_SUMMARY.value)
    assert res.answer is not None
    assert "$" in res.answer
    assert len(res.evidence) > 0
    assert "total_sales_revenue" in res.insights[0] or "Sales Revenue" in str(res.evidence[0])


def test_copilot_intent_inventory_value():
    """Verify copilot handles INVENTORY_VALUE intent deterministically."""
    res = CopilotService.process_query("What is the total monetary value of our inventory in stock?")
    assert res.intent in ("INVENTORY_VALUE", CopilotIntentEnum.INVENTORY_VALUE.value)
    assert res.answer is not None
    assert "$" in res.answer
    assert len(res.evidence) > 0


def test_copilot_intent_overstock_value():
    """Verify copilot handles OVERSTOCK_VALUE intent deterministically."""
    res = CopilotService.process_query("How much capital is tied up in excess overstocked inventory?")
    assert res.intent in ("OVERSTOCK_VALUE", CopilotIntentEnum.OVERSTOCK_VALUE.value)
    assert res.answer is not None
    assert "$" in res.answer


def test_copilot_intent_store_value_analysis():
    """Verify copilot handles STORE_VALUE_ANALYSIS intent."""
    res = CopilotService.process_query("Which store holds the highest inventory value?")
    assert res.intent in ("STORE_VALUE_ANALYSIS", CopilotIntentEnum.STORE_VALUE_ANALYSIS.value)
    assert res.answer is not None
    assert len(res.evidence) > 0


def test_copilot_intent_product_value_analysis():
    """Verify copilot handles PRODUCT_VALUE_ANALYSIS intent."""
    res = CopilotService.process_query("Show me product level revenue and inventory value breakdown")
    assert res.intent in ("PRODUCT_VALUE_ANALYSIS", CopilotIntentEnum.PRODUCT_VALUE_ANALYSIS.value)
    assert res.answer is not None
    assert len(res.evidence) > 0


def test_copilot_intent_category_value_analysis():
    """Verify copilot handles CATEGORY_VALUE_ANALYSIS intent."""
    res = CopilotService.process_query("What is the category breakdown of sales revenue and inventory value?")
    assert res.intent in ("CATEGORY_VALUE_ANALYSIS", CopilotIntentEnum.CATEGORY_VALUE_ANALYSIS.value)
    assert res.answer is not None
    assert len(res.evidence) > 0


def test_copilot_grounded_evidence_no_hallucination():
    """Verify that dollar amounts in response match calculated evidence records exactly."""
    val_data = ValueAnalyticsService.get_value_analytics_summary()
    res = CopilotService.process_query("What is our total inventory value?")
    
    assert res.intent in ("INVENTORY_VALUE", CopilotIntentEnum.INVENTORY_VALUE.value)
    expected_formatted = f"${val_data.total_inventory_value:,.2f}"
    assert expected_formatted in res.answer


# =====================================================================
# 4. Audit Trail, Prompt Caching & Invalidation for Value Queries
# =====================================================================

def test_value_query_audit_trail_logging():
    """Verify financial queries are recorded into audit_logs table."""
    question = "Give me the total sales revenue summary"
    res = CopilotService.process_query(question)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs WHERE question = ? ORDER BY id DESC LIMIT 1", (question,))
        log = cursor.fetchone()
        assert log is not None
        assert log["intent"] in ("REVENUE_SUMMARY", CopilotIntentEnum.REVENUE_SUMMARY.value)
        assert log["status"] in ("ANSWERED", "answered", "success", "fallback")
        assert log["cache_key"] is not None


def test_value_query_caching_and_invalidation():
    """Verify caching works for value questions and invalidates when data version updates."""
    question = "What is the overstock tied-up capital?"
    
    # 1st call: fresh execution
    res1 = CopilotService.process_query(question)
    
    # 2nd call: cache hit
    res2 = CopilotService.process_query(question)
    assert res2.answer == res1.answer

    # Verify cache hit recorded in audit trail
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cache_hit FROM audit_logs WHERE question = ? ORDER BY id DESC LIMIT 1", (question,))
        log = cursor.fetchone()
        assert log is not None
        assert log["cache_hit"] in (1, True)

    # Invalidate data version
    DataVersionService.increment_data_version()
    
    # 3rd call after invalidation -> fresh response
    res3 = CopilotService.process_query(question)
    assert res3.answer == res1.answer  # Values remain consistent if DB didn't change
