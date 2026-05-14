-- ============================================================
-- Q6. 제품당 high(위반) 영양소 개수 분포
--
-- 한 제품에서 high 판정을 받은 영양소가 0~4개 중 몇 개인지의 분포.
-- undiagnosed (모든 영양소 NULL) 는 high_count=0 이지만 별도 표시.
-- ============================================================

WITH bucketed AS (
    SELECT
        CASE
            WHEN diagnosed_count = 0 THEN 0   -- undiagnosed
            ELSE high_count + 1               -- 0→1, 1→2, ... 4→5
        END                                   AS bucket_order,
        CASE
            WHEN diagnosed_count = 0 THEN 'undiagnosed (no data)'
            WHEN high_count = 0      THEN '0 violations'
            WHEN high_count = 1      THEN '1 violation'
            WHEN high_count = 2      THEN '2 violations'
            WHEN high_count = 3      THEN '3 violations'
            WHEN high_count = 4      THEN '4 violations (all)'
        END                                   AS bucket
    FROM v_risk_score
)
SELECT
    bucket,
    COUNT(*)                                            AS product_n,
    ROUND(COUNT(*)::numeric
          / SUM(COUNT(*)) OVER () * 100, 2)             AS share_pct
FROM bucketed
GROUP BY bucket, bucket_order
ORDER BY bucket_order;
