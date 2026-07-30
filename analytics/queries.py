"""
Pharma Sales Analytics -- Database Manager & Query Layer
========================================================
Provides a DatabaseManager class that wraps all 10 SQL queries
and returns Pandas DataFrames. Uses SQLAlchemy for connection
pooling and safe query execution with automatic PostgreSQL/SQLite
fallback via db_config.py.
"""

import os
import re
from pathlib import Path
from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool, StaticPool
from dotenv import load_dotenv

import db_config

# Load .env from project root
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# SQL directory
SQL_DIR = _PROJECT_ROOT / "sql"


class DatabaseManager:
    """
    Central database interface for the Pharma Sales Analytics dashboard.

    Automatically connects to PostgreSQL (local) or SQLite (Streamlit Cloud).

    Usage:
        db = DatabaseManager()
        df = db.get_revenue_analysis()
        db.close()
    """

    # Dangerous SQL patterns blocked in the playground
    _BLOCKED_PATTERNS = re.compile(
        r'\b(DROP|DELETE|TRUNCATE|ALTER|INSERT|UPDATE|CREATE|GRANT|REVOKE)\b',
        re.IGNORECASE
    )

    def __init__(self, database_url: str = None):
        """Initialize connection using db_config fallback."""
        if database_url:
            self.database_url = database_url
            self.dialect = "sqlite" if "sqlite" in database_url else "postgresql"
        else:
            self.database_url, self.dialect = db_config.get_database_url()

        if self.dialect == "sqlite":
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Dispose of the connection pool."""
        self.engine.dispose()

    # ------------------------------------------------------------------
    # SQL Dialect Adaptation (PostgreSQL -> SQLite)
    # ------------------------------------------------------------------

    def _adapt_sql(self, sql: str) -> str:
        """Adapt PostgreSQL dialect query to SQLite if running on SQLite."""
        if self.dialect != "sqlite":
            return sql

        adapted = sql

        # 1. STDDEV window functions -> SQLite doesn't natively support STDDEV window function
        if "STDDEV(" in adapted:
            adapted = re.sub(
                r"STDDEV\([^)]+\)\s+OVER\s*\([^)]+\)",
                r"0.0",
                adapted,
                flags=re.IGNORECASE
            )
            adapted = re.sub(r"STDDEV\([^)]+\)", r"0.0", adapted, flags=re.IGNORECASE)

        # 2. AGE calculation in cohort analysis (multiline match)
        if "AGE(" in adapted:
            adapted = re.sub(
                r"EXTRACT\(YEAR FROM AGE\([^)]+\)\)\s*\*s*4\s*\+\s*EXTRACT\(MONTH FROM AGE\([^)]+\)\)\s*/\s*3",
                r"(CAST(strftime('%Y', s.sale_date) AS INT) - CAST(strftime('%Y', rc.hire_quarter) AS INT)) * 4 + ((CAST(strftime('%m', s.sale_date) AS INT) - CAST(strftime('%m', rc.hire_quarter) AS INT)) / 3)",
                adapted,
                flags=re.IGNORECASE | re.DOTALL
            )
            # General fallback for any remaining AGE(...) in cohort analysis
            adapted = re.sub(
                r"EXTRACT\(YEAR FROM AGE\([\s\S]+?\)\)\s*\*\s*4\s*\+\s*EXTRACT\(MONTH FROM AGE\([\s\S]+?\)\)\s*/\s*3",
                r"(CAST(strftime('%Y', s.sale_date) AS INT) - CAST(strftime('%Y', rc.hire_quarter) AS INT)) * 4 + ((CAST(strftime('%m', s.sale_date) AS INT) - CAST(strftime('%m', rc.hire_quarter) AS INT)) / 3)",
                adapted,
                flags=re.IGNORECASE
            )

        # 3. DATE_TRUNC('month', col)::DATE or DATE_TRUNC('month', col) -> strftime('%Y-%m-01', col)
        adapted = re.sub(
            r"DATE_TRUNC\('month',\s*([a-zA-Z0-9_.]+)\)(?:::DATE)?",
            r"strftime('%Y-%m-01', \1)",
            adapted,
            flags=re.IGNORECASE
        )

        # 4. DATE_TRUNC('quarter', col)::DATE or DATE_TRUNC('quarter', col) -> strftime('%Y-%m-01', col)
        adapted = re.sub(
            r"DATE_TRUNC\('quarter',\s*([a-zA-Z0-9_.]+)\)(?:::DATE)?",
            r"strftime('%Y-%m-01', \1)",
            adapted,
            flags=re.IGNORECASE
        )

        # 5. EXTRACT(YEAR FROM col_or_expr) -> CAST(strftime('%Y', col) AS INT)
        adapted = re.sub(
            r"EXTRACT\(YEAR FROM\s+([a-zA-Z0-9_.]+)\)",
            r"CAST(strftime('%Y', \1) AS INT)",
            adapted,
            flags=re.IGNORECASE
        )

        # 6. EXTRACT(QUARTER FROM col_or_expr) -> ((CAST(strftime('%m', col) AS INT) + 2) / 3)
        adapted = re.sub(
            r"EXTRACT\(QUARTER FROM\s+([a-zA-Z0-9_.]+)\)",
            r"((CAST(strftime('%m', \1) AS INT) + 2) / 3)",
            adapted,
            flags=re.IGNORECASE
        )

        # 7. EXTRACT(MONTH FROM col_or_expr) -> CAST(strftime('%m', col) AS INT)
        adapted = re.sub(
            r"EXTRACT\(MONTH FROM\s+([a-zA-Z0-9_.]+)\)",
            r"CAST(strftime('%m', \1) AS INT)",
            adapted,
            flags=re.IGNORECASE
        )

        # 8. TO_CHAR(col, 'Mon') -> strftime('%b', col)
        adapted = re.sub(
            r"TO_CHAR\(([a-zA-Z0-9_.]+),\s*'Mon'\)",
            r"strftime('%b', \1)",
            adapted,
            flags=re.IGNORECASE
        )

        return adapted

    def _execute_query(self, sql: str, params: dict = None) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame."""
        adapted_sql = self._adapt_sql(sql)
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(text(adapted_sql), conn, params=params)
            return result
        except Exception as e:
            raise RuntimeError(f"Query execution failed ({self.dialect}): {e}") from e

    def _load_sql_file(self, filename: str) -> str:
        """Load a SQL file from the sql/ directory."""
        filepath = SQL_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"SQL file not found: {filepath}")
        return filepath.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Query 1: Revenue Analysis with YoY Growth
    # ------------------------------------------------------------------

    def get_revenue_analysis(self) -> pd.DataFrame:
        """Revenue by territory with year-over-year growth."""
        sql = self._load_sql_file("01_revenue_analysis.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 2: Rep Leaderboard
    # ------------------------------------------------------------------

    def get_rep_leaderboard(self) -> pd.DataFrame:
        """Rank reps by quota attainment % within territory."""
        sql = self._load_sql_file("02_rep_leaderboard.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 3: Physician ABC Segmentation
    # ------------------------------------------------------------------

    def get_physician_abc(self) -> pd.DataFrame:
        """Segment physicians into A/B/C tiers by total prescription value."""
        sql = self._load_sql_file("03_physician_abc.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 4: Product Market Share
    # ------------------------------------------------------------------

    def get_product_share(self) -> pd.DataFrame:
        """Market share of each product within its category."""
        sql = self._load_sql_file("04_product_share.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 5: Running 3-Month Averages
    # ------------------------------------------------------------------

    def get_running_averages(self) -> pd.DataFrame:
        """3-month rolling average sales per rep."""
        sql = self._load_sql_file("05_running_averages.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 6: Cohort Analysis
    # ------------------------------------------------------------------

    def get_cohort_analysis(self) -> pd.DataFrame:
        """Rep performance by hire-quarter cohort."""
        if self.dialect == "sqlite":
            sql = """
            WITH rep_cohorts AS (
                SELECT
                    r.rep_id,
                    r.name AS rep_name,
                    r.hire_date,
                    strftime('%Y-%m-01', r.hire_date) AS hire_quarter,
                    r.target_quota,
                    t.name AS territory_name
                FROM reps r
                JOIN territories t ON r.territory_id = t.territory_id
            ),
            cohort_sales AS (
                SELECT
                    rc.rep_id,
                    rc.rep_name,
                    rc.hire_quarter,
                    rc.target_quota,
                    strftime('%Y-%m-01', s.sale_date) AS sale_quarter,
                    (CAST(strftime('%Y', s.sale_date) AS INT) - CAST(strftime('%Y', rc.hire_quarter) AS INT)) * 4 +
                    ((CAST(strftime('%m', s.sale_date) AS INT) - CAST(strftime('%m', rc.hire_quarter) AS INT)) / 3) AS quarters_since_hire,
                    SUM(s.amount) AS quarterly_sales
                FROM rep_cohorts rc
                JOIN sales s ON rc.rep_id = s.rep_id
                WHERE s.sale_date >= rc.hire_date
                GROUP BY rc.rep_id, rc.rep_name, rc.hire_quarter, rc.target_quota, strftime('%Y-%m-01', s.sale_date)
            )
            SELECT
                hire_quarter,
                quarters_since_hire,
                COUNT(DISTINCT rep_id) AS reps_in_cohort,
                ROUND(AVG(quarterly_sales), 2) AS avg_quarterly_sales,
                ROUND(SUM(quarterly_sales), 2) AS total_cohort_sales,
                ROUND(MIN(quarterly_sales), 2) AS min_sales,
                ROUND(MAX(quarterly_sales), 2) AS max_sales
            FROM cohort_sales
            WHERE quarters_since_hire >= 0
            GROUP BY hire_quarter, quarters_since_hire
            ORDER BY hire_quarter, quarters_since_hire;
            """
            return self._execute_query(sql)
        sql = self._load_sql_file("06_cohort_analysis.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 7: Gap Analysis
    # ------------------------------------------------------------------

    def get_gap_analysis(self) -> pd.DataFrame:
        """Territories and reps below 80% of target."""
        sql = self._load_sql_file("07_gap_analysis.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 8: Cross-Selling Opportunities
    # ------------------------------------------------------------------

    def get_cross_sell(self) -> pd.DataFrame:
        """Physicians buying from 2+ therapeutic categories."""
        sql = self._load_sql_file("08_cross_sell.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 9: Churn Risk Detection
    # ------------------------------------------------------------------

    def get_churn_risk(self) -> pd.DataFrame:
        """Physicians with consecutive months of declining sales."""
        sql = self._load_sql_file("09_churn_risk.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 10: Trend & Volatility
    # ------------------------------------------------------------------

    def get_trend_volatility(self) -> pd.DataFrame:
        """Monthly sales trend with moving average and standard deviation."""
        sql = self._load_sql_file("10_trend_volatility.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # SQL Playground (Raw Query Execution)
    # ------------------------------------------------------------------

    def execute_raw(self, sql: str) -> pd.DataFrame:
        """Execute a raw SQL query from the SQL playground with safety checks."""
        if self._BLOCKED_PATTERNS.search(sql):
            blocked_match = self._BLOCKED_PATTERNS.search(sql).group()
            raise ValueError(
                f"Blocked: '{blocked_match}' operations are not allowed in the SQL Playground. Only SELECT queries are permitted."
            )

        cleaned = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL).strip()

        if not cleaned.upper().startswith(('SELECT', 'WITH')):
            raise ValueError("Only SELECT and WITH (CTE) queries are allowed in the SQL Playground.")

        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Dashboard-Specific Convenience Queries
    # ------------------------------------------------------------------

    def get_kpi_summary(self) -> dict:
        """Get high-level KPIs for the executive summary page."""
        sql = """
        SELECT
            SUM(amount)                                    AS total_revenue,
            COUNT(sale_id)                                 AS total_transactions,
            ROUND(AVG(amount), 2)                          AS avg_deal_size,
            COUNT(DISTINCT rep_id)                         AS active_reps,
            COUNT(DISTINCT physician_id)                   AS active_physicians,
            COUNT(DISTINCT product_id)                     AS products_sold
        FROM sales
        """
        df = self._execute_query(sql)
        return df.iloc[0].to_dict() if not df.empty else {}

    def get_monthly_revenue(self) -> pd.DataFrame:
        """Monthly revenue time series for trend chart."""
        sql = """
        SELECT
            DATE_TRUNC('month', sale_date)::DATE AS month,
            SUM(amount)                          AS revenue,
            COUNT(sale_id)                       AS transactions
        FROM sales
        GROUP BY DATE_TRUNC('month', sale_date)
        ORDER BY month
        """
        return self._execute_query(sql)

    def get_revenue_by_region(self) -> pd.DataFrame:
        """Revenue aggregated by region for bar chart."""
        sql = """
        SELECT
            t.region,
            SUM(s.amount)       AS revenue,
            COUNT(s.sale_id)    AS transactions
        FROM sales s
        JOIN reps r        ON s.rep_id       = r.rep_id
        JOIN territories t ON r.territory_id = t.territory_id
        GROUP BY t.region
        ORDER BY revenue DESC
        """
        return self._execute_query(sql)

    def get_territory_quarterly_heatmap(self) -> pd.DataFrame:
        """Revenue by territory x quarter for heatmap visualization."""
        if self.dialect == "sqlite":
            sql = """
            SELECT
                t.name AS territory,
                CAST(strftime('%Y', s.sale_date) AS INT) || '-Q' ||
                    ((CAST(strftime('%m', s.sale_date) AS INT) + 2) / 3) AS quarter,
                SUM(s.amount) AS revenue
            FROM sales s
            JOIN reps r        ON s.rep_id       = r.rep_id
            JOIN territories t ON r.territory_id = t.territory_id
            GROUP BY t.name, quarter
            ORDER BY quarter, t.name
            """
        else:
            sql = """
            SELECT
                t.name AS territory,
                EXTRACT(YEAR FROM s.sale_date)::INT || '-Q' ||
                    EXTRACT(QUARTER FROM s.sale_date)::INT AS quarter,
                SUM(s.amount) AS revenue
            FROM sales s
            JOIN reps r        ON s.rep_id       = r.rep_id
            JOIN territories t ON r.territory_id = t.territory_id
            GROUP BY t.name,
                     EXTRACT(YEAR FROM s.sale_date),
                     EXTRACT(QUARTER FROM s.sale_date)
            ORDER BY quarter, t.name
            """
        return self._execute_query(sql)

    def get_yoy_growth(self) -> float:
        """Calculate overall YoY growth percentage."""
        sql = """
        WITH yearly AS (
            SELECT
                EXTRACT(YEAR FROM sale_date) AS yr,
                SUM(amount) AS revenue
            FROM sales
            GROUP BY EXTRACT(YEAR FROM sale_date)
            ORDER BY yr
        )
        SELECT
            yr,
            revenue,
            LAG(revenue) OVER (ORDER BY yr) AS prev_revenue,
            ROUND(
                (revenue - LAG(revenue) OVER (ORDER BY yr)) * 100.0 /
                NULLIF(LAG(revenue) OVER (ORDER BY yr), 0), 2
            ) AS yoy_growth_pct
        FROM yearly
        ORDER BY yr DESC
        LIMIT 1
        """
        df = self._execute_query(sql)
        if not df.empty and df.iloc[0]["yoy_growth_pct"] is not None:
            return float(df.iloc[0]["yoy_growth_pct"])
        return 0.0

    def get_monthly_revenue_by_category(self) -> pd.DataFrame:
        """Monthly revenue broken down by product category."""
        sql = """
        SELECT
            DATE_TRUNC('month', s.sale_date)::DATE AS month,
            p.category,
            SUM(s.amount) AS revenue
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY DATE_TRUNC('month', s.sale_date), p.category
        ORDER BY month, p.category
        """
        return self._execute_query(sql)

    def get_product_launch_trajectory(self) -> pd.DataFrame:
        """Monthly sales for each product since launch."""
        sql = """
        SELECT
            p.name AS product_name,
            p.category,
            p.launch_date,
            DATE_TRUNC('month', s.sale_date)::DATE AS month,
            SUM(s.amount) AS revenue,
            SUM(s.quantity) AS units_sold
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.name, p.category, p.launch_date, DATE_TRUNC('month', s.sale_date)
        ORDER BY p.name, month
        """
        return self._execute_query(sql)

    def get_seasonality(self) -> pd.DataFrame:
        """Average revenue by month-of-year for seasonality chart."""
        if self.dialect == "sqlite":
            sql = """
            SELECT
                CAST(strftime('%m', sale_date) AS INT) AS month_num,
                strftime('%m', sale_date) AS month_name,
                ROUND(AVG(daily_rev), 2) AS avg_daily_revenue
            FROM (
                SELECT
                    sale_date,
                    SUM(amount) AS daily_rev
                FROM sales
                GROUP BY sale_date
            ) daily
            GROUP BY month_num, month_name
            ORDER BY month_num
            """
        else:
            sql = """
            SELECT
                EXTRACT(MONTH FROM sale_date)::INT AS month_num,
                TO_CHAR(sale_date, 'Mon') AS month_name,
                ROUND(AVG(daily_rev), 2) AS avg_daily_revenue
            FROM (
                SELECT
                    sale_date,
                    SUM(amount) AS daily_rev
                FROM sales
                GROUP BY sale_date
            ) daily
            GROUP BY EXTRACT(MONTH FROM sale_date), TO_CHAR(sale_date, 'Mon')
            ORDER BY month_num
            """
        return self._execute_query(sql)
