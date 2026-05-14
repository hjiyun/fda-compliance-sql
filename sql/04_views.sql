-- ============================================================
-- 04_views.sql
-- 표준학개론 2차 프로젝트: 적합성 진단 VIEW 2종
--   v_compliance_results : 제품 × 영양소 단위 진단 (low / moderate / high)
--   v_risk_score         : 제품별 종합 위험도 (high / medium / low / undiagnosed)
--
-- 진단 임계값 (FDA Daily Value 기준 3단계):
--   percent_dv  = amount_per_100g / daily_value * 100
--     - low      : percent_dv < 5
--     - moderate : 5 <= percent_dv < 20
--     - high     : percent_dv >= 20  (= 100g당 DV의 20% 이상, 'high in' 표시 기준)
--
-- NULL 정책:
--   product_nutrients 에 행이 없는 (제품, 영양소) 쌍은 진단 결과에서 제외.
--   ETL 시점에 결측을 NULL 로 보존했으므로 phantom 0 위양성 적합 회피됨.
-- ============================================================

DROP VIEW IF EXISTS v_risk_score          CASCADE;
DROP VIEW IF EXISTS v_compliance_results  CASCADE;

-- ============================================================
-- v_compliance_results : 제품 × 영양소 단위 진단
-- ============================================================
CREATE VIEW v_compliance_results AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name        AS category,
    p.category_source,
    pn.nutrient_code,
    nl.nutrient_name_kr,
    pn.amount_per_100g     AS value_per_100g,
    nl.daily_value,
    nl.unit,
    ROUND(pn.amount_per_100g / nl.daily_value * 100, 2)  AS percent_dv,
    nl.high_threshold_100g,
    CASE
        WHEN pn.amount_per_100g / nl.daily_value * 100 >= 20 THEN 'high'
        WHEN pn.amount_per_100g / nl.daily_value * 100 >= 5  THEN 'moderate'
        ELSE                                                      'low'
    END                    AS judgment
FROM       product_nutrients pn
INNER JOIN products          p  ON p.product_id     = pn.product_id
INNER JOIN nutrient_limits   nl ON nl.nutrient_code = pn.nutrient_code
LEFT JOIN  categories        c  ON c.category_id    = p.category_id;

COMMENT ON VIEW v_compliance_results IS
'제품 × 영양소 단위 적합성 진단 결과. NULL 영양소는 행이 생성되지 않음 (위양성 적합 회피).';

-- ============================================================
-- v_risk_score : 제품별 종합 위험도
--   - 4개 영양소 중 진단 가능한 것만 집계
--   - undiagnosed : product_nutrients 에 단 한 행도 없는 제품 (= 4개 모두 NULL)
-- ============================================================
CREATE VIEW v_risk_score AS
WITH per_product AS (
    SELECT
        p.product_id,
        p.product_name,
        c.category_name        AS category,
        p.category_source,
        COUNT(vcr.nutrient_code) FILTER (WHERE vcr.judgment = 'high')      AS high_count,
        COUNT(vcr.nutrient_code) FILTER (WHERE vcr.judgment = 'moderate')  AS moderate_count,
        COUNT(vcr.nutrient_code) FILTER (WHERE vcr.judgment = 'low')       AS low_count,
        COUNT(vcr.nutrient_code)                                           AS diagnosed_count
    FROM       products             p
    LEFT JOIN  categories           c   ON c.category_id  = p.category_id
    LEFT JOIN  v_compliance_results vcr ON vcr.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, c.category_name, p.category_source
)
SELECT
    product_id,
    product_name,
    category,
    category_source,
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
FROM per_product;

COMMENT ON VIEW v_risk_score IS
'제품별 종합 위험도. risk_level: high (high_count>=2) / medium (high=1 OR mod>=2) / low / undiagnosed.';

SELECT '✅ 04_views.sql 실행 완료 - VIEW 2개 생성 (v_compliance_results, v_risk_score)' AS message;
