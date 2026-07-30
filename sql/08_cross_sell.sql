-- ============================================================
-- Query 8: Cross-Selling — Physicians Buying Multiple Categories
-- ============================================================
-- Business Question: Which physicians purchase from 2+ different
-- therapeutic categories? These are cross-sell opportunities.
--
-- SQL Techniques: COUNT DISTINCT, CASE pivot, aggregation
-- ============================================================

WITH physician_categories AS (
    -- Step 1: Count distinct categories per physician
    SELECT
        ph.physician_id,
        ph.name                         AS physician_name,
        ph.specialty,
        ph.tier,
        ph.hospital_affiliation,
        t.name                          AS territory_name,
        COUNT(DISTINCT p.category)      AS categories_purchased,
        SUM(s.amount)                   AS total_spend,
        COUNT(s.sale_id)                AS total_orders,
        -- Pivot: revenue by category using CASE
        SUM(CASE WHEN p.category = 'Cardiology' THEN s.amount ELSE 0 END) AS cardiology_revenue,
        SUM(CASE WHEN p.category = 'Oncology'   THEN s.amount ELSE 0 END) AS oncology_revenue,
        SUM(CASE WHEN p.category = 'Neurology'  THEN s.amount ELSE 0 END) AS neurology_revenue
    FROM physicians ph
    JOIN territories t ON ph.territory_id = t.territory_id
    JOIN sales s       ON ph.physician_id  = s.physician_id
    JOIN products p    ON s.product_id     = p.product_id
    GROUP BY ph.physician_id, ph.name, ph.specialty, ph.tier,
             ph.hospital_affiliation, t.name
)

SELECT
    physician_name,
    specialty,
    tier,
    hospital_affiliation,
    territory_name,
    categories_purchased,
    total_spend,
    total_orders,
    cardiology_revenue,
    oncology_revenue,
    neurology_revenue,
    -- Cross-sell opportunity: physicians buying only 1-2 categories
    CASE
        WHEN categories_purchased = 3 THEN 'Full Portfolio'
        WHEN categories_purchased = 2 THEN 'Cross-Sell: Add 1 Category'
        ELSE 'Cross-Sell: High Potential'
    END AS cross_sell_status
FROM physician_categories
WHERE categories_purchased >= 2
ORDER BY total_spend DESC;
