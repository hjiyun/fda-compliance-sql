-- ============================================================
-- Q3. CTE 다단계 진단 — 영양소별 판정 → 제품별 집계 → 위험도 분류
--
-- 보고서 4.6절 예시 구조: 3-step CTE
--   1) violation_check : (제품, 영양소) 단위 판정
--   2) risk_summary    : 제품별 high/moderate/low 카운트
--   3) 최종 SELECT     : 위험도 분류 + 분포
-- ============================================================

WITH violation_check AS (
    SELECT
        pn.product_id,
        p.product_name,
        c.category_name                                         AS category,
        p.category_source,
        pn.nutrient_code,
        pn.amount_per_100g,
        nl.daily_value,
        ROUND(pn.amount_per_100g / nl.daily_value * 100, 2)     AS percent_dv,
        CASE
            WHEN pn.amount_per_100g / nl.daily_value * 100 >= 20 THEN 'high'
            WHEN pn.amount_per_100g / nl.daily_value * 100 >= 5  THEN 'moderate'
            ELSE                                                      'low'
        END                                                     AS judgment
    FROM       product_nutrients pn
    INNER JOIN products          p  ON p.product_id     = pn.product_id
    INNER JOIN nutrient_limits   nl ON nl.nutrient_code = pn.nutrient_code
                                    AND nl.country_code  = 'US'
    LEFT JOIN  categories        c  ON c.category_id    = p.category_id
),
risk_summary AS (
    SELECT
        product_id,
        product_name,
        category,
        category_source,
        COUNT(*) FILTER (WHERE judgment = 'high')      AS high_count,
        COUNT(*) FILTER (WHERE judgment = 'moderate')  AS moderate_count,
        COUNT(*) FILTER (WHERE judgment = 'low')       AS low_count,
        COUNT(*)                                       AS diagnosed_count
    FROM violation_check
    GROUP BY product_id, product_name, category, category_source
)
SELECT
    CASE
        WHEN high_count    >= 2  THEN 'high'
        WHEN high_count     = 1
          OR moderate_count >= 2 THEN 'medium'
        ELSE                          'low'
    END                                AS risk_level,
    COUNT(*)                           AS product_n,
    ROUND(COUNT(*)::numeric
          / SUM(COUNT(*)) OVER () * 100, 2)  AS share_pct
FROM risk_summary
GROUP BY risk_level
ORDER BY product_n DESC;
