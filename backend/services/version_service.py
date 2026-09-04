import logging
from backend.database.connection import get_db_connection

logger = logging.getLogger("retail_copilot.version_service")


class DataVersionService:
    """Service to track, retrieve, and increment the authoritative retail data version."""

    @staticmethod
    def get_data_version() -> int:
        """Fetch the current integer data version from SQLite system_state."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_state WHERE key = 'data_version'")
                row = cursor.fetchone()
                if row and row["value"]:
                    return int(row["value"])
                
                # Default initialize if missing
                cursor.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES ('data_version', '1')")
                return 1
        except Exception as e:
            logger.error(f"Error fetching data_version: {e}", exc_info=True)
            return 1

    @staticmethod
    def increment_data_version() -> int:
        """
        Increment the data version counter by 1.
        Called whenever products, stores, sales, or inventory data is modified.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_state WHERE key = 'data_version'")
                row = cursor.fetchone()
                current_ver = int(row["value"]) if (row and row["value"]) else 1
                new_ver = current_ver + 1
                cursor.execute(
                    """
                    INSERT INTO system_state (key, value, updated_at) 
                    VALUES ('data_version', ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET 
                        value = excluded.value, 
                        updated_at = excluded.updated_at
                    """,
                    (str(new_ver),),
                )
                logger.info(f"Data version successfully incremented from {current_ver} to {new_ver}.")
                return new_ver
        except Exception as e:
            logger.error(f"Error incrementing data_version: {e}", exc_info=True)
            return 1
