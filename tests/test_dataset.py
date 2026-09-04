import sqlite3
from datetime import datetime, timedelta
from backend.database.schema import init_db
from backend.database.connection import get_connection
from backend.database.seed import seed_database


def test_retail_dataset_validation():
    # Force fresh seed
    counts = seed_database(force=True)
    print("[OK] Seed executed:", counts)

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Store counts and unique codes
    cursor.execute("SELECT id, store_code, store_name, city FROM stores")
    stores = cursor.fetchall()
    assert len(stores) == 4, f"Expected 4 stores, found {len(stores)}"
    store_codes = [s["store_code"] for s in stores]
    assert len(store_codes) == len(set(store_codes)), "Store codes must be unique"
    print(f"[OK] 4 Stores verified with unique codes: {store_codes}")

    # 2. Product counts and unique SKUs
    cursor.execute("SELECT id, sku, product_name, category, unit_price, reorder_level FROM products")
    products = cursor.fetchall()
    assert 80 <= len(products) <= 100, f"Expected 80-100 products, found {len(products)}"
    skus = [p["sku"] for p in products]
    assert len(skus) == len(set(skus)), "Product SKUs must be unique"
    categories = {p["category"] for p in products}
    assert len(categories) >= 5, f"Expected at least 5 categories, found {len(categories)}"
    print(f"[OK] {len(products)} Products verified across {len(categories)} categories: {categories}")

    # 3. Inventory completeness (Every store/product combination)
    expected_inventory_count = len(stores) * len(products)
    cursor.execute("SELECT COUNT(*) FROM inventory")
    inv_count = cursor.fetchone()[0]
    assert inv_count == expected_inventory_count, f"Expected {expected_inventory_count} inventory records, found {inv_count}"

    cursor.execute("SELECT MIN(stock_quantity), MAX(stock_quantity) FROM inventory")
    min_stock, max_stock = cursor.fetchone()
    assert min_stock >= 0, f"Inventory stock cannot be negative, found {min_stock}"
    assert max_stock > 50, f"Expected max inventory > 50, found {max_stock}"
    print(f"[OK] {inv_count} Inventory records verified (Min stock: {min_stock}, Max stock: {max_stock})")

    # 4. Sales span and volume
    cursor.execute("SELECT COUNT(*), MIN(sale_date), MAX(sale_date), SUM(revenue) FROM sales")
    sales_count, min_date, max_date, total_revenue = cursor.fetchone()
    assert sales_count > 10000, f"Expected > 10,000 sales records, found {sales_count}"
    d_min = datetime.fromisoformat(min_date)
    d_max = datetime.fromisoformat(max_date)
    days_span = (d_max - d_min).days + 1
    assert days_span >= 170, f"Expected ~180 days span, found {days_span}"
    print(f"[OK] {sales_count} Sales records verified spanning {days_span} days (Total Revenue: ${total_revenue:,.2f})")

    # 5. Referential Integrity & Numerical Constraints
    cursor.execute("""
        SELECT COUNT(*) FROM sales s
        LEFT JOIN stores st ON s.store_id = st.id
        LEFT JOIN products p ON s.product_id = p.id
        WHERE st.id IS NULL OR p.id IS NULL
    """)
    orphan_sales = cursor.fetchone()[0]
    assert orphan_sales == 0, f"Found {orphan_sales} orphan sales records"

    cursor.execute("SELECT COUNT(*) FROM sales WHERE quantity <= 0")
    invalid_qty = cursor.fetchone()[0]
    assert invalid_qty == 0, f"Found {invalid_qty} sales with non-positive quantity"

    cursor.execute("SELECT COUNT(*) FROM sales WHERE ABS(revenue - (quantity * unit_price)) > 0.01")
    invalid_rev = cursor.fetchone()[0]
    assert invalid_rev == 0, f"Found {invalid_rev} sales with revenue mismatch"
    print("[OK] Referential integrity and mathematical consistency (revenue = qty * unit_price) verified.")

    # 6. Scenario Pattern Presence (Underlying Data Validation)
    # Check Stock-out risk (SKUs with stock < reorder level)
    cursor.execute("""
        SELECT p.sku, p.product_name, p.reorder_level, AVG(i.stock_quantity) as avg_stock
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        GROUP BY p.id
        HAVING avg_stock < p.reorder_level * 0.5
    """)
    stockout_candidates = cursor.fetchall()
    assert len(stockout_candidates) >= 5, f"Expected stockout risk candidates, found {len(stockout_candidates)}"
    print(f"[OK] Stock-out risk patterns detected ({len(stockout_candidates)} SKUs with stock < 50% reorder level)")

    # Check Overstock (SKUs with stock > 80 and very low total sales)
    cursor.execute("""
        SELECT p.sku, p.product_name,
               (SELECT AVG(stock_quantity) FROM inventory WHERE product_id = p.id) as avg_stock,
               (SELECT COUNT(*) FROM sales WHERE product_id = p.id) as total_sales
        FROM products p
        WHERE (SELECT AVG(stock_quantity) FROM inventory WHERE product_id = p.id) > 80
          AND (SELECT COUNT(*) FROM sales WHERE product_id = p.id) < 150
    """)
    overstock_candidates = cursor.fetchall()
    assert len(overstock_candidates) >= 5, f"Expected overstock candidates, found {len(overstock_candidates)}"
    print(f"[OK] Overstock / slow-moving patterns detected ({len(overstock_candidates)} SKUs with high stock & low sales)")

    # Check Sales Spike (SKUs with recent sales velocity >> historical velocity)
    cutoff_date = (d_max - timedelta(days=21)).isoformat()
    cursor.execute("""
        SELECT p.sku,
            SUM(CASE WHEN s.sale_date >= ? THEN s.quantity ELSE 0 END) * 1.0 / 21 as recent_daily,
            SUM(CASE WHEN s.sale_date < ? THEN s.quantity ELSE 0 END) * 1.0 / 159 as hist_daily
        FROM products p
        JOIN sales s ON p.id = s.product_id
        GROUP BY p.id
        HAVING recent_daily > hist_daily * 2.5
    """, (cutoff_date, cutoff_date))
    spike_candidates = cursor.fetchall()
    assert len(spike_candidates) >= 4, f"Expected sales spike candidates, found {len(spike_candidates)}"
    print(f"[OK] Sales spike patterns detected ({len(spike_candidates)} SKUs with recent velocity > 2.5x historical)")

    # Check Sales Drop (SKUs with historical velocity >> recent velocity)
    cursor.execute("""
        SELECT p.sku,
            SUM(CASE WHEN s.sale_date >= ? THEN s.quantity ELSE 0 END) * 1.0 / 21 as recent_daily,
            SUM(CASE WHEN s.sale_date < ? THEN s.quantity ELSE 0 END) * 1.0 / 159 as hist_daily
        FROM products p
        JOIN sales s ON p.id = s.product_id
        GROUP BY p.id
        HAVING hist_daily > recent_daily * 3.0 AND hist_daily > 2.0
    """, (cutoff_date, cutoff_date))
    drop_candidates = cursor.fetchall()
    assert len(drop_candidates) >= 4, f"Expected sales drop candidates, found {len(drop_candidates)}"
    print(f"[OK] Sales drop patterns detected ({len(drop_candidates)} SKUs with historical velocity > 3.0x recent)")

    # 7. Idempotence Check
    init_db(seed=True)
    cursor.execute("SELECT COUNT(*) FROM stores")
    assert cursor.fetchone()[0] == 4, "Idempotent seed should not duplicate stores"
    cursor.execute("SELECT COUNT(*) FROM products")
    assert cursor.fetchone()[0] == len(products), "Idempotent seed should not duplicate products"
    cursor.execute("SELECT COUNT(*) FROM sales")
    assert cursor.fetchone()[0] == sales_count, "Idempotent seed should not duplicate sales"
    cursor.execute("SELECT COUNT(*) FROM inventory")
    assert cursor.fetchone()[0] == inv_count, "Idempotent seed should not duplicate inventory"
    print("[OK] Database seeding idempotence verified (no duplication on re-init).")

    conn.close()
    print("\n[SUCCESS] All Retail Dataset validation checks passed successfully!")


if __name__ == "__main__":
    test_retail_dataset_validation()
