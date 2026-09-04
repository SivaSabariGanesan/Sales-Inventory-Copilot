from typing import Optional, List, Any
import logging
from backend.database.connection import get_db_connection
from backend.models.store import StoreItem, StoreOverviewKPIs, StoreListResponse

logger = logging.getLogger("retail_copilot.services.store")


class StoreService:
    @staticmethod
    def get_stores(search: Optional[str] = None) -> StoreListResponse:
        """
        Query physical store network from SQLite database with real inventory statistics.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Overall KPIs
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT city) FROM stores")
            kpi_row = cursor.fetchone()
            total_locations = kpi_row[0] if kpi_row else 0
            regions_covered = kpi_row[1] if kpi_row else 0

            cursor.execute("SELECT COUNT(DISTINCT product_id), COALESCE(SUM(stock_quantity), 0) FROM inventory")
            inv_kpi_row = cursor.fetchone()
            total_skus_stocked = inv_kpi_row[0] if inv_kpi_row else 0
            total_inventory_units = int(inv_kpi_row[1]) if inv_kpi_row else 0

            kpis = StoreOverviewKPIs(
                total_locations=total_locations,
                regions_covered=regions_covered,
                total_skus_stocked=total_skus_stocked,
                total_inventory_units=total_inventory_units,
            )

            # 2. Store Query with inventory aggregation
            query_conditions = []
            params: List[Any] = []

            if search and search.strip():
                clean_search = f"%{search.strip()}%"
                query_conditions.append("(s.store_name LIKE ? OR s.store_code LIKE ? OR s.city LIKE ?)")
                params.extend([clean_search, clean_search, clean_search])

            where_clause = ""
            if query_conditions:
                where_clause = "WHERE " + " AND ".join(query_conditions)

            select_sql = f"""
                SELECT 
                    s.id,
                    s.store_code,
                    s.store_name,
                    s.city,
                    s.created_at,
                    COUNT(i.product_id) as total_skus,
                    COALESCE(SUM(i.stock_quantity), 0) as total_inventory_units
                FROM stores s
                LEFT JOIN inventory i ON s.id = i.store_id
                {where_clause}
                GROUP BY s.id, s.store_code, s.store_name, s.city, s.created_at
                ORDER BY s.store_code ASC
            """

            cursor.execute(select_sql, params)
            rows = cursor.fetchall()

            stores = [
                StoreItem(
                    id=row["id"],
                    store_code=row["store_code"],
                    store_name=row["store_name"],
                    city=row["city"],
                    status="Active",
                    total_skus=row["total_skus"],
                    total_inventory_units=int(row["total_inventory_units"]),
                    created_at=str(row["created_at"]) if row["created_at"] else None,
                )
                for row in rows
            ]

        return StoreListResponse(kpis=kpis, stores=stores)
