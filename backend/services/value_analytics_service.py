import logging
from typing import Optional, List, Dict, Any
from backend.database.connection import get_db_connection
from backend.models.value_analytics import (
    ProductValueSummary,
    StoreValueSummary,
    CategoryValueSummary,
    OverstockValueSummary,
    ValueAnalyticsResponse,
)
from backend.services.overstock_service import OverstockService

logger = logging.getLogger("retail_copilot.value_analytics")


class ValueAnalyticsService:
    """
    Deterministic service for financial, revenue, and inventory value calculations.
    All calculations are strictly executed in Python/SQLite with zero hallucination.
    """

    @classmethod
    def calculate_inventory_value(
        cls,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        product_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate inventory value (stock_quantity * unit_price) overall and across dimensions.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Base inventory query with filters
            where_clauses = ["1=1"]
            params = []

            if store_id:
                where_clauses.append("i.store_id = ?")
                params.append(store_id)
            if category and category.strip().upper() != "ALL":
                where_clauses.append("p.category = ?")
                params.append(category.strip())
            if product_id:
                where_clauses.append("p.id = ?")
                params.append(product_id)

            where_str = " AND ".join(where_clauses)

            # 1. Total inventory value and units
            total_sql = f"""
                SELECT 
                    COALESCE(SUM(i.stock_quantity * COALESCE(p.unit_price, 0.0)), 0.0) as total_val,
                    COALESCE(SUM(i.stock_quantity), 0) as total_units
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                WHERE {where_str}
            """
            cursor.execute(total_sql, params)
            total_row = cursor.fetchone()
            total_val = round(float(total_row["total_val"] or 0.0), 2)
            total_units = int(total_row["total_units"] or 0)

            # 2. Inventory value by Store
            store_sql = f"""
                SELECT 
                    s.id as store_id,
                    s.store_name,
                    s.store_code,
                    COALESCE(SUM(i.stock_quantity * COALESCE(p.unit_price, 0.0)), 0.0) as store_val,
                    COALESCE(SUM(i.stock_quantity), 0) as store_units
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                JOIN stores s ON i.store_id = s.id
                WHERE {where_str}
                GROUP BY s.id, s.store_name, s.store_code
                ORDER BY store_val DESC
            """
            cursor.execute(store_sql, params)
            store_rows = cursor.fetchall()
            stores_summary = [
                {
                    "store_id": r["store_id"],
                    "store_name": r["store_name"],
                    "store_code": r["store_code"],
                    "inventory_value": round(float(r["store_val"] or 0.0), 2),
                    "stock_units": int(r["store_units"] or 0),
                }
                for r in store_rows
            ]

            # 3. Inventory value by Category
            cat_sql = f"""
                SELECT 
                    p.category,
                    COALESCE(SUM(i.stock_quantity * COALESCE(p.unit_price, 0.0)), 0.0) as cat_val,
                    COALESCE(SUM(i.stock_quantity), 0) as cat_units
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                WHERE {where_str}
                GROUP BY p.category
                ORDER BY cat_val DESC
            """
            cursor.execute(cat_sql, params)
            cat_rows = cursor.fetchall()
            cat_summary = [
                {
                    "category": r["category"],
                    "inventory_value": round(float(r["cat_val"] or 0.0), 2),
                    "stock_units": int(r["cat_units"] or 0),
                }
                for r in cat_rows
            ]

            # 4. Top inventory value products
            prod_sql = f"""
                SELECT 
                    p.id as product_id,
                    p.sku,
                    p.product_name,
                    p.category,
                    COALESCE(p.unit_price, 0.0) as unit_price,
                    COALESCE(SUM(i.stock_quantity), 0) as total_stock,
                    COALESCE(SUM(i.stock_quantity * COALESCE(p.unit_price, 0.0)), 0.0) as prod_val
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                WHERE {where_str}
                GROUP BY p.id, p.sku, p.product_name, p.category, p.unit_price
                ORDER BY prod_val DESC
                LIMIT 10
            """
            cursor.execute(prod_sql, params)
            prod_rows = cursor.fetchall()
            top_products = [
                ProductValueSummary(
                    product_id=r["product_id"],
                    sku=r["sku"],
                    product_name=r["product_name"],
                    category=r["category"],
                    unit_price=round(float(r["unit_price"] or 0.0), 2),
                    total_stock_quantity=int(r["total_stock"] or 0),
                    inventory_value=round(float(r["prod_val"] or 0.0), 2),
                    total_sales_quantity=0,
                    total_revenue=0.0,
                )
                for r in prod_rows
            ]

            return {
                "total_inventory_value": total_val,
                "total_stock_units": total_units,
                "stores_summary": stores_summary,
                "category_summary": cat_summary,
                "top_products": top_products,
            }

    @classmethod
    def calculate_sales_revenue(
        cls,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate sales revenue using authoritative stored `revenue` field
        with deterministic `quantity * unit_price` fallback.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            where_clauses = ["1=1"]
            params = []

            if store_id:
                where_clauses.append("s.store_id = ?")
                params.append(store_id)
            if category and category.strip().upper() != "ALL":
                where_clauses.append("p.category = ?")
                params.append(category.strip())
            if product_id:
                where_clauses.append("s.product_id = ?")
                params.append(product_id)
            if start_date:
                where_clauses.append("s.date >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("s.date <= ?")
                params.append(end_date)

            where_str = " AND ".join(where_clauses)

            # 1. Total revenue and sales units
            total_sql = f"""
                SELECT 
                    COALESCE(SUM(COALESCE(s.revenue, s.quantity * COALESCE(s.unit_price, p.unit_price, 0.0))), 0.0) as total_rev,
                    COALESCE(SUM(s.quantity), 0) as total_units
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE {where_str}
            """
            cursor.execute(total_sql, params)
            total_row = cursor.fetchone()
            total_rev = round(float(total_row["total_rev"] or 0.0), 2)
            total_units = int(total_row["total_units"] or 0)

            # 2. Revenue by Store
            store_sql = f"""
                SELECT 
                    st.id as store_id,
                    st.store_name,
                    st.store_code,
                    COALESCE(SUM(COALESCE(s.revenue, s.quantity * COALESCE(s.unit_price, p.unit_price, 0.0))), 0.0) as store_rev,
                    COALESCE(SUM(s.quantity), 0) as store_units
                FROM sales s
                JOIN stores st ON s.store_id = st.id
                JOIN products p ON s.product_id = p.id
                WHERE {where_str}
                GROUP BY st.id, st.store_name, st.store_code
                ORDER BY store_rev DESC
            """
            cursor.execute(store_sql, params)
            store_rows = cursor.fetchall()
            stores_revenue = [
                {
                    "store_id": r["store_id"],
                    "store_name": r["store_name"],
                    "store_code": r["store_code"],
                    "revenue": round(float(r["store_rev"] or 0.0), 2),
                    "sales_units": int(r["store_units"] or 0),
                }
                for r in store_rows
            ]

            # 3. Revenue by Category
            cat_sql = f"""
                SELECT 
                    p.category,
                    COALESCE(SUM(COALESCE(s.revenue, s.quantity * COALESCE(s.unit_price, p.unit_price, 0.0))), 0.0) as cat_rev,
                    COALESCE(SUM(s.quantity), 0) as cat_units
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE {where_str}
                GROUP BY p.category
                ORDER BY cat_rev DESC
            """
            cursor.execute(cat_sql, params)
            cat_rows = cursor.fetchall()
            cat_revenue = [
                {
                    "category": r["category"],
                    "revenue": round(float(r["cat_rev"] or 0.0), 2),
                    "sales_units": int(r["cat_units"] or 0),
                }
                for r in cat_rows
            ]

            # 4. Top products by Revenue
            prod_sql = f"""
                SELECT 
                    p.id as product_id,
                    p.sku,
                    p.product_name,
                    p.category,
                    COALESCE(p.unit_price, 0.0) as unit_price,
                    COALESCE(SUM(s.quantity), 0) as sales_units,
                    COALESCE(SUM(COALESCE(s.revenue, s.quantity * COALESCE(s.unit_price, p.unit_price, 0.0))), 0.0) as prod_rev
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE {where_str}
                GROUP BY p.id, p.sku, p.product_name, p.category, p.unit_price
                ORDER BY prod_rev DESC
                LIMIT 10
            """
            cursor.execute(prod_sql, params)
            prod_rows = cursor.fetchall()
            top_products = [
                ProductValueSummary(
                    product_id=r["product_id"],
                    sku=r["sku"],
                    product_name=r["product_name"],
                    category=r["category"],
                    unit_price=round(float(r["unit_price"] or 0.0), 2),
                    total_stock_quantity=0,
                    inventory_value=0.0,
                    total_sales_quantity=int(r["sales_units"] or 0),
                    total_revenue=round(float(r["prod_rev"] or 0.0), 2),
                )
                for r in prod_rows
            ]

            return {
                "total_sales_revenue": total_rev,
                "total_sales_units": total_units,
                "stores_revenue": stores_revenue,
                "category_revenue": cat_revenue,
                "top_products": top_products,
            }

    @classmethod
    def calculate_overstock_value(
        cls,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> OverstockValueSummary:
        """
        Calculates tied-up inventory value in overstocked and slow-moving items
        by reusing the existing deterministic OverstockService.
        """
        overstock_data = OverstockService.calculate_overstock(store_id=store_id, category=category)

        # Retrieve unit prices for affected products in one query
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, unit_price FROM products")
            prices_map = {r["id"]: float(r["unit_price"] or 0.0) for r in cursor.fetchall()}

        total_overstock_val = 0.0
        severe_val = 0.0
        moderate_val = 0.0
        no_demand_val = 0.0
        slow_moving_val = 0.0

        affected_product_ids = set()
        affected_store_ids = set()
        product_tied_up = {}

        for item in overstock_data.results:
            price = prices_map.get(item.product_id, 0.0)
            item_val = round(item.current_stock * price, 2)
            total_overstock_val += item_val

            affected_product_ids.add(item.product_id)
            affected_store_ids.add(item.store_id)

            if item.product_id not in product_tied_up:
                product_tied_up[item.product_id] = {
                    "product_name": item.product_name,
                    "sku": item.sku,
                    "category": item.category,
                    "unit_price": price,
                    "total_stock": 0,
                    "tied_up_value": 0.0,
                }
            product_tied_up[item.product_id]["total_stock"] += item.current_stock
            product_tied_up[item.product_id]["tied_up_value"] += item_val

            if item.status == "SEVERE_OVERSTOCK":
                severe_val += item_val
            elif item.status == "OVERSTOCK":
                moderate_val += item_val
            elif item.status == "NO_RECENT_DEMAND":
                no_demand_val += item_val
            elif item.status == "SLOW_MOVING":
                slow_moving_val += item_val

        top_contributor = None
        if product_tied_up:
            top_p_id = max(product_tied_up, key=lambda pid: product_tied_up[pid]["tied_up_value"])
            top_info = product_tied_up[top_p_id]
            top_contributor = {
                "product_id": top_p_id,
                "product_name": top_info["product_name"],
                "sku": top_info["sku"],
                "category": top_info["category"],
                "unit_price": top_info["unit_price"],
                "total_stock": top_info["total_stock"],
                "tied_up_value": round(top_info["tied_up_value"], 2),
            }

        return OverstockValueSummary(
            total_overstock_inventory_value=round(total_overstock_val, 2),
            products_affected_count=len(affected_product_ids),
            stores_affected_count=len(affected_store_ids),
            severe_overstock_value=round(severe_val, 2),
            moderate_overstock_value=round(moderate_val, 2),
            no_demand_value=round(no_demand_val, 2),
            slow_moving_value=round(slow_moving_val, 2),
            top_contributing_product=top_contributor,
        )

    @classmethod
    def get_value_analytics_summary(
        cls,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ValueAnalyticsResponse:
        """
        Consolidated value analytics endpoint payload returning inventory values,
        revenues, overstock capital, and top lists.
        """
        inv_data = cls.calculate_inventory_value(store_id=store_id, category=category, product_id=product_id)
        sales_data = cls.calculate_sales_revenue(
            store_id=store_id, category=category, product_id=product_id, start_date=start_date, end_date=end_date
        )
        overstock_summary = cls.calculate_overstock_value(store_id=store_id, category=category)

        # Merge store summaries
        stores_dict = {}
        for s in inv_data["stores_summary"]:
            stores_dict[s["store_id"]] = {
                "store_id": s["store_id"],
                "store_name": s["store_name"],
                "store_code": s["store_code"],
                "total_inventory_value": s["inventory_value"],
                "total_stock_units": s["stock_units"],
                "total_revenue": 0.0,
                "total_sales_units": 0,
            }
        for s in sales_data["stores_revenue"]:
            if s["store_id"] not in stores_dict:
                stores_dict[s["store_id"]] = {
                    "store_id": s["store_id"],
                    "store_name": s["store_name"],
                    "store_code": s["store_code"],
                    "total_inventory_value": 0.0,
                    "total_stock_units": 0,
                    "total_revenue": s["revenue"],
                    "total_sales_units": s["sales_units"],
                }
            else:
                stores_dict[s["store_id"]]["total_revenue"] = s["revenue"]
                stores_dict[s["store_id"]]["total_sales_units"] = s["sales_units"]

        stores_summary_list = [
            StoreValueSummary(
                store_id=v["store_id"],
                store_name=v["store_name"],
                store_code=v["store_code"],
                total_inventory_value=v["total_inventory_value"],
                total_revenue=v["total_revenue"],
                total_stock_units=v["total_stock_units"],
                total_sales_units=v["total_sales_units"],
            )
            for v in sorted(stores_dict.values(), key=lambda x: x["total_revenue"], reverse=True)
        ]

        # Merge category summaries
        cat_dict = {}
        for c in inv_data["category_summary"]:
            cat_dict[c["category"]] = {
                "category": c["category"],
                "total_inventory_value": c["inventory_value"],
                "total_stock_units": c["stock_units"],
                "total_revenue": 0.0,
                "total_sales_units": 0,
            }
        for c in sales_data["category_revenue"]:
            if c["category"] not in cat_dict:
                cat_dict[c["category"]] = {
                    "category": c["category"],
                    "total_inventory_value": 0.0,
                    "total_stock_units": 0,
                    "total_revenue": c["revenue"],
                    "total_sales_units": c["sales_units"],
                }
            else:
                cat_dict[c["category"]]["total_revenue"] = c["revenue"]
                cat_dict[c["category"]]["total_sales_units"] = c["sales_units"]

        category_summary_list = [
            CategoryValueSummary(
                category=v["category"],
                total_inventory_value=v["total_inventory_value"],
                total_revenue=v["total_revenue"],
                total_stock_units=v["total_stock_units"],
                total_sales_units=v["total_sales_units"],
            )
            for v in sorted(cat_dict.values(), key=lambda x: x["total_revenue"], reverse=True)
        ]

        return ValueAnalyticsResponse(
            total_inventory_value=inv_data["total_inventory_value"],
            total_sales_revenue=sales_data["total_sales_revenue"],
            overstock_inventory_value=overstock_summary.total_overstock_inventory_value,
            total_stock_units=inv_data["total_stock_units"],
            total_sales_units=sales_data["total_sales_units"],
            top_products_by_revenue=sales_data["top_products"],
            top_stores_by_revenue=stores_summary_list[:5],
            top_inventory_value_products=inv_data["top_products"],
            stores_summary=stores_summary_list,
            category_summary=category_summary_list,
            overstock_summary=overstock_summary,
        )
