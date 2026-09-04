import sqlite3
from datetime import datetime
from backend.services.overstock_service import (
    OverstockService,
    DEMAND_LOOKBACK_DAYS,
    SLOW_MOVING_MAX_DAILY_SALES,
    OVERSTOCK_DAYS,
    SEVERE_OVERSTOCK_DAYS,
)
from backend.database.connection import get_db_connection
from backend.database.seed import seed_database


def test_overstock_detection_logic():
    # Ensure database is seeded
    seed_database(force=False)

    # 1. Run live calculation on seeded database
    resp = OverstockService.calculate_overstock()
    assert resp.lookback_days == DEMAND_LOOKBACK_DAYS
    assert resp.summary.total_attention_items > 0, "Expected overstock items from seeded dataset"
    assert resp.summary.severe_overstock_count > 0, "Expected SEVERE_OVERSTOCK items"
    assert resp.summary.overstock_count >= resp.summary.severe_overstock_count

    print(f"[OK] Live Seeded Overstock Items: Total={resp.summary.total_attention_items}, "
          f"Severe={resp.summary.severe_overstock_count}, Overstock={resp.summary.overstock_count}, "
          f"NoDemand={resp.summary.no_recent_demand_count}, SlowMoving={resp.summary.slow_moving_count}")

    # 2. Ranking Verification
    # SEVERE_OVERSTOCK (0) > NO_RECENT_DEMAND (1) > OVERSTOCK (2) > SLOW_MOVING (3)
    status_priority = {
        "SEVERE_OVERSTOCK": 0,
        "NO_RECENT_DEMAND": 1,
        "OVERSTOCK": 2,
        "SLOW_MOVING": 3,
    }

    results = resp.results
    assert len(results) == resp.summary.total_attention_items

    for i in range(len(results) - 1):
        curr_item = results[i]
        next_item = results[i + 1]

        curr_rank = status_priority[curr_item.status]
        next_rank = status_priority[next_item.status]

        assert curr_rank <= next_rank, f"Rank violation: {curr_item.status} before {next_item.status}"

        # Within same status, verify ordering
        if curr_rank == next_rank:
            if curr_item.status == "NO_RECENT_DEMAND":
                assert curr_item.current_stock >= next_item.current_stock
            elif curr_item.days_of_stock is not None and next_item.days_of_stock is not None:
                assert curr_item.days_of_stock >= next_item.days_of_stock - 0.01

    print("[OK] Ranking verified (Severe > NoDemand > Overstock > SlowMoving, descending by days/stock).")

    # 3. Mathematical Calculations & Classification Integrity
    for item in results:
        assert item.current_stock > 0, "Zero inventory must not appear in overstock results"

        if item.status == "NO_RECENT_DEMAND":
            assert item.recent_quantity_sold == 0
            assert item.average_daily_sales == 0.0
            assert item.days_of_stock is None
            assert item.is_no_demand is True
        else:
            assert item.recent_quantity_sold > 0
            expected_avg = round(item.recent_quantity_sold / float(DEMAND_LOOKBACK_DAYS), 2)
            assert abs(item.average_daily_sales - expected_avg) < 0.02

            expected_days = round(item.current_stock / (item.recent_quantity_sold / float(DEMAND_LOOKBACK_DAYS)), 2)
            assert abs(item.days_of_stock - expected_days) < 0.05

            if item.status == "SEVERE_OVERSTOCK":
                assert item.days_of_stock > SEVERE_OVERSTOCK_DAYS
                assert item.is_severely_overstocked is True
            elif item.status == "OVERSTOCK":
                assert OVERSTOCK_DAYS < item.days_of_stock <= SEVERE_OVERSTOCK_DAYS
                assert item.is_overstocked is True
            elif item.status == "SLOW_MOVING":
                assert item.average_daily_sales <= SLOW_MOVING_MAX_DAILY_SALES

        # Explainability text checks
        assert str(item.current_stock) in item.explanation

    print("[OK] Mathematical formulas, days of stock, and explanations verified.")

    # 4. Filters Verification
    # Filter by dynamic store_id
    with get_db_connection() as conn:
        first_store_id = conn.execute("SELECT id FROM stores LIMIT 1").fetchone()[0]

    resp_store = OverstockService.calculate_overstock(store_id=first_store_id)
    assert len(resp_store.results) > 0
    for item in resp_store.results:
        assert item.store_id == first_store_id
    print(f"[OK] Filter by store_id={first_store_id} verified ({len(resp_store.results)} items).")

    # Filter by category = 'Electronics'
    resp_elec = OverstockService.calculate_overstock(category="Electronics")
    for item in resp_elec.results:
        assert item.category == "Electronics"
    print(f"[OK] Filter by category='Electronics' verified ({len(resp_elec.results)} items).")

    # Filter by status = 'SEVERE_OVERSTOCK'
    resp_severe = OverstockService.calculate_overstock(status_filter="SEVERE_OVERSTOCK")
    for item in resp_severe.results:
        assert item.status == "SEVERE_OVERSTOCK"
    print(f"[OK] Filter by status='SEVERE_OVERSTOCK' verified ({len(resp_severe.results)} items).")

    print("\n[SUCCESS] All Overstock & Slow-Moving Inventory backend tests passed!")


if __name__ == "__main__":
    test_overstock_detection_logic()
