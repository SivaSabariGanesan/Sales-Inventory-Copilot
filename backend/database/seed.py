import random
from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
import logging

from backend.database.connection import get_db_connection

logger = logging.getLogger("retail_copilot.seed")

# Deterministic random seed
SEED_VALUE = 42

STORES_DATA = [
    {"store_code": "STR-001", "store_name": "RetailCo Chennai Central", "city": "Chennai"},
    {"store_code": "STR-002", "store_name": "RetailCo Anna Nagar", "city": "Chennai"},
    {"store_code": "STR-003", "store_name": "RetailCo Velachery", "city": "Chennai"},
    {"store_code": "STR-004", "store_name": "RetailCo T. Nagar", "city": "Chennai"},
]

# 90 Products across 6 categories with specific scenario archetypes
# Archetypes: 'normal', 'stockout_risk', 'overstock', 'spike', 'drop'
PRODUCTS_DEFINITIONS: List[Dict[str, Any]] = [
    # --- ELECTRONICS (15) ---
    {"sku": "ELEC-001", "name": "Wireless Noise-Cancelling Headphones", "cat": "Electronics", "price": 129.99, "reorder": 20, "archetype": "stockout_risk"},
    {"sku": "ELEC-002", "name": "65W GaN Fast Wall Charger", "cat": "Electronics", "price": 29.99, "reorder": 25, "archetype": "spike"},
    {"sku": "ELEC-003", "name": "Ergonomic Bluetooth Optical Mouse", "cat": "Electronics", "price": 24.99, "reorder": 15, "archetype": "normal"},
    {"sku": "ELEC-004", "name": "Mechanical Gaming Keyboard RGB", "cat": "Electronics", "price": 79.99, "reorder": 12, "archetype": "normal"},
    {"sku": "ELEC-005", "name": "7-in-1 USB-C Multiport Hub", "cat": "Electronics", "price": 39.99, "reorder": 18, "archetype": "normal"},
    {"sku": "ELEC-006", "name": "1080p HD Streaming Webcam", "cat": "Electronics", "price": 49.99, "reorder": 15, "archetype": "drop"},
    {"sku": "ELEC-007", "name": "Smart LED Desk Lamp with Dimmer", "cat": "Electronics", "price": 34.99, "reorder": 10, "archetype": "normal"},
    {"sku": "ELEC-008", "name": "Portable Waterproof Bluetooth Speaker", "cat": "Electronics", "price": 54.99, "reorder": 16, "archetype": "normal"},
    {"sku": "ELEC-009", "name": "20000mAh Dual USB-C Power Bank", "cat": "Electronics", "price": 44.99, "reorder": 20, "archetype": "stockout_risk"},
    {"sku": "ELEC-010", "name": "Magnetic 15W Wireless Charging Pad", "cat": "Electronics", "price": 19.99, "reorder": 15, "archetype": "normal"},
    {"sku": "ELEC-011", "name": "Dual-Band AC1200 WiFi Range Extender", "cat": "Electronics", "price": 32.99, "reorder": 10, "archetype": "overstock"},
    {"sku": "ELEC-012", "name": "4K Ultra HD Action Sports Camera", "cat": "Electronics", "price": 99.99, "reorder": 8, "archetype": "overstock"},
    {"sku": "ELEC-013", "name": "Smart Fitness Tracker Band with Heart Rate", "cat": "Electronics", "price": 49.99, "reorder": 15, "archetype": "normal"},
    {"sku": "ELEC-014", "name": "Braided High-Speed HDMI 2.1 Cable 2m", "cat": "Electronics", "price": 14.99, "reorder": 25, "archetype": "normal"},
    {"sku": "ELEC-015", "name": "Wireless Lavalier Lapel Microphone Kit", "cat": "Electronics", "price": 38.99, "reorder": 12, "archetype": "normal"},

    # --- ACCESSORIES (15) ---
    {"sku": "ACCS-001", "name": "Shockproof Matte Smartphone Case", "cat": "Accessories", "price": 14.99, "reorder": 30, "archetype": "spike"},
    {"sku": "ACCS-002", "name": "Tempered Glass Screen Protector 2-Pack", "cat": "Accessories", "price": 9.99, "reorder": 35, "archetype": "normal"},
    {"sku": "ACCS-003", "name": "Water-Resistant Vegan Leather Laptop Sleeve", "cat": "Accessories", "price": 27.99, "reorder": 15, "archetype": "normal"},
    {"sku": "ACCS-004", "name": "Anti-Theft Commuter Backpack with USB", "cat": "Accessories", "price": 59.99, "reorder": 12, "archetype": "stockout_risk"},
    {"sku": "ACCS-005", "name": "Travel Electronics Cable Organizer Pouch", "cat": "Accessories", "price": 16.99, "reorder": 20, "archetype": "normal"},
    {"sku": "ACCS-006", "name": "Anti-Glare Blue Light Blocking Glasses", "cat": "Accessories", "price": 19.99, "reorder": 18, "archetype": "normal"},
    {"sku": "ACCS-007", "name": "Windproof Compact Automatic Travel Umbrella", "cat": "Accessories", "price": 22.99, "reorder": 15, "archetype": "normal"},
    {"sku": "ACCS-008", "name": "Adjustable Aluminum Phone & Tablet Stand", "cat": "Accessories", "price": 18.99, "reorder": 20, "archetype": "normal"},
    {"sku": "ACCS-009", "name": "Optical Lens & Screen Microfiber Cleaning Kit", "cat": "Accessories", "price": 8.99, "reorder": 25, "archetype": "normal"},
    {"sku": "ACCS-010", "name": "Smart Bluetooth Item & Key Finder Beacon", "cat": "Accessories", "price": 24.99, "reorder": 15, "archetype": "overstock"},
    {"sku": "ACCS-011", "name": "UV400 Polarized Classic Sunglasses", "cat": "Accessories", "price": 34.99, "reorder": 12, "archetype": "drop"},
    {"sku": "ACCS-012", "name": "Heavy Duty Canvas Grocery Tote Bag", "cat": "Accessories", "price": 11.99, "reorder": 30, "archetype": "normal"},
    {"sku": "ACCS-013", "name": "Memory Foam Ergonomic Travel Neck Pillow", "cat": "Accessories", "price": 21.99, "reorder": 15, "archetype": "normal"},
    {"sku": "ACCS-014", "name": "Replacement Silicone Earbud Tips Multi-Size", "cat": "Accessories", "price": 6.99, "reorder": 40, "archetype": "normal"},
    {"sku": "ACCS-015", "name": "RFID Blocking Slim Leather Cardholder", "cat": "Accessories", "price": 24.99, "reorder": 18, "archetype": "normal"},

    # --- HOME (15) ---
    {"sku": "HOME-001", "name": "Ultrasonic Essential Oil Aromatherapy Diffuser", "cat": "Home", "price": 29.99, "reorder": 18, "archetype": "stockout_risk"},
    {"sku": "HOME-002", "name": "Double-Wall Insulated Stainless Steel Bottle", "cat": "Home", "price": 21.99, "reorder": 25, "archetype": "normal"},
    {"sku": "HOME-003", "name": "Ergonomic Memory Foam Seat Cushion", "cat": "Home", "price": 34.99, "reorder": 14, "archetype": "normal"},
    {"sku": "HOME-004", "name": "Velvet Decorative Throw Pillow Covers 2-Pack", "cat": "Home", "price": 17.99, "reorder": 20, "archetype": "normal"},
    {"sku": "HOME-005", "name": "Handmade Ceramic Coffee Mug Set of 4", "cat": "Home", "price": 32.99, "reorder": 12, "archetype": "normal"},
    {"sku": "HOME-006", "name": "Expandable Bamboo Kitchen Drawer Organizer", "cat": "Home", "price": 26.99, "reorder": 15, "archetype": "spike"},
    {"sku": "HOME-007", "name": "Digital Indoor Humidity & Temperature Monitor", "cat": "Home", "price": 13.99, "reorder": 20, "archetype": "normal"},
    {"sku": "HOME-008", "name": "Rechargeable Motion Sensor LED Night Light 3-Pack", "cat": "Home", "price": 19.99, "reorder": 22, "archetype": "normal"},
    {"sku": "HOME-009", "name": "Quick-Dry Chenille Non-Slip Bath Mat", "cat": "Home", "price": 16.99, "reorder": 20, "archetype": "normal"},
    {"sku": "HOME-010", "name": "Pure Lavender & Eucalyptus Essential Oil Set", "cat": "Home", "price": 18.99, "reorder": 18, "archetype": "normal"},
    {"sku": "HOME-011", "name": "Hand-Poured Scented Soy Wax Aromatherapy Candle", "cat": "Home", "price": 15.99, "reorder": 20, "archetype": "drop"},
    {"sku": "HOME-012", "name": "Foldable Fabric Wardrobe Storage Bins 3-Pack", "cat": "Home", "price": 24.99, "reorder": 15, "archetype": "normal"},
    {"sku": "HOME-013", "name": "Magnetic Wall-Mounted Stainless Knife Bar", "cat": "Home", "price": 22.99, "reorder": 10, "archetype": "overstock"},
    {"sku": "HOME-014", "name": "Vacuum Insulated Stainless Steel Food Jar", "cat": "Home", "price": 25.99, "reorder": 14, "archetype": "normal"},
    {"sku": "HOME-015", "name": "Natural Woven Cotton Linen Table Runner", "cat": "Home", "price": 19.99, "reorder": 12, "archetype": "normal"},

    # --- KITCHEN (15) ---
    {"sku": "KTCH-001", "name": "Heat-Resistant Silicone Cooking Utensil Set 10pc", "cat": "Kitchen", "price": 32.99, "reorder": 18, "archetype": "stockout_risk"},
    {"sku": "KTCH-002", "name": "High-Precision Digital Kitchen Food Scale", "cat": "Kitchen", "price": 18.99, "reorder": 20, "archetype": "normal"},
    {"sku": "KTCH-003", "name": "Borosilicate Glass French Press Coffee Maker", "cat": "Kitchen", "price": 26.99, "reorder": 15, "archetype": "normal"},
    {"sku": "KTCH-004", "name": "Stainless Steel Manual Conical Burr Grinder", "cat": "Kitchen", "price": 39.99, "reorder": 10, "archetype": "overstock"},
    {"sku": "KTCH-005", "name": "Heavy-Duty Multi-Purpose Chef Kitchen Shears", "cat": "Kitchen", "price": 14.99, "reorder": 25, "archetype": "normal"},
    {"sku": "KTCH-006", "name": "Airtight Glass Meal Prep Containers Set of 5", "cat": "Kitchen", "price": 36.99, "reorder": 16, "archetype": "spike"},
    {"sku": "KTCH-007", "name": "Granite Non-Stick 10-Inch Omelette Frying Pan", "cat": "Kitchen", "price": 42.99, "reorder": 14, "archetype": "normal"},
    {"sku": "KTCH-008", "name": "Stainless Steel Heavy Gauge Measuring Spoons Set", "cat": "Kitchen", "price": 11.99, "reorder": 30, "archetype": "normal"},
    {"sku": "KTCH-009", "name": "Non-Stick Silicone Baking Mats 2-Pack", "cat": "Kitchen", "price": 15.99, "reorder": 22, "archetype": "normal"},
    {"sku": "KTCH-010", "name": "Handheld Battery-Operated Milk Frother Whisk", "cat": "Kitchen", "price": 12.99, "reorder": 25, "archetype": "normal"},
    {"sku": "KTCH-011", "name": "Pre-Seasoned Cast Iron Skillet 12-Inch", "cat": "Kitchen", "price": 46.99, "reorder": 10, "archetype": "drop"},
    {"sku": "KTCH-012", "name": "Fresh Herb Keeper and Storage Pod", "cat": "Kitchen", "price": 16.99, "reorder": 15, "archetype": "normal"},
    {"sku": "KTCH-013", "name": "Double-Walled Insulated Glass Espresso Cups 2pc", "cat": "Kitchen", "price": 19.99, "reorder": 18, "archetype": "normal"},
    {"sku": "KTCH-014", "name": "Electric Automatic Wine Bottle Opener Corkscrew", "cat": "Kitchen", "price": 28.99, "reorder": 12, "archetype": "normal"},
    {"sku": "KTCH-015", "name": "Organic Bamboo Large End-Grain Cutting Board", "cat": "Kitchen", "price": 34.99, "reorder": 15, "archetype": "normal"},

    # --- PERSONAL CARE (15) ---
    {"sku": "CARE-001", "name": "Sonic Electric Toothbrush with 4 Brush Heads", "cat": "Personal Care", "price": 44.99, "reorder": 18, "archetype": "stockout_risk"},
    {"sku": "CARE-002", "name": "Waterproof Cordless Beard Trimmer & Styler", "cat": "Personal Care", "price": 38.99, "reorder": 16, "archetype": "normal"},
    {"sku": "CARE-003", "name": "Clarifying Organic Tea Tree Foaming Face Wash", "cat": "Personal Care", "price": 15.99, "reorder": 25, "archetype": "spike"},
    {"sku": "CARE-004", "name": "Pure Vitamin C 20% + Hyaluronic Acid Serum", "cat": "Personal Care", "price": 22.99, "reorder": 20, "archetype": "normal"},
    {"sku": "CARE-005", "name": "Percussive Deep Tissue Muscle Massage Gun", "cat": "Personal Care", "price": 89.99, "reorder": 8, "archetype": "overstock"},
    {"sku": "CARE-006", "name": "Activated Charcoal Enamel Whitening Toothpaste", "cat": "Personal Care", "price": 8.99, "reorder": 35, "archetype": "normal"},
    {"sku": "CARE-007", "name": "Silicone Hair Growth Scalp Massager Shampoo Brush", "cat": "Personal Care", "price": 7.99, "reorder": 30, "archetype": "normal"},
    {"sku": "CARE-008", "name": "Broad Spectrum SPF 50 Mineral Daily Sunscreen", "cat": "Personal Care", "price": 19.99, "reorder": 25, "archetype": "drop"},
    {"sku": "CARE-009", "name": "Organic Soothing 99% Pure Aloe Vera Gel", "cat": "Personal Care", "price": 11.99, "reorder": 28, "archetype": "normal"},
    {"sku": "CARE-010", "name": "Cedarwood & Jojoba Conditioning Beard Oil", "cat": "Personal Care", "price": 16.99, "reorder": 18, "archetype": "normal"},
    {"sku": "CARE-011", "name": "Tourmaline Ceramic Hair Straightening Flat Iron", "cat": "Personal Care", "price": 49.99, "reorder": 12, "archetype": "normal"},
    {"sku": "CARE-012", "name": "Ionic Negative Ion Salon Fast Blow Dryer", "cat": "Personal Care", "price": 59.99, "reorder": 10, "archetype": "normal"},
    {"sku": "CARE-013", "name": "Relaxing French Lavender Epsom Bath Soak Crystals", "cat": "Personal Care", "price": 13.99, "reorder": 20, "archetype": "normal"},
    {"sku": "CARE-014", "name": "Collagen Plumping Hydrating Sheet Mask 6-Pack", "cat": "Personal Care", "price": 14.99, "reorder": 25, "archetype": "normal"},
    {"sku": "CARE-015", "name": "Surgical Stainless Steel Manicure & Pedicure Set", "cat": "Personal Care", "price": 18.99, "reorder": 20, "archetype": "normal"},

    # --- OFFICE (15) ---
    {"sku": "OFFC-001", "name": "Ergonomic Memory Foam Keyboard Wrist Rest Pad", "cat": "Office", "price": 17.99, "reorder": 20, "archetype": "stockout_risk"},
    {"sku": "OFFC-002", "name": "Dual-Sided PU Leather Extended Desk Blotter Mat", "cat": "Office", "price": 21.99, "reorder": 18, "archetype": "spike"},
    {"sku": "OFFC-003", "name": "3-Tier Steel Mesh Desk Paper Document Tray", "cat": "Office", "price": 24.99, "reorder": 14, "archetype": "normal"},
    {"sku": "OFFC-004", "name": "Compact Desktop Cross-Cut Security Paper Shredder", "cat": "Office", "price": 64.99, "reorder": 8, "archetype": "overstock"},
    {"sku": "OFFC-005", "name": "Quick-Dry Retractable Gel Roller Pens 10-Pack", "cat": "Office", "price": 12.99, "reorder": 35, "archetype": "normal"},
    {"sku": "OFFC-006", "name": "Glass Desktop Whiteboard with Marker Drawer", "cat": "Office", "price": 32.99, "reorder": 12, "archetype": "normal"},
    {"sku": "OFFC-007", "name": "Foldable Ergonomic Vented Laptop Riser Stand", "cat": "Office", "price": 27.99, "reorder": 16, "archetype": "normal"},
    {"sku": "OFFC-008", "name": "Super Sticky Pastel Note Pads 6-Pack 3x3in", "cat": "Office", "price": 8.99, "reorder": 40, "archetype": "normal"},
    {"sku": "OFFC-009", "name": "Undated Productivity Goal Weekly Planner Notebook", "cat": "Office", "price": 16.99, "reorder": 20, "archetype": "drop"},
    {"sku": "OFFC-010", "name": "Under-Desk Flame Retardant Cable Management Box", "cat": "Office", "price": 19.99, "reorder": 18, "archetype": "normal"},
    {"sku": "OFFC-011", "name": "Adjustable Ergonomic Footrest with Massage Bumps", "cat": "Office", "price": 34.99, "reorder": 14, "archetype": "normal"},
    {"sku": "OFFC-012", "name": "Heavy Duty Plier Stapler with 2000 Staples", "cat": "Office", "price": 15.99, "reorder": 22, "archetype": "normal"},
    {"sku": "OFFC-013", "name": "Low-Odor Chisel Tip Dry Erase Markers 8-Pack", "cat": "Office", "price": 10.99, "reorder": 30, "archetype": "normal"},
    {"sku": "OFFC-014", "name": "Rotatable Acrylic Art & Office Supply Caddy", "cat": "Office", "price": 18.99, "reorder": 16, "archetype": "normal"},
    {"sku": "OFFC-015", "name": "Tear-Free Correction Tape Dispensers 6-Pack", "cat": "Office", "price": 9.99, "reorder": 30, "archetype": "normal"},
]


def generate_retail_dataset(
    start_date: date = date.today() - timedelta(days=180),
    days_count: int = 180,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Tuple], List[Tuple]]:
    """
    Generate deterministic retail dataset records.
    Returns (stores, products, sales_records, inventory_records)
    """
    random.seed(SEED_VALUE)

    # 1. Stores
    stores = STORES_DATA

    # 2. Products
    products = PRODUCTS_DEFINITIONS

    sales_records: List[Tuple] = []
    inventory_records: List[Tuple] = []

    # Store multipliers (flagship vs neighborhood variations)
    store_multipliers = {
        "STR-001": 1.25,  # Chennai Central (Flagship)
        "STR-002": 1.05,  # Anna Nagar
        "STR-003": 0.90,  # Velachery
        "STR-004": 1.15,  # T. Nagar
    }

    # Store ID mapping (1-indexed based on insertion order)
    # Store 1: STR-001, Store 2: STR-002, Store 3: STR-003, Store 4: STR-004

    for store_idx, store in enumerate(stores, start=1):
        s_mult = store_multipliers[store["store_code"]]

        for prod_idx, prod in enumerate(products, start=1):
            archetype = prod["archetype"]
            unit_price = prod["price"]
            reorder_level = prod["reorder"]

            # Generate 180 days of daily sales
            for day_offset in range(days_count):
                current_date = start_date + timedelta(days=day_offset)
                is_weekend = current_date.weekday() >= 5
                weekend_mult = 1.35 if is_weekend else 1.0

                # Determine sales probability and base quantity based on archetype & time window
                # The last 21 days (3 weeks) represent the recent window
                is_recent = day_offset >= (days_count - 21)

                if archetype == "normal":
                    sale_prob = 0.55 * s_mult
                    base_qty = random.randint(1, 4)
                elif archetype == "stockout_risk":
                    # High recent demand surge
                    if is_recent:
                        sale_prob = 0.88 * s_mult
                        base_qty = random.randint(4, 9)
                    else:
                        sale_prob = 0.60 * s_mult
                        base_qty = random.randint(2, 5)
                elif archetype == "overstock":
                    # Consistently slow moving
                    sale_prob = 0.08 * s_mult
                    base_qty = 1
                elif archetype == "spike":
                    # Sudden sharp sales spike in recent weeks
                    if is_recent:
                        sale_prob = 0.92 * s_mult
                        base_qty = random.randint(6, 12)
                    else:
                        sale_prob = 0.30 * s_mult
                        base_qty = random.randint(1, 2)
                elif archetype == "drop":
                    # High historical sales that collapsed recently
                    if is_recent:
                        sale_prob = 0.08 * s_mult
                        base_qty = 1
                    else:
                        sale_prob = 0.85 * s_mult
                        base_qty = random.randint(5, 10)
                else:
                    sale_prob = 0.50
                    base_qty = random.randint(1, 3)

                # Random variation with weekend lift
                if random.random() < min(sale_prob * weekend_mult, 0.98):
                    qty = max(1, int(round(base_qty * (0.8 + 0.4 * random.random()))))
                    revenue = round(qty * unit_price, 2)
                    sales_records.append((
                        current_date.isoformat(),
                        store_idx,
                        prod_idx,
                        qty,
                        unit_price,
                        revenue,
                    ))

            # Generate current inventory record for this (store, product)
            if archetype == "normal":
                stock = random.randint(35, 75)
            elif archetype == "stockout_risk":
                # Stock depleted below reorder level
                stock = random.randint(1, max(2, int(reorder_level * 0.35)))
            elif archetype == "overstock":
                # High excess stock relative to zero/low demand
                stock = random.randint(90, 160)
            elif archetype == "spike":
                # Stock running thin due to recent spike
                stock = random.randint(18, 38)
            elif archetype == "drop":
                # Excess stock accumulated before the demand dropped
                stock = random.randint(70, 110)
            else:
                stock = random.randint(25, 50)

            inventory_records.append((
                store_idx,
                prod_idx,
                stock,
            ))

    return stores, products, sales_records, inventory_records


def seed_database(force: bool = False) -> Dict[str, int]:
    """
    Seed SQLite database with retail dataset if empty or if forced.
    Returns record counts of seeded entities.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM stores")
        store_count = cursor.fetchone()[0]

        if store_count > 0 and not force:
            logger.info("Database already contains records. Skipping seed.")
            cursor.execute("SELECT COUNT(*) FROM products")
            prod_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM sales")
            sales_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM inventory")
            inv_count = cursor.fetchone()[0]
            return {
                "stores": store_count,
                "products": prod_count,
                "sales": sales_count,
                "inventory": inv_count,
            }

        if force:
            logger.info("Force flag set: clearing existing retail records...")
            cursor.execute("DELETE FROM sales")
            cursor.execute("DELETE FROM inventory")
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM stores")

        logger.info("Generating and seeding retail dataset...")
        stores, products, sales, inventory = generate_retail_dataset()

        # Insert Stores
        cursor.executemany(
            "INSERT INTO stores (store_code, store_name, city) VALUES (?, ?, ?)",
            [(s["store_code"], s["store_name"], s["city"]) for s in stores],
        )

        # Insert Products
        cursor.executemany(
            "INSERT INTO products (sku, product_name, category, unit_price, reorder_level) VALUES (?, ?, ?, ?, ?)",
            [(p["sku"], p["name"], p["cat"], p["price"], p["reorder"]) for p in products],
        )

        # Fetch created store and product ID maps
        cursor.execute("SELECT id, store_code FROM stores")
        store_map = {row["store_code"]: row["id"] for row in cursor.fetchall()}

        cursor.execute("SELECT id, sku FROM products")
        product_map = {row["sku"]: row["id"] for row in cursor.fetchall()}

        # Remap sales and inventory to actual database IDs
        # sales: (date_str, store_idx_1based, prod_idx_1based, qty, unit_price, revenue)
        store_codes_list = [s["store_code"] for s in stores]
        product_skus_list = [p["sku"] for p in products]

        remapped_sales = [
            (
                s[0],
                store_map[store_codes_list[s[1] - 1]],
                product_map[product_skus_list[s[2] - 1]],
                s[3],
                s[4],
                s[5],
            )
            for s in sales
        ]

        remapped_inventory = [
            (
                store_map[store_codes_list[i[0] - 1]],
                product_map[product_skus_list[i[1] - 1]],
                i[2],
            )
            for i in inventory
        ]

        # Insert Sales
        cursor.executemany(
            """
            INSERT INTO sales (sale_date, store_id, product_id, quantity, unit_price, revenue)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            remapped_sales,
        )

        # Insert Inventory
        cursor.executemany(
            """
            INSERT INTO inventory (store_id, product_id, stock_quantity)
            VALUES (?, ?, ?)
            """,
            remapped_inventory,
        )

        logger.info(
            f"Seeding completed successfully: {len(stores)} stores, {len(products)} products, "
            f"{len(sales)} sales, {len(inventory)} inventory records."
        )

        return {
            "stores": len(stores),
            "products": len(products),
            "sales": len(sales),
            "inventory": len(inventory),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    counts = seed_database(force=True)
    print(f"Retail dataset seeded successfully: {counts}")
