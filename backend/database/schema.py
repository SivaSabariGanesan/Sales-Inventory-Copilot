import logging
from backend.database.connection import get_db_connection

logger = logging.getLogger("retail_copilot.database")

SCHEMA_SQL = """
-- Stores Table
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_code TEXT UNIQUE NOT NULL,
    store_name TEXT NOT NULL,
    city TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price NUMERIC NOT NULL,
    reorder_level NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales Table
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date TIMESTAMP NOT NULL,
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC NOT NULL,
    revenue NUMERIC NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_store ON sales(store_id);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);

-- Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    UNIQUE(store_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_store ON inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);

-- Users Table (Authentication Foundation)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'google',
    provider_user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- System State & Data Versioning
CREATE TABLE IF NOT EXISTS system_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copilot Audit Trail
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    question TEXT NOT NULL,
    normalized_question TEXT NOT NULL,
    intent TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    status TEXT NOT NULL,
    cache_hit INTEGER NOT NULL DEFAULT 0,
    cache_key TEXT,
    gemini_calls INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost REAL,
    action_recommendation TEXT,
    needs_human_review INTEGER NOT NULL DEFAULT 0,
    prompt_version TEXT NOT NULL DEFAULT 'v1.2.0',
    model TEXT NOT NULL DEFAULT 'gemini-2.5-flash',
    data_version INTEGER NOT NULL DEFAULT 1,
    execution_steps TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_intent ON audit_logs(intent);
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_audit_cache_hit ON audit_logs(cache_hit);
CREATE INDEX IF NOT EXISTS idx_audit_data_version ON audit_logs(data_version);

-- Safe Copilot Application & Prompt Cache
CREATE TABLE IF NOT EXISTS copilot_cache (
    cache_key TEXT PRIMARY KEY,
    data_version INTEGER NOT NULL,
    prompt_version TEXT NOT NULL,
    model TEXT NOT NULL,
    normalized_question TEXT NOT NULL,
    response_json TEXT NOT NULL,
    gemini_calls INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_data_version ON copilot_cache(data_version);
"""


def init_db(seed: bool = True) -> None:
    """Initialize SQLite database with required tables, indexes, and initial retail dataset."""
    with get_db_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO system_state (key, value) VALUES ('data_version', '1')")
    logger.info("SQLite database schema initialized successfully.")

    if seed:
        from backend.database.seed import seed_database
        seed_database(force=False)
