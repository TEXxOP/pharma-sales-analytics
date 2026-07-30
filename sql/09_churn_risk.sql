-- ============================================================
-- Query 9: Churn Risk — Physicians with Declining Sales
-- ============================================================
-- Business Question: Which physicians show a pattern of declining
-- prescription volume? Flag those with 3+ consecutive months
-- of decline as churn risks.
--
-- SQL Techniques: LAG, CASE, running comparison, CTEs
-- ============================================================

WITH monthly_physician_sales AS (
    -- Step 1: Monthly sales per physician
    SELECT
        ph.physician_id,
        ph.name                                     AS physician_name,
        ph.specialty,
        ph.tier,
        t.name                                      AS territory_name,
        DATE_TRUNC('month', s.sale_date)::DATE      AS sale_month,
        SUM(s.amount)                               AS monthly_revenue,
        SUM(s.quantity)                              AS monthly_quantity
    FROM physicians ph
    JOIN territories t ON ph.territory_id = t.territory_id
    JOIN sales s       ON ph.physician_id = s.physician_id
    GROUP BY ph.physician_id, ph.name, ph.specialty, ph.tier,
             t.name, DATE_TRUNC('month', s.sale_date)
),
with_lag AS (
    -- Step 2: Compare each month to the previous month using LAG
    SELECT
        *,
        LAG(monthly_revenue, 1) OVER (
            PARTITION BY physician_id ORDER BY sale_month
        ) AS prev_month_revenue,
        LAG(monthly_revenue, 2) OVER (
            PARTITION BY physician_id ORDER BY sale_month
        ) AS prev_2month_revenue,
        -- Flag if current month is lower than previous
        CASE
            WHEN monthly_revenue < LAG(monthly_revenue, 1) OVER (
                PARTITION BY physician_id ORDER BY sale_month
            ) THEN 1
            ELSE 0
        END AS is_declining
    FROM monthly_physician_sales
),
consecutive_decline AS (
    -- Step 3: Count consecutive months of decline
    SELECT
        *,
        -- Sum of declining flags over a 3-month window
        SUM(is_declining) OVER (
            PARTITION BY physician_id
            ORDER BY sale_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS decline_streak
    FROM with_lag
)

-- Step 4: Flag physicians with 3 consecutive declining months
SELECT
    physician_name,
    specialty,
    tier,
    territory_name,
    sale_month,
    monthly_revenue,
    prev_month_revenue,
    ROUND(
        (monthly_revenue - COALESCE(prev_month_revenue, monthly_revenue)) * 100.0
        / NULLIF(prev_month_revenue, 0), 2
    ) AS mom_change_pct,
    decline_streak,
    CASE
        WHEN decline_streak >= 3 THEN 'HIGH RISK'
        WHEN decline_streak >= 2 THEN 'MODERATE RISK'
        ELSE 'STABLE'
    END AS churn_risk_level
FROM consecutive_decline
WHERE decline_streak >= 2
ORDER BY decline_streak DESC, monthly_revenue DESC;
