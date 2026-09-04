import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from backend.config import settings

_db_initialized = False


def _ensure_tables_exist(conn: sqlite3.Connection):
    global _db_initialized
    if _db_initialized:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stores'")
        row = cursor.fetchone()
        if not row:
            from backend.database.schema import init_db
            init_db(seed=True)
        _db_initialized = True
    except Exception as e:
        print(f"Warning during table check: {e}")


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create and return a configured SQLite connection with foreign key enforcement."""
    if db_path is None:
        db_path = settings.get_db_path()

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(db_path),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        check_same_thread=False,
    )
    # Enable foreign key constraint enforcement
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for obtaining a database connection with auto-commit/rollback."""
    conn = get_connection()
    _ensure_tables_exist(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
