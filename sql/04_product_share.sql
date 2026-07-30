-- ============================================================
-- Query 4: Product Market Share by Category
-- ============================================================
-- Business Question: What is each product's share within its
-- therapeutic category? Which drugs dominate their segment?
--
-- SQL Techniques: Subquery, ratio calculation, aggregation
-- ============================================================

WITH product_revenue AS (
    -- Step 1: Total revenue per product
    SELECT
        p.product_id,
        p.name              AS product_name,
        p.category,
        p.price_per_unit,
        p.launch_date,
        SUM(s.amount)       AS product_revenue,
        SUM(s.quantity)      AS total_units_sold,
        COUNT(s.sale_id)     AS total_transactions
    FROM products p
    LEFT JOIN sales s ON p.product_id = s.product_id
    GROUP BY p.product_id, p.name, p.category, p.price_per_unit, p.launch_date
),
category_totals AS (
    -- Step 2: Total revenue per category (used as denominator)
    SELECT
        category,
        SUM(product_revenue) AS category_revenue
    FROM product_revenue
    GROUP BY category
)

-- Step 3: Calculate market share as product revenue / category revenue
SELECT
    pr.product_name,
    pr.category,
    pr.price_per_unit,
    pr.launch_date,
    pr.product_revenue,
    pr.total_units_sold,
    pr.total_transactions,
    ct.category_revenue,
    ROUND(
        pr.product_revenue * 100.0 / NULLIF(ct.category_revenue, 0), 2
    ) AS market_share_pct,
    -- Rank within category
    RANK() OVER (
        PARTITION BY pr.category
        ORDER BY pr.product_revenue DESC
    ) AS category_rank
FROM product_revenue pr
JOIN category_totals ct ON pr.category = ct.category
ORDER BY pr.category, market_share_pct DESC;
