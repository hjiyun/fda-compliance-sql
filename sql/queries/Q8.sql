-- ============================================================
-- Q8. 가설 검증 — category_source 신뢰도와 위반(high) 비율의 관계
--
-- Week 2 발견 3: "카테고리 미분류(Other) 그룹에 sodium 위험 집중"
--   (mean 528 mg/100g > FDA 임계 460)
--
-- Q8 가설:
--   H1) Other 그룹은 4개 영양소 모두에서 위반율이 Trusted 그룹보다 유의하게 높다.
--   H2) Inferred(name) 그룹은 Trusted 그룹과 유사하다.
--
-- 그룹 정의:
--   Trusted  : category_source IN ('tags', 'top')           — 메타데이터 기반
--   Inferred : category_source = 'name'                     — product_name 키워드 추론
--   Other    : category_source = 'other'                    — 매핑 실패
--
-- 출력: 3 group × 4 nutrient = 12 rows
--   group_name, nutrient_code, total_n, high_count, violation_rate
-- ============================================================

WITH grouped AS (
    SELECT
        CASE
            WHEN p.category_source IN ('tags', 'top') THEN 'Trusted'
            WHEN p.category_source = 'name'           THEN 'Inferred'
            WHEN p.category_source = 'other'          THEN 'Other'
        END                                            AS group_name,
        vcr.nutrient_code,
        vcr.judgment
    FROM       v_compliance_results vcr
    INNER JOIN products             p ON p.product_id = vcr.product_id
)
SELECT
    group_name,
    nutrient_code,
    COUNT(*)                                                AS total_n,
    COUNT(*) FILTER (WHERE judgment = 'high')               AS high_count,
    ROUND(COUNT(*) FILTER (WHERE judgment = 'high')::numeric
          / NULLIF(COUNT(*), 0) * 100, 2)                   AS violation_rate
FROM grouped
GROUP BY group_name, nutrient_code
ORDER BY nutrient_code,
         CASE
            WHEN group_name = 'Trusted'  THEN 1
            WHEN group_name = 'Inferred' THEN 2
            WHEN group_name = 'Other'    THEN 3
         END;
