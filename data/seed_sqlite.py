"""
Pharma Sales Analytics -- SQLite Seeder
========================================
Creates and populates pharma.db for zero-config SQLite deployment on Streamlit Cloud.
"""

import sqlite3
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent
PROJECT_ROOT = DATA_DIR.parent


def seed_sqlite(db_path=None):
    """Seed SQLite database from CSVs."""
    if db_path is None:
        db_path = PROJECT_ROOT / "pharma.db"

    # Make sure CSVs exist
    sales_csv = DATA_DIR / "sales.csv"
    if not sales_csv.exists():
        print("CSV files not found. Running generate_data.py...")
        import data.generate_data  # noqa

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Drop existing tables
    for tbl in ["sales", "physicians", "reps", "products", "territories"]:
        cur.execute(f"DROP TABLE IF EXISTS {tbl}")

    # Create tables
    cur.execute("""
    CREATE TABLE territories (
        territory_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        region TEXT NOT NULL,
        manager TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE reps (
        rep_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        territory_id INTEGER NOT NULL,
        hire_date TEXT NOT NULL,
        target_quota REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price_per_unit REAL NOT NULL,
        launch_date TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE physicians (
        physician_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        territory_id INTEGER NOT NULL,
        tier TEXT NOT NULL,
        hospital_affiliation TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE sales (
        sale_id INTEGER PRIMARY KEY,
        rep_id INTEGER NOT NULL,
        physician_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        sale_date TEXT NOT NULL,
        amount REAL NOT NULL
    );
    """)

    # Load CSVs into pandas and write to SQLite
    tables = [
        ("territories", "territories.csv"),
        ("reps", "reps.csv"),
        ("products", "products.csv"),
        ("physicians", "physicians.csv"),
        ("sales", "sales.csv"),
    ]

    for table_name, csv_file in tables:
        df = pd.read_csv(DATA_DIR / csv_file)
        df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"  [OK] SQLite {table_name}: {len(df)} rows loaded")

    # Create indexes
    cur.execute("CREATE INDEX idx_sales_rep ON sales(rep_id);")
    cur.execute("CREATE INDEX idx_sales_physician ON sales(physician_id);")
    cur.execute("CREATE INDEX idx_sales_product ON sales(product_id);")
    cur.execute("CREATE INDEX idx_sales_date ON sales(sale_date);")

    conn.commit()
    conn.close()
    print("SQLite database successfully created and seeded!")


if __name__ == "__main__":
    seed_sqlite()
