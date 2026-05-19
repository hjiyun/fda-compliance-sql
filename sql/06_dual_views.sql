-- ============================================================
-- 06_dual_views.sql
-- Week 4 Step 5 — 듀얼 VIEW 전환
--   v_compliance_results : 다국가 (US + EU + CODEX, 약 19,767 행)
--   v_compliance_us      : 단일국 US 필터 (Week 3 호환, 6,589 행)
--   v_risk_score         : 다국가 (제품 × 국가, 약 7,479 행)
--   v_risk_score_us      : 단일국 US 필터 (Week 3 호환, 2,493 행)
--
-- 사전 조건: 05_multi_country_migration.sql 적용 완료
--   - nutrients 테이블 (4행)
--   - nutrient_limits PK = (country_code, nutrient_code), 12행
--
-- v_risk_score 의 다국가 의미:
--   - 같은 제품이 국가별로 다른 risk_level 을 가질 수 있음
--   - 예: sodium 420 mg/100g 제품 → US/EU low, CODEX high (Q10 분석 토대)
--   - undiagnosed 제품(366건) 은 국가별 3회 노출됨 (CROSS JOIN 으로 보존)
-- ============================================================

BEGIN;

DROP VIEW IF EXISTS v_risk_score_us       CASCADE;
DROP VIEW IF EXISTS v_compliance_us       CASCADE;
DROP VIEW IF EXISTS v_risk_score          CASCADE;
DROP VIEW IF EXISTS v_compliance_results  CASCADE;

-- ============================================================
-- v_compliance_results : 다국가 진단 (제품 × 영양소 × 국가)
-- ============================================================
CREATE VIEW v_compliance_results AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name        AS category,
    p.category_source,
    pn.nutrient_code,
    n.nutrient_name_kr,
    nl.country_code,
    pn.amount_per_100g     AS value_per_100g,
    nl.daily_value,
    n.unit,
    ROUND(pn.amount_per_100g / nl.daily_value * 100, 2)  AS percent_dv,
    nl.high_threshold_100g,
    CASE
        WHEN pn.amount_per_100g / nl.daily_value * 100 >= 20 THEN 'high'
        WHEN pn.amount_per_100g / nl.daily_value * 100 >= 5  THEN 'moderate'
        ELSE                                                      'low'
    END                    AS judgment
FROM       product_nutrients pn
INNER JOIN products          p  ON p.product_id     = pn.product_id
INNER JOIN nutrients         n  ON n.nutrient_code  = pn.nutrient_code
INNER JOIN nutrient_limits   nl ON nl.nutrient_code = pn.nutrient_code
LEFT JOIN  categories        c  ON c.category_id    = p.category_id;

COMMENT ON VIEW v_compliance_results IS
'다국가 적합성 진단 (제품 × 영양소 × 국가). 6,589 영양소 측정 × 3국 = 19,767 행.';

-- ============================================================
-- v_compliance_us : US 단일국 필터 VIEW (Week 3 호환)
-- ============================================================
CREATE VIEW v_compliance_us AS
SELECT *
FROM v_compliance_results
WHERE country_code = 'US';

COMMENT ON VIEW v_compliance_us IS
'US 진단 결과 (Week 3 v_compliance_results 호환). country_code 컬럼은 항상 ''US''.';

-- ============================================================
-- v_risk_score : 다국가 위험도 (제품 × 국가)
--   - products CROSS JOIN (DISTINCT country_code) 로 undiagnosed 보존
--   - 같은 제품이 국가별로 다른 risk_level 을 가질 수 있음
-- ============================================================
CREATE VIEW v_risk_score AS
WITH country_list AS (
    SELECT DISTINCT country_code FROM nutrient_limits
),
products_x_countries AS (
    SELECT p.product_id, p.product_name, p.category_id, p.category_source,
           cl.country_code
    FROM       products p
    CROSS JOIN country_list cl
),
per_product_country AS (
    SELECT
        pxc.product_id,
        pxc.product_name,
        c.category_name        AS category,
        pxc.category_source,
        pxc.country_code,
        COUNT(vcr.nutrient_code) FILTER (WHERE vcr.judgment = 'high')      AS high_count,
        COUNT(vcr.nutrient_code) FILTER (WHERE vcr.judgment = 'moderate')  AS moderate_count,
        COUNT(vcr.nutrient_code) FILTER (WHERE vcr.judgment = 'low')       AS low_count,
        COUNT(vcr.nutrient_code)                                           AS diagnosed_count
    FROM       products_x_countries pxc
    LEFT JOIN  categories           c   ON c.category_id  = pxc.category_id
    LEFT JOIN  v_compliance_results vcr
            ON vcr.product_id   = pxc.product_id
           AND vcr.country_code = pxc.country_code
    GROUP BY pxc.product_id, pxc.product_name, c.category_name,
             pxc.category_source, pxc.country_code
)
SELECT
    product_id,
    product_name,
    category,
    category_source,
    country_code,
    high_count,
    moderate_count,
    low_count,
    (4 - diagnosed_count)  AS null_count,
    diagnosed_count,
    CASE
        WHEN diagnosed_count = 0   THEN 'undiagnosed'
        WHEN high_count     >= 2   THEN 'high'
        WHEN high_count      = 1
          OR moderate_count >= 2   THEN 'medium'
        ELSE                            'low'
    END                    AS risk_level
FROM per_product_country;

COMMENT ON VIEW v_risk_score IS
'다국가 제품 위험도. 2,493 제품 × 3국 = 7,479 행. 임계값 차이로 같은 제품도 국가별 판정 다를 수 있음.';

-- ============================================================
-- v_risk_score_us : US 단일국 필터 (Week 3 호환)
-- ============================================================
CREATE VIEW v_risk_score_us AS
SELECT *
FROM v_risk_score
WHERE country_code = 'US';

COMMENT ON VIEW v_risk_score_us IS
'US 위험도 (Week 3 v_risk_score 호환). country_code 컬럼은 항상 ''US''.';

COMMIT;

-- ============================================================
-- 검증
-- ============================================================
SELECT 'v_compliance_results' AS view_name, count(*) AS rows FROM v_compliance_results
UNION ALL
SELECT 'v_compliance_us',     count(*) FROM v_compliance_us
UNION ALL
SELECT 'v_risk_score',        count(*) FROM v_risk_score
UNION ALL
SELECT 'v_risk_score_us',     count(*) FROM v_risk_score_us;
