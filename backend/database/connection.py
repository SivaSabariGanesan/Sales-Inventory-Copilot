import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from backend.config import settings


def get_connection(db_path: Path = settings.DB_PATH) -> sqlite3.Connection:
    """Create and return a configured SQLite connection with foreign key enforcement."""
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
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
