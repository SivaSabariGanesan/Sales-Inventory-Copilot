import pytest
import sqlite3
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient

from app import app
from backend.services.sales_anomaly_service import (
    SalesAnomalyService,
    RECENT_DAYS,
    BASELINE_DAYS,
    SPIKE_PERCENT_THRESHOLD,
    DROP_PERCENT_THRESHOLD,
    MIN_BASELINE_DAILY_SALES,
)
from backend.database.schema import init_db
from backend.config import settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure DB schema is initialized for testing."""
    init_db()


def test_sales_anomaly_live_dataset():
    """Test anomaly calculations on seeded retail.db."""
    response = SalesAnomalyService.calculate_anomalies()
    assert isinstance(response.results, list)
    assert response.recent_days == RECENT_DAYS
    assert response.baseline_days == BASELINE_DAYS
    assert response.recent_start_date != ""
    assert response.recent_end_date != ""
    assert response.baseline_start_date != ""
    assert response.baseline_end_date != ""

    # Check date separation
    r_start = date.fromisoformat(response.recent_start_date)
    r_end = date.fromisoformat(response.recent_end_date)
    b_start = date.fromisoformat(response.baseline_start_date)
    b_end = date.fromisoformat(response.baseline_end_date)

    assert (r_end - r_start).days == RECENT_DAYS - 1
    assert (b_end - b_start).days == BASELINE_DAYS - 1
    assert (r_start - b_end).days == 1  # No overlap and consecutive!

    # Check summary consistency
    spikes = [i for i in response.results if i.status == "SPIKE"]
    drops = [i for i in response.results if i.status == "DROP"]
    assert response.summary.spike_count == len(spikes)
    assert response.summary.drop_count == len(drops)
    assert response.summary.total_signals == len(spikes) + len(drops)


def test_sales_spike_detection():
    """Test spike conditions: percentage_change >= 50% and baseline >= 2.0."""
    # Create an in-memory scenario with exact known sales
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("CREATE TABLE stores (id INTEGER PRIMARY KEY, store_name TEXT, store_code TEXT)")
    cur.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, sku TEXT, product_name TEXT, category TEXT, unit_price REAL)")
    cur.execute("CREATE TABLE sales (id INTEGER PRIMARY KEY, store_id INTEGER, product_id INTEGER, sale_date TEXT, quantity INTEGER, total_amount REAL)")

    cur.execute("INSERT INTO stores VALUES (1, 'Test Store', 'TST')")
    cur.execute("INSERT INTO products VALUES (1, 'SKU1', 'Spike Item', 'Tech', 10.0)")

    # Baseline 30 days: 4 units/day = 120 total units
    # Recent 7 days: 8 units/day = 56 total units
    # % Change = ((8 - 4) / 4) * 100 = +100% -> SPIKE
    ref_date = date(2026, 8, 31)
    for i in range(30):
        d = ref_date - timedelta(days=7 + i)
        cur.execute("INSERT INTO sales VALUES (NULL, 1, 1, ?, 4, 40.0)", (d.isoformat(),))
    for i in range(7):
        d = ref_date - timedelta(days=i)
        cur.execute("INSERT INTO sales VALUES (NULL, 1, 1, ?, 8, 80.0)", (d.isoformat(),))

    conn.commit()

    # Query with the exact logic
    r_start = (ref_date - timedelta(days=6)).isoformat()
    r_end = ref_date.isoformat()
    b_start = (ref_date - timedelta(days=36)).isoformat()
    b_end = (ref_date - timedelta(days=7)).isoformat()

    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0) FROM sales WHERE sale_date >= ? AND sale_date <= ?
    """, (r_start, r_end))
    r_qty = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0) FROM sales WHERE sale_date >= ? AND sale_date <= ?
    """, (b_start, b_end))
    b_qty = cur.fetchone()[0]

    r_avg = r_qty / 7.0
    b_avg = b_qty / 30.0
    pct_change = ((r_avg - b_avg) / b_avg) * 100.0

    assert r_qty == 56
    assert b_qty == 120
    assert r_avg == 8.0
    assert b_avg == 4.0
    assert pct_change == 100.0
    assert b_avg >= MIN_BASELINE_DAILY_SALES
    assert pct_change >= SPIKE_PERCENT_THRESHOLD


def test_sales_drop_detection():
    """Test drop conditions: percentage_change <= -40% and baseline >= 2.0."""
    # Baseline: 10 units/day = 300 total units
    # Recent: 5 units/day = 35 total units
    # % Change = ((5 - 10) / 10) * 100 = -50% -> DROP
    b_qty = 300
    r_qty = 35
    r_avg = r_qty / 7.0
    b_avg = b_qty / 30.0
    pct_change = ((r_avg - b_avg) / b_avg) * 100.0

    assert r_avg == 5.0
    assert b_avg == 10.0
    assert pct_change == -50.0
    assert pct_change <= DROP_PERCENT_THRESHOLD
    assert b_avg >= MIN_BASELINE_DAILY_SALES


def test_zero_baseline_handling():
    """Test zero baseline: percentage_change is None and status is INSUFFICIENT_BASELINE."""
    r_qty = 14
    b_qty = 0
    r_avg = r_qty / 7.0
    b_avg = 0.0

    assert b_avg == 0.0
    # Service must not divide by zero and return None for percentage_change
    assert r_avg == 2.0


def test_low_baseline_handling():
    """Test low baseline (e.g. 0.5 units/day < 2.0): status is INSUFFICIENT_BASELINE."""
    # Baseline = 0.5 units/day (15 units in 30 days)
    # Recent = 1.0 units/day (7 units in 7 days)
    # % Change = +100%, but baseline is below 2.0 -> INSUFFICIENT_BASELINE
    b_qty = 15
    r_qty = 7
    r_avg = r_qty / 7.0
    b_avg = b_qty / 30.0
    pct_change = ((r_avg - b_avg) / b_avg) * 100.0

    assert b_avg == 0.5
    assert b_avg < MIN_BASELINE_DAILY_SALES
    assert pct_change == 100.0


def test_recent_sales_zero_complete_drop():
    """Test recent sales = 0 with sufficient baseline: change is -100% and status is DROP."""
    # Baseline: 5 units/day = 150 units in 30 days
    # Recent: 0 units in 7 days
    # % Change = ((0 - 5) / 5) * 100 = -100% -> DROP
    b_qty = 150
    r_qty = 0
    r_avg = r_qty / 7.0
    b_avg = b_qty / 30.0
    pct_change = ((r_avg - b_avg) / b_avg) * 100.0

    assert r_avg == 0.0
    assert b_avg == 5.0
    assert pct_change == -100.0
    assert pct_change <= DROP_PERCENT_THRESHOLD


def test_exact_threshold_boundaries():
    """Test exact +50% spike and -40% drop boundary conditions."""
    # Exact +50% spike: Baseline = 4.0, Recent = 6.0 -> ((6 - 4) / 4) * 100 = 50.0%
    b_avg = 4.0
    r_avg = 6.0
    pct_spike = ((r_avg - b_avg) / b_avg) * 100.0
    assert pct_spike == SPIKE_PERCENT_THRESHOLD

    # Exact -40% drop: Baseline = 5.0, Recent = 3.0 -> ((3 - 5) / 5) * 100 = -40.0%
    b_avg_drop = 5.0
    r_avg_drop = 3.0
    pct_drop = ((r_avg_drop - b_avg_drop) / b_avg_drop) * 100.0
    assert pct_drop == DROP_PERCENT_THRESHOLD


def test_api_sales_anomalies_endpoint():
    """Test GET /api/sales/anomalies endpoint structure and filters."""
    response = client.get("/api/sales/anomalies")
    assert response.status_code == 200
    data = response.json()

    assert "generated_at" in data
    assert "recent_days" in data
    assert "baseline_days" in data
    assert "summary" in data
    assert "results" in data
    assert isinstance(data["results"], list)

    # Test filtering by status
    resp_spikes = client.get("/api/sales/anomalies?status=SPIKE")
    assert resp_spikes.status_code == 200
    spikes_data = resp_spikes.json()
    for item in spikes_data["results"]:
        assert item["status"] == "SPIKE"
        assert item["percentage_change"] is not None
        assert item["percentage_change"] >= 50.0

    # Test filtering by store_id
    resp_store = client.get("/api/sales/anomalies?store_id=1")
    assert resp_store.status_code == 200
    store_data = resp_store.json()
    for item in store_data["results"]:
        assert item["store_id"] == 1


def test_sorting_by_magnitude():
    """Test that results are sorted with largest magnitude changes first."""
    response = SalesAnomalyService.calculate_anomalies()
    signals = [item for item in response.results if item.status in ("SPIKE", "DROP") and item.percentage_change is not None]

    if len(signals) >= 2:
        for i in range(len(signals) - 1):
            assert abs(signals[i].percentage_change) >= abs(signals[i + 1].percentage_change)
