"""
Pharma Sales Analytics — Database Manager & Query Layer
========================================================
Provides a DatabaseManager class that wraps all 10 SQL queries
and returns Pandas DataFrames. Uses SQLAlchemy for connection
pooling and safe query execution.
"""

import os
import re
from pathlib import Path
from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# SQL directory
SQL_DIR = _PROJECT_ROOT / "sql"


class DatabaseManager:
    """
    Central database interface for the Pharma Sales Analytics dashboard.

    Usage:
        db = DatabaseManager()
        df = db.get_revenue_analysis()
        db.close()

    Or as a context manager:
        with DatabaseManager() as db:
            df = db.get_revenue_analysis()
    """

    # Dangerous SQL patterns blocked in the playground
    _BLOCKED_PATTERNS = re.compile(
        r'\b(DROP|DELETE|TRUNCATE|ALTER|INSERT|UPDATE|CREATE|GRANT|REVOKE)\b',
        re.IGNORECASE
    )

    def __init__(self, database_url: str = None):
        """
        Initialize with connection pooling.

        Args:
            database_url: PostgreSQL connection string. Falls back to DATABASE_URL env var.
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://admin:admin123@localhost:5432/pharma_analytics"
        )
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections every 30 minutes
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Dispose of the connection pool."""
        self.engine.dispose()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_query(self, sql: str, params: dict = None) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame."""
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(text(sql), conn, params=params)
            return result
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e

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
        """
        Revenue by territory with year-over-year growth.
        Uses CTE + LAG window function.
        """
        sql = self._load_sql_file("01_revenue_analysis.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 2: Rep Leaderboard
    # ------------------------------------------------------------------

    def get_rep_leaderboard(self) -> pd.DataFrame:
        """
        Rank reps by quota attainment % within territory.
        Uses RANK() + PARTITION BY.
        """
        sql = self._load_sql_file("02_rep_leaderboard.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 3: Physician ABC Segmentation
    # ------------------------------------------------------------------

    def get_physician_abc(self) -> pd.DataFrame:
        """
        Segment physicians into A/B/C tiers by total prescription value.
        Uses NTILE(3).
        """
        sql = self._load_sql_file("03_physician_abc.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 4: Product Market Share
    # ------------------------------------------------------------------

    def get_product_share(self) -> pd.DataFrame:
        """
        Market share of each product within its category.
        Uses subquery + ratio calculation.
        """
        sql = self._load_sql_file("04_product_share.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 5: Running 3-Month Averages
    # ------------------------------------------------------------------

    def get_running_averages(self) -> pd.DataFrame:
        """
        3-month rolling average sales per rep.
        Uses ROWS BETWEEN window frame.
        """
        sql = self._load_sql_file("05_running_averages.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 6: Cohort Analysis
    # ------------------------------------------------------------------

    def get_cohort_analysis(self) -> pd.DataFrame:
        """
        Rep performance by hire-quarter cohort.
        Uses DATE_TRUNC + self-join.
        """
        sql = self._load_sql_file("06_cohort_analysis.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 7: Gap Analysis
    # ------------------------------------------------------------------

    def get_gap_analysis(self) -> pd.DataFrame:
        """
        Territories and reps below 80% of target.
        Uses JOIN + HAVING.
        """
        sql = self._load_sql_file("07_gap_analysis.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 8: Cross-Selling Opportunities
    # ------------------------------------------------------------------

    def get_cross_sell(self) -> pd.DataFrame:
        """
        Physicians buying from 2+ therapeutic categories.
        Uses COUNT DISTINCT + CASE pivot.
        """
        sql = self._load_sql_file("08_cross_sell.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 9: Churn Risk Detection
    # ------------------------------------------------------------------

    def get_churn_risk(self) -> pd.DataFrame:
        """
        Physicians with consecutive months of declining sales.
        Uses LAG + CASE + running comparison.
        """
        sql = self._load_sql_file("09_churn_risk.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # Query 10: Trend & Volatility
    # ------------------------------------------------------------------

    def get_trend_volatility(self) -> pd.DataFrame:
        """
        Monthly sales trend with moving average and standard deviation.
        Uses window functions for moving avg + STDDEV.
        """
        sql = self._load_sql_file("10_trend_volatility.sql")
        return self._execute_query(sql)

    # ------------------------------------------------------------------
    # SQL Playground (Raw Query Execution)
    # ------------------------------------------------------------------

    def execute_raw(self, sql: str) -> pd.DataFrame:
        """
        Execute a raw SQL query from the SQL playground.

        Safety: Blocks destructive operations (DROP, DELETE, ALTER, etc.)
        Only SELECT queries are permitted.

        Args:
            sql: Raw SQL query string.

        Returns:
            DataFrame with query results.

        Raises:
            ValueError: If the query contains blocked keywords.
        """
        # Security check — block destructive operations
        if self._BLOCKED_PATTERNS.search(sql):
            blocked_match = self._BLOCKED_PATTERNS.search(sql).group()
            raise ValueError(
                f"⛔ Blocked: '{blocked_match}' operations are not allowed "
                f"in the SQL Playground. Only SELECT queries are permitted."
            )

        # Additional safety: must start with SELECT or WITH (after whitespace/comments)
        cleaned = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)  # Remove comments
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)  # Remove block comments
        cleaned = cleaned.strip()

        if not cleaned.upper().startswith(('SELECT', 'WITH')):
            raise ValueError(
                "⛔ Only SELECT and WITH (CTE) queries are allowed in the SQL Playground."
            )

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
        """Revenue by territory × quarter for heatmap visualization."""
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
        """Monthly sales for each product since launch — for trajectory chart."""
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
