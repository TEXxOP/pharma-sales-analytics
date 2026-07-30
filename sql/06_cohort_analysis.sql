-- ============================================================
-- Query 6: Cohort Analysis — Rep Performance by Hire Quarter
-- ============================================================
-- Business Question: Do reps hired in certain quarters perform
-- better? How long does it take new reps to ramp up?
--
-- SQL Techniques: DATE_TRUNC, self-join, cohort grouping
-- ============================================================

WITH rep_cohorts AS (
    -- Step 1: Assign each rep to a hire-quarter cohort
    SELECT
        r.rep_id,
        r.name                                        AS rep_name,
        r.hire_date,
        DATE_TRUNC('quarter', r.hire_date)::DATE      AS hire_quarter,
        r.target_quota,
        t.name                                        AS territory_name
    FROM reps r
    JOIN territories t ON r.territory_id = t.territory_id
),
cohort_sales AS (
    -- Step 2: Calculate each rep's sales per quarter since hire
    SELECT
        rc.rep_id,
        rc.rep_name,
        rc.hire_quarter,
        rc.target_quota,
        DATE_TRUNC('quarter', s.sale_date)::DATE      AS sale_quarter,
        -- "Quarters since hire" = how many quarters after joining
        EXTRACT(YEAR FROM AGE(
            DATE_TRUNC('quarter', s.sale_date),
            rc.hire_quarter
        )) * 4 +
        EXTRACT(MONTH FROM AGE(
            DATE_TRUNC('quarter', s.sale_date),
            rc.hire_quarter
        )) / 3                                        AS quarters_since_hire,
        SUM(s.amount)                                 AS quarterly_sales
    FROM rep_cohorts rc
    JOIN sales s ON rc.rep_id = s.rep_id
    WHERE s.sale_date >= rc.hire_date  -- Only count sales after hire
    GROUP BY rc.rep_id, rc.rep_name, rc.hire_quarter,
             rc.target_quota, DATE_TRUNC('quarter', s.sale_date)
)

-- Step 3: Aggregate by cohort to see average ramp-up
SELECT
    hire_quarter,
    quarters_since_hire,
    COUNT(DISTINCT rep_id)              AS reps_in_cohort,
    ROUND(AVG(quarterly_sales), 2)     AS avg_quarterly_sales,
    ROUND(SUM(quarterly_sales), 2)     AS total_cohort_sales,
    ROUND(MIN(quarterly_sales), 2)     AS min_sales,
    ROUND(MAX(quarterly_sales), 2)     AS max_sales
FROM cohort_sales
WHERE quarters_since_hire >= 0
GROUP BY hire_quarter, quarters_since_hire
ORDER BY hire_quarter, quarters_since_hire;
