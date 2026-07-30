-- ============================================================
-- Query 7: Gap Analysis — Territories & Reps Below Target
-- ============================================================
-- Business Question: Which territories and reps are falling
-- below 80% of their sales target? Where do we need intervention?
--
-- SQL Techniques: JOIN, HAVING, aggregation, CASE
-- ============================================================

-- Part A: Territory-level gap analysis
WITH territory_performance AS (
    SELECT
        t.territory_id,
        t.name                AS territory_name,
        t.region,
        t.manager,
        SUM(r.target_quota)   AS territory_quota,
        SUM(s.amount)         AS territory_sales,
        COUNT(DISTINCT r.rep_id) AS rep_count
    FROM territories t
    JOIN reps r    ON t.territory_id = r.territory_id
    JOIN sales s   ON r.rep_id       = s.rep_id
    GROUP BY t.territory_id, t.name, t.region, t.manager
    -- HAVING filters to only territories below 80% attainment
    HAVING SUM(s.amount) < SUM(r.target_quota) * 0.80
)

SELECT
    territory_name,
    region,
    manager,
    rep_count,
    territory_quota,
    territory_sales,
    ROUND(territory_sales * 100.0 / NULLIF(territory_quota, 0), 2) AS attainment_pct,
    territory_quota - territory_sales AS revenue_gap,
    CASE
        WHEN territory_sales < territory_quota * 0.5 THEN 'CRITICAL'
        WHEN territory_sales < territory_quota * 0.7 THEN 'AT RISK'
        ELSE 'WATCH'
    END AS risk_level
FROM territory_performance
ORDER BY attainment_pct ASC;
