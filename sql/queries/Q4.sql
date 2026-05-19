-- ============================================================
-- Q4. 카테고리 내 영양소 함량 순위 (RANK 윈도우 함수)
--
-- 각 카테고리 × 영양소 조합에서 상위 5개 제품을 추출.
-- Other 그룹은 제외 (메타데이터 부재로 진정한 '카테고리 비교'가 아님).
-- ============================================================

WITH ranked AS (
    SELECT
        category,
        nutrient_code,
        product_id,
        product_name,
        value_per_100g,
        percent_dv,
        judgment,
        RANK() OVER (
            PARTITION BY category, nutrient_code
            ORDER BY     value_per_100g DESC
        )                                       AS rk
    FROM v_compliance_us
    WHERE category IS NOT NULL
      AND category != 'Other'
)
SELECT
    category,
    nutrient_code,
    rk,
    product_name,
    value_per_100g,
    percent_dv,
    judgment
FROM ranked
WHERE rk <= 5
ORDER BY category, nutrient_code, rk;
