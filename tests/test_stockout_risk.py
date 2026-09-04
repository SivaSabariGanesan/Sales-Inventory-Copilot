import sqlite3
from datetime import datetime, date, timedelta
from backend.services.inventory_risk_service import (
    InventoryRiskService,
    STOCKOUT_HIGH_DAYS,
    STOCKOUT_MEDIUM_DAYS,
    DEMAND_LOOKBACK_DAYS,
)
from backend.database.connection import get_db_connection
from backend.database.seed import seed_database


def test_stockout_risk_logic():
    # Ensure database is seeded
    seed_database(force=False)

    # 1. Run live calculation on seeded database
    resp = InventoryRiskService.calculate_stockout_risks()
    assert resp.lookback_days == DEMAND_LOOKBACK_DAYS
    assert resp.summary.total_at_risk > 0, "Expected at-risk products from seeded dataset"
    assert resp.summary.high_risk_count > 0, "Expected HIGH risk products"
    assert resp.summary.medium_risk_count > 0, "Expected MEDIUM risk products"
    assert resp.summary.most_urgent_product is not None

    print(f"[OK] Live Seeded Stockout Risks: Total={resp.summary.total_at_risk}, "
          f"HIGH={resp.summary.high_risk_count}, MEDIUM={resp.summary.medium_risk_count}, "
          f"Most Urgent='{resp.summary.most_urgent_product}' ({resp.summary.min_days_remaining} days)")

    # 2. Verify sorting by urgency (HIGH before MEDIUM, days_remaining ascending)
    results = resp.results
    assert len(results) == resp.summary.total_at_risk

    risk_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    for i in range(len(results) - 1):
        curr_item = results[i]
        next_item = results[i + 1]

        curr_rank = risk_rank[curr_item.risk_level]
        next_rank = risk_rank[next_item.risk_level]

        assert curr_rank <= next_rank, f"Sort violation: {curr_item.risk_level} appeared before {next_item.risk_level}"
        if curr_rank == next_rank:
            c_days = curr_item.estimated_days_remaining or 0
            n_days = next_item.estimated_days_remaining or 0
            assert c_days <= n_days + 0.01, f"Days remaining sort violation: {c_days} > {n_days}"

    print("[OK] Results sorted by risk severity and days remaining ascending.")

    # 3. Verify arithmetic integrity and evidence structure
    for item in results:
        # daily sales check
        expected_daily = round(item.recent_quantity_sold / float(DEMAND_LOOKBACK_DAYS), 2)
        assert abs(item.average_daily_sales - expected_daily) < 0.02

        # days remaining check
        if item.current_stock == 0:
            assert item.estimated_days_remaining == 0.0
            assert item.risk_level == "HIGH"
        else:
            expected_days = round(item.current_stock / (item.recent_quantity_sold / float(DEMAND_LOOKBACK_DAYS)), 2)
            assert abs(item.estimated_days_remaining - expected_days) < 0.05

            if item.estimated_days_remaining <= STOCKOUT_HIGH_DAYS:
                assert item.risk_level == "HIGH"
            elif item.estimated_days_remaining <= STOCKOUT_MEDIUM_DAYS:
                assert item.risk_level == "MEDIUM"

        # explanation check
        assert str(item.current_stock) in item.explanation
        assert str(item.recent_quantity_sold) in item.explanation

    print("[OK] Arithmetic formulas and explainability texts verified across all results.")

    # 4. Filter parameters test
    # Filter by dynamic first store_id
    with get_db_connection() as conn:
        first_store_id = conn.execute("SELECT id FROM stores LIMIT 1").fetchone()[0]

    resp_store = InventoryRiskService.calculate_stockout_risks(store_id=first_store_id)
    assert len(resp_store.results) > 0, f"Expected risk items for store_id={first_store_id}"
    for item in resp_store.results:
        assert item.store_id == first_store_id
    print(f"[OK] Filter by store_id={first_store_id} verified ({len(resp_store.results)} items).")

    # Filter by category = 'Electronics'
    resp_elec = InventoryRiskService.calculate_stockout_risks(category="Electronics")
    for item in resp_elec.results:
        assert item.category == "Electronics"
    print(f"[OK] Filter by category='Electronics' verified ({len(resp_elec.results)} items).")

    # Filter by risk_level = 'HIGH'
    resp_high = InventoryRiskService.calculate_stockout_risks(risk_level_filter="HIGH")
    for item in resp_high.results:
        assert item.risk_level == "HIGH"
    print(f"[OK] Filter by risk_level='HIGH' verified ({len(resp_high.results)} items).")

    print("\n[SUCCESS] All Stock-Out Risk Detection backend tests passed!")


if __name__ == "__main__":
    test_stockout_risk_logic()
