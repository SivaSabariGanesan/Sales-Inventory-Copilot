import pytest
from fastapi.testclient import TestClient

from app import app
from backend.database.schema import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_e2e_health_check():
    """Verify health check endpoint returns ok and database path."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "sqlite"


def test_e2e_dashboard_flow():
    """Verify executive dashboard summary endpoint returns valid structure."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "attention" in data
    assert "inventory_summary" in data
    assert "sales_summary" in data
    assert "store_breakdown" in data
    assert data["kpis"]["total_products"] > 0
    assert data["kpis"]["total_stores"] > 0


def test_e2e_inventory_stockout_flow():
    """Verify stockout risk detection endpoint."""
    response = client.get("/api/inventory/stockout-risks")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_e2e_inventory_overstock_flow():
    """Verify overstock and slow-moving detection endpoint."""
    response = client.get("/api/inventory/overstock")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_e2e_sales_anomalies_flow():
    """Verify sales velocity anomaly detection endpoint."""
    response = client.get("/api/sales/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_e2e_recommendations_flow():
    """Verify action recommendations and today's attention endpoints."""
    resp_recs = client.get("/api/recommendations")
    assert resp_recs.status_code == 200
    assert "summary" in resp_recs.json()

    resp_today = client.get("/api/recommendations/today")
    assert resp_today.status_code == 200
    assert "results" in resp_today.json()


def test_e2e_copilot_grounded_query():
    """Verify natural-language Copilot queries with deterministic evidence."""
    response = client.post(
        "/api/copilot/query",
        json={"question": "Which products are at risk of running out?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ANSWERED"
    assert len(data["evidence"]) > 0
    assert len(data["insights"]) > 0


def test_e2e_copilot_safe_refusal():
    """Verify safe refusal of unsupported predictive queries."""
    response = client.post(
        "/api/copilot/query",
        json={"question": "What will sales be next year?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNSUPPORTED"
    assert data["needs_human_review"] is True


def test_e2e_spa_html_delivery():
    """Verify that root URL delivers the production HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Retail" in response.text or "html" in response.text.lower()
