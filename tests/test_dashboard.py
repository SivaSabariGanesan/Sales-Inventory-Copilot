import pytest
from fastapi.testclient import TestClient

from app import app
from backend.services.dashboard_service import DashboardService
from backend.services.inventory_risk_service import InventoryRiskService
from backend.services.overstock_service import OverstockService
from backend.services.sales_anomaly_service import SalesAnomalyService
from backend.services.recommendation_service import RecommendationService
from backend.database.schema import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_dashboard_kpis_and_cross_service_consistency():
    """Verify that dashboard KPIs strictly match underlying specialized services."""
    dash_res = DashboardService.get_dashboard_summary()

    stockout_res = InventoryRiskService.calculate_stockout_risks()
    overstock_res = OverstockService.calculate_overstock()
    sales_res = SalesAnomalyService.calculate_anomalies()
    recs_res = RecommendationService.get_recommendations()

    # Verify Stock-out KPIs
    assert dash_res.kpis.high_stockout_risks == stockout_res.summary.high_risk_count
    assert dash_res.kpis.medium_stockout_risks == stockout_res.summary.medium_risk_count

    # Verify Overstock KPIs
    assert dash_res.kpis.overstocked_items == overstock_res.summary.overstock_count
    assert dash_res.kpis.severe_overstock_count == overstock_res.summary.severe_overstock_count
    assert dash_res.kpis.no_recent_demand_count == overstock_res.summary.no_recent_demand_count

    # Verify Sales Signals KPIs
    assert dash_res.kpis.sales_spikes == sales_res.summary.spike_count
    assert dash_res.kpis.sales_drops == sales_res.summary.drop_count
    assert dash_res.kpis.total_sales_signals == sales_res.summary.spike_count + sales_res.summary.drop_count

    # Verify Attention Items match recommendations
    assert len(dash_res.attention) <= 6
    if len(dash_res.attention) > 0 and len(recs_res.results) > 0:
        assert dash_res.attention[0].id == recs_res.results[0].id


def test_dashboard_inventory_and_sales_health():
    """Verify inventory health segmentation and sales extrema calculations."""
    dash_res = DashboardService.get_dashboard_summary()

    inv_health = dash_res.inventory_summary
    assert inv_health.total_evaluated_skus > 0
    assert inv_health.high_risk_count + inv_health.medium_risk_count + inv_health.overstock_count + inv_health.no_recent_demand_count + inv_health.healthy_count == inv_health.total_evaluated_skus

    sales_health = dash_res.sales_summary
    assert sales_health.total_signals == sales_health.spike_count + sales_health.drop_count
    if sales_health.largest_spike:
        assert sales_health.largest_spike["change_pct"] >= 50.0
    if sales_health.largest_drop:
        assert sales_health.largest_drop["change_pct"] <= -40.0


def test_dashboard_store_breakdown():
    """Verify store breakdown matrix contains all stores with matching counts."""
    dash_res = DashboardService.get_dashboard_summary()
    assert len(dash_res.store_breakdown) == dash_res.kpis.total_stores
    assert len(dash_res.store_breakdown) > 0

    # Check sum of store high stockouts matches total
    sum_high_stockouts = sum(st.high_stockouts for st in dash_res.store_breakdown)
    assert sum_high_stockouts == dash_res.kpis.high_stockout_risks


def test_dashboard_store_filtering():
    """Verify that filtering by store_id scopes all dashboard metrics to that store."""
    all_summary = DashboardService.get_dashboard_summary()
    assert len(all_summary.store_breakdown) > 0
    first_store_id = all_summary.store_breakdown[0].store_id

    dash_res = DashboardService.get_dashboard_summary(store_id=first_store_id)
    assert dash_res.scope.store_id == first_store_id
    assert dash_res.scope.store_name is not None
    assert len(dash_res.store_breakdown) == 1
    assert dash_res.store_breakdown[0].store_id == first_store_id

    # Check that attention items are all from this store
    for item in dash_res.attention:
        assert item.store_id == first_store_id


def test_dashboard_category_filtering():
    """Verify that filtering by category scopes all dashboard metrics to that category."""
    dash_res = DashboardService.get_dashboard_summary(category="Electronics")
    assert dash_res.scope.category == "Electronics"

    for item in dash_res.attention:
        assert item.category == "Electronics"


def test_dashboard_api_endpoint():
    """Test GET /api/dashboard/summary FastAPI endpoint."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    assert "generated_at" in data
    assert "scope" in data
    assert "kpis" in data
    assert "attention" in data
    assert "inventory_summary" in data
    assert "sales_summary" in data
    assert "store_breakdown" in data

    first_store_id = data["store_breakdown"][0]["store_id"]
    # Test with store query param
    resp_store = client.get(f"/api/dashboard/summary?store_id={first_store_id}")
    assert resp_store.status_code == 200
    data_store = resp_store.json()
    assert data_store["scope"]["store_id"] == first_store_id
