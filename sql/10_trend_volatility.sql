-- ============================================================
-- Query 10: Sales Trend with Moving Average & Volatility
-- ============================================================
-- Business Question: What is the overall sales trend? How stable
-- are monthly revenues? Identify periods of high volatility.
--
-- SQL Techniques: Window functions, STDDEV, moving average
-- ============================================================

WITH monthly_totals AS (
    -- Step 1: Aggregate total monthly sales across all reps
    SELECT
        DATE_TRUNC('month', s.sale_date)::DATE  AS sale_month,
        SUM(s.amount)                           AS monthly_revenue,
        COUNT(s.sale_id)                        AS monthly_transactions,
        COUNT(DISTINCT s.rep_id)                AS active_reps,
        AVG(s.amount)                           AS avg_deal_size
    FROM sales s
    GROUP BY DATE_TRUNC('month', s.sale_date)
)

SELECT
    sale_month,
    monthly_revenue,
    monthly_transactions,
    active_reps,
    ROUND(avg_deal_size, 2) AS avg_deal_size,

    -- 3-month moving average
    ROUND(
        AVG(monthly_revenue) OVER (
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS moving_avg_3m,

    -- 3-month moving standard deviation (volatility)
    ROUND(
        STDDEV(monthly_revenue) OVER (
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS moving_stddev_3m,

    -- Month-over-month change
    monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY sale_month)
        AS mom_change,

    -- Month-over-month change percentage
    ROUND(
        (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY sale_month))
        * 100.0 / NULLIF(LAG(monthly_revenue) OVER (ORDER BY sale_month), 0),
        2
    ) AS mom_change_pct,

    -- Classify volatility
    CASE
        WHEN STDDEV(monthly_revenue) OVER (
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) > AVG(monthly_revenue) OVER (
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) * 0.15 THEN 'HIGH VOLATILITY'
        WHEN STDDEV(monthly_revenue) OVER (
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) > AVG(monthly_revenue) OVER (
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) * 0.08 THEN 'MODERATE'
        ELSE 'STABLE'
    END AS volatility_level

FROM monthly_totals
ORDER BY sale_month;
