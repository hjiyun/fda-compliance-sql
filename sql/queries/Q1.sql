-- ============================================================
-- Q1. 영양소별 / 카테고리별 기준 초과(high) 분포
--
-- 목적: 4개 영양소 각각의 high 판정 건수와, 카테고리별 분포를 한 번에 확인.
-- 분모: 진단된 (제품, 영양소) 쌍 (NULL 제외, v_compliance_results 행)
-- ============================================================

-- 1-A. 영양소별 전체 high 분포
SELECT
    nutrient_code,
    nutrient_name_kr,
    COUNT(*) FILTER (WHERE judgment = 'high')      AS high_n,
    COUNT(*)                                       AS diagnosed_n,
    ROUND(
        COUNT(*) FILTER (WHERE judgment = 'high')::numeric
        / NULLIF(COUNT(*), 0) * 100, 2)            AS high_pct
FROM v_compliance_results
GROUP BY nutrient_code, nutrient_name_kr
ORDER BY high_pct DESC;

-- 1-B. 카테고리 × 영양소 high 분포 (Other 포함)
SELECT
    COALESCE(category, '(Other)')                  AS category,
    nutrient_code,
    COUNT(*) FILTER (WHERE judgment = 'high')      AS high_n,
    COUNT(*)                                       AS diagnosed_n,
    ROUND(
        COUNT(*) FILTER (WHERE judgment = 'high')::numeric
        / NULLIF(COUNT(*), 0) * 100, 2)            AS high_pct
FROM v_compliance_results
GROUP BY category, nutrient_code
ORDER BY category, nutrient_code;
