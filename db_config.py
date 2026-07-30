"""
Pharma Sales Analytics -- Database Configuration & Fallback Manager
===================================================================
Automatically selects between PostgreSQL (for local development)
and SQLite (for zero-config deployment on Streamlit Cloud).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).parent
load_dotenv(_PROJECT_ROOT / ".env")

# SQLite database file path
SQLITE_DB_PATH = _PROJECT_ROOT / "pharma.db"
SQLITE_URL = f"sqlite:///{SQLITE_DB_PATH.as_posix()}"

# PostgreSQL database URL from env
PG_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5434/pharma_analytics")


def is_streamlit_cloud() -> bool:
    """Detect if running in Streamlit Community Cloud environment."""
    return (
        os.getenv("STREAMLIT_CLOUD") is not None
        or os.getenv("STREAMLIT_SHARING_MODE") is not None
        or os.getenv("IS_STREAMLIT_CLOUD") == "true"
        or not os.path.exists(_PROJECT_ROOT / ".env")
    )


def get_database_url() -> tuple[str, str]:
    """
    Returns (database_url, dialect_type).
    dialect_type is either 'postgresql' or 'sqlite'.
    """
    # 1. Force SQLite if on Streamlit Cloud
    if is_streamlit_cloud():
        ensure_sqlite_database()
        return SQLITE_URL, "sqlite"

    # 2. Try PostgreSQL first for local dev
    try:
        import psycopg2
        db_port = int(os.getenv("DB_PORT", 5434))
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=db_port,
            dbname=os.getenv("DB_NAME", "pharma_analytics"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "admin123"),
            connect_timeout=2,
        )
        conn.close()
        return PG_URL, "postgresql"
    except Exception:
        # Fall back to SQLite if PostgreSQL is not available
        ensure_sqlite_database()
        return SQLITE_URL, "sqlite"


def ensure_sqlite_database():
    """Seed SQLite database if it does not already exist."""
    if not SQLITE_DB_PATH.exists() or SQLITE_DB_PATH.stat().st_size == 0:
        print("SQLite database not found. Auto-generating and seeding SQLite data...")
        from data.seed_sqlite import seed_sqlite
        seed_sqlite(SQLITE_DB_PATH)
