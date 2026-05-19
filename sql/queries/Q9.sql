-- ============================================================
-- Q9. 다국가 × 신뢰 그룹 × 영양소 위반률 비교 (Q8 의 다국가 확장)
--
-- 목적: Q8 ("Other 그룹 sodium 위험 집중") 의 가설 검증을 3국으로 확장.
--   - 4 영양소 × 3 국가 (US/EU/CODEX) × 3 그룹 (Trusted/Inferred/Other) = 36 셀
--   - Q8 의 US 결과는 Q9 의 country_code='US' 슬라이스와 일치해야 함 (회귀 보장)
--
-- 그룹 정의 (Q8 과 동일):
--   Trusted  : category_source IN ('tags', 'top')   — 메타데이터 기반
--   Inferred : category_source = 'name'             — product_name 키워드 추론
--   Other    : category_source = 'other'            — 매핑 실패
--
-- Sugars 주의:
--   OFF 원본의 sugars 는 total sugars 기준. US=added, CODEX=free 와는 정의 차이가 있어
--   sugars 의 cross-country 비교는 "surrogate" 비교임을 해석에 명시할 것.
-- ============================================================

WITH grouped AS (
    SELECT
        vcr.country_code,
        vcr.nutrient_code,
        CASE
            WHEN vcr.category_source IN ('tags', 'top') THEN 'Trusted'
            WHEN vcr.category_source = 'name'           THEN 'Inferred'
            WHEN vcr.category_source = 'other'          THEN 'Other'
        END                                                AS group_name,
        vcr.judgment
    FROM v_compliance_results vcr
)
SELECT
    country_code,
    nutrient_code,
    group_name,
    COUNT(*)                                                AS total_n,
    COUNT(*) FILTER (WHERE judgment = 'high')               AS high_count,
    ROUND(COUNT(*) FILTER (WHERE judgment = 'high')::numeric
          / NULLIF(COUNT(*), 0) * 100, 2)                   AS violation_rate
FROM grouped
GROUP BY country_code, nutrient_code, group_name
ORDER BY country_code, nutrient_code,
         CASE group_name
             WHEN 'Trusted'  THEN 1
             WHEN 'Inferred' THEN 2
             WHEN 'Other'    THEN 3
         END;
