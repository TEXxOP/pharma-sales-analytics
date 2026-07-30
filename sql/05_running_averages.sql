-- ============================================================
-- Query 5: Running 3-Month Average Sales per Rep
-- ============================================================
-- Business Question: What is the sales trend for each rep
-- over time? Smooth out noise with a 3-month rolling average.
--
-- SQL Techniques: Window function with ROWS BETWEEN, DATE_TRUNC
-- ============================================================

WITH monthly_sales AS (
    -- Step 1: Aggregate sales per rep per month
    SELECT
        r.rep_id,
        r.name              AS rep_name,
        t.name              AS territory_name,
        DATE_TRUNC('month', s.sale_date)::DATE AS sale_month,
        SUM(s.amount)       AS monthly_revenue,
        COUNT(s.sale_id)    AS monthly_deals
    FROM sales s
    JOIN reps r        ON s.rep_id       = r.rep_id
    JOIN territories t ON r.territory_id = t.territory_id
    GROUP BY r.rep_id, r.name, t.name, DATE_TRUNC('month', s.sale_date)
)

-- Step 2: Calculate 3-month rolling average using ROWS BETWEEN
SELECT
    rep_name,
    territory_name,
    sale_month,
    monthly_revenue,
    monthly_deals,
    -- 3-month rolling average (current + 2 preceding months)
    ROUND(
        AVG(monthly_revenue) OVER (
            PARTITION BY rep_id
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_3m_avg_revenue,
    -- 3-month rolling total
    SUM(monthly_revenue) OVER (
        PARTITION BY rep_id
        ORDER BY sale_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3m_total,
    -- Cumulative running total
    SUM(monthly_revenue) OVER (
        PARTITION BY rep_id
        ORDER BY sale_month
        ROWS UNBOUNDED PRECEDING
    ) AS cumulative_revenue
FROM monthly_sales
ORDER BY rep_name, sale_month;
