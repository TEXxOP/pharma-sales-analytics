-- ============================================================
-- Query 3: Physician ABC Segmentation
-- ============================================================
-- Business Question: How should we segment physicians by their
-- total prescription value? Who are our most valuable doctors?
--
-- SQL Techniques: NTILE(3) window function, CASE, aggregation
-- ============================================================

WITH physician_value AS (
    -- Step 1: Calculate total value and frequency per physician
    SELECT
        p.physician_id,
        p.name               AS physician_name,
        p.specialty,
        p.tier               AS current_tier,
        p.hospital_affiliation,
        t.name               AS territory_name,
        SUM(s.amount)        AS total_value,
        COUNT(s.sale_id)     AS total_transactions,
        AVG(s.amount)        AS avg_deal_size,
        COUNT(DISTINCT s.product_id) AS products_purchased
    FROM physicians p
    JOIN territories t ON p.territory_id = t.territory_id
    LEFT JOIN sales s  ON p.physician_id = s.physician_id
    GROUP BY p.physician_id, p.name, p.specialty, p.tier,
             p.hospital_affiliation, t.name
),
segmented AS (
    -- Step 2: Use NTILE to divide physicians into 3 equal segments
    -- NTILE(3) assigns 1 = Top third, 2 = Middle, 3 = Bottom
    SELECT
        *,
        NTILE(3) OVER (ORDER BY total_value DESC) AS value_segment
    FROM physician_value
    WHERE total_value IS NOT NULL AND total_value > 0
)

SELECT
    physician_name,
    specialty,
    current_tier,
    hospital_affiliation,
    territory_name,
    total_value,
    total_transactions,
    ROUND(avg_deal_size, 2) AS avg_deal_size,
    products_purchased,
    -- Map NTILE segment to ABC label
    CASE value_segment
        WHEN 1 THEN 'A - High Value'
        WHEN 2 THEN 'B - Medium Value'
        WHEN 3 THEN 'C - Low Value'
    END AS abc_segment,
    value_segment
FROM segmented
ORDER BY total_value DESC;
