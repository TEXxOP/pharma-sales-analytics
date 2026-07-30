-- ============================================================
-- Query 1: Revenue by Territory with Year-over-Year Growth
-- ============================================================
-- Business Question: How is each territory performing compared
-- to the previous year? Which territories are growing/declining?
--
-- SQL Techniques: CTE, DATE_TRUNC, SUM aggregation, LAG window function
-- ============================================================

WITH yearly_revenue AS (
    -- Step 1: Aggregate total revenue per territory per year
    SELECT
        t.territory_id,
        t.name            AS territory_name,
        t.region,
        EXTRACT(YEAR FROM s.sale_date)  AS sale_year,
        SUM(s.amount)                   AS total_revenue,
        COUNT(s.sale_id)                AS total_transactions
    FROM sales s
    JOIN reps r    ON s.rep_id       = r.rep_id
    JOIN territories t ON r.territory_id = t.territory_id
    GROUP BY t.territory_id, t.name, t.region, EXTRACT(YEAR FROM s.sale_date)
),
with_growth AS (
    -- Step 2: Calculate YoY growth using LAG to look at the previous year
    SELECT
        territory_id,
        territory_name,
        region,
        sale_year,
        total_revenue,
        total_transactions,
        LAG(total_revenue) OVER (
            PARTITION BY territory_id
            ORDER BY sale_year
        ) AS prev_year_revenue,
        ROUND(
            (total_revenue - LAG(total_revenue) OVER (
                PARTITION BY territory_id ORDER BY sale_year
            )) * 100.0 /
            NULLIF(LAG(total_revenue) OVER (
                PARTITION BY territory_id ORDER BY sale_year
            ), 0),
            2
        ) AS yoy_growth_pct
    FROM yearly_revenue
)

-- Step 3: Final output sorted by year and revenue
SELECT
    territory_name,
    region,
    sale_year,
    total_revenue,
    total_transactions,
    prev_year_revenue,
    COALESCE(yoy_growth_pct, 0) AS yoy_growth_pct
FROM with_growth
ORDER BY sale_year DESC, total_revenue DESC;
