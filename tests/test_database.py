import sqlite3
from backend.database.schema import init_db
from backend.database.connection import get_connection

def test_database_schema_and_constraints():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Check all tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cursor.fetchall()}
    required = {'stores', 'products', 'sales', 'inventory', 'users'}
    assert required.issubset(tables), f"Missing tables: {required - tables}"
    print("[OK] All 5 required tables exist:", required)

    # 2. Foreign Key Enforcement
    try:
        cursor.execute(
            "INSERT INTO sales (sale_date, store_id, product_id, quantity, unit_price, revenue) "
            "VALUES (CURRENT_TIMESTAMP, 9999, 9999, 1, 10, 10)"
        )
        assert False, "Expected ForeignKey error"
    except sqlite3.IntegrityError:
        print("[OK] Foreign Key constraint enforced.")

    # 3. Check sales quantity > 0
    cursor.execute(
        "INSERT INTO stores (store_code, store_name, city) VALUES ('TEST01', 'Store 1', 'City 1')"
    )
    store_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO products (sku, product_name, category, unit_price, reorder_level) "
        "VALUES ('SKU01', 'Prod 1', 'Cat', 10, 5)"
    )
    prod_id = cursor.lastrowid

    try:
        cursor.execute(
            "INSERT INTO sales (sale_date, store_id, product_id, quantity, unit_price, revenue) "
            "VALUES (CURRENT_TIMESTAMP, ?, ?, 0, 10, 0)",
            (store_id, prod_id),
        )
        assert False, "Expected quantity > 0 error"
    except sqlite3.IntegrityError:
        print("[OK] Sales quantity > 0 constraint enforced.")

    # 4. Check inventory stock >= 0
    try:
        cursor.execute(
            "INSERT INTO inventory (store_id, product_id, stock_quantity) VALUES (?, ?, -5)",
            (store_id, prod_id),
        )
        assert False, "Expected stock >= 0 error"
    except sqlite3.IntegrityError:
        print("[OK] Inventory stock >= 0 constraint enforced.")

    # 5. Check unique (store_id, product_id)
    cursor.execute(
        "INSERT INTO inventory (store_id, product_id, stock_quantity) VALUES (?, ?, 10)",
        (store_id, prod_id),
    )
    try:
        cursor.execute(
            "INSERT INTO inventory (store_id, product_id, stock_quantity) VALUES (?, ?, 20)",
            (store_id, prod_id),
        )
        assert False, "Expected UNIQUE(store_id, product_id) error"
    except sqlite3.IntegrityError:
        print("[OK] Inventory unique (store_id, product_id) enforced.")

    # 6. Roll back test transactions to ensure no fake data remains
    conn.rollback()
    conn.close()

    # Verify zero records
    conn2 = get_connection()
    for t in required:
        count = conn2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        assert count == 0, f"Table {t} should have 0 records, found {count}"
    conn2.close()
    print("[OK] Verified clean database with 0 records.")


if __name__ == "__main__":
    test_database_schema_and_constraints()
