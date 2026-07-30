-- ============================================================
-- Query 2: Rep Leaderboard — Rank by Quota Attainment %
-- ============================================================
-- Business Question: Who are the top-performing reps in each
-- territory? How do they rank against their quota targets?
--
-- SQL Techniques: RANK(), PARTITION BY, CASE, aggregation
-- ============================================================

WITH rep_performance AS (
    -- Step 1: Calculate total sales and quota attainment per rep
    SELECT
        r.rep_id,
        r.name                  AS rep_name,
        t.name                  AS territory_name,
        t.region,
        r.target_quota,
        r.hire_date,
        SUM(s.amount)           AS total_sales,
        COUNT(s.sale_id)        AS total_deals,
        ROUND(
            SUM(s.amount) * 100.0 / NULLIF(r.target_quota, 0), 2
        )                       AS quota_attainment_pct
    FROM reps r
    JOIN territories t ON r.territory_id = t.territory_id
    LEFT JOIN sales s  ON r.rep_id       = s.rep_id
    GROUP BY r.rep_id, r.name, t.name, t.region, r.target_quota, r.hire_date
),
ranked AS (
    -- Step 2: Rank reps within their territory by quota attainment
    SELECT
        *,
        RANK() OVER (
            PARTITION BY territory_name
            ORDER BY quota_attainment_pct DESC
        ) AS territory_rank,
        RANK() OVER (
            ORDER BY quota_attainment_pct DESC
        ) AS overall_rank,
        -- Performance classification
        CASE
            WHEN quota_attainment_pct >= 120 THEN 'Star Performer'
            WHEN quota_attainment_pct >= 100 THEN 'On Target'
            WHEN quota_attainment_pct >= 80  THEN 'Near Target'
            ELSE 'Below Target'
        END AS performance_tier
    FROM rep_performance
)

SELECT
    rep_name,
    territory_name,
    region,
    hire_date,
    total_sales,
    total_deals,
    target_quota,
    quota_attainment_pct,
    territory_rank,
    overall_rank,
    performance_tier
FROM ranked
ORDER BY overall_rank;
