from typing import Optional, List, Dict, Any
import logging
from backend.database.connection import get_db_connection
from backend.models.product import ProductItem, ProductListResponse

logger = logging.getLogger("retail_copilot.services.product")


class ProductService:
    @staticmethod
    def get_products(
        search: Optional[str] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> ProductListResponse:
        """
        Query master product catalog from SQLite database with parameterized search and category filtering.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Get total count across all products
            cursor.execute("SELECT COUNT(*) FROM products")
            total_count = cursor.fetchone()[0]

            # 2. Get distinct categories
            cursor.execute("SELECT DISTINCT category FROM products ORDER BY category ASC")
            categories = [row["category"] for row in cursor.fetchall()]

            # 3. Build filtered query with parameterized WHERE conditions
            query_conditions = []
            params: List[Any] = []

            if category and category.strip() and category.strip().upper() != "ALL":
                query_conditions.append("category = ?")
                params.append(category.strip())

            if search and search.strip():
                clean_search = f"%{search.strip()}%"
                query_conditions.append("(product_name LIKE ? OR sku LIKE ?)")
                params.extend([clean_search, clean_search])

            where_clause = ""
            if query_conditions:
                where_clause = "WHERE " + " AND ".join(query_conditions)

            # Filtered count
            count_sql = f"SELECT COUNT(*) FROM products {where_clause}"
            cursor.execute(count_sql, params)
            filtered_count = cursor.fetchone()[0]

            # Select products
            select_sql = f"""
                SELECT id, sku, product_name, category, unit_price, reorder_level, created_at
                FROM products
                {where_clause}
                ORDER BY category ASC, product_name ASC
            """
            
            if limit is not None and limit > 0:
                select_sql += " LIMIT ? OFFSET ?"
                params.extend([limit, offset or 0])

            cursor.execute(select_sql, params)
            rows = cursor.fetchall()

            products = [
                ProductItem(
                    id=row["id"],
                    sku=row["sku"],
                    product_name=row["product_name"],
                    category=row["category"],
                    unit_price=float(row["unit_price"]),
                    reorder_level=float(row["reorder_level"]),
                    created_at=str(row["created_at"]) if row["created_at"] else None,
                )
                for row in rows
            ]

        return ProductListResponse(
            total_count=total_count,
            filtered_count=filtered_count,
            categories=categories,
            products=products,
        )
