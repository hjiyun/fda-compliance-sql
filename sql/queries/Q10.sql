-- ============================================================
-- Q10. 동일 제품의 국가별 판정 차이 (Cross-country compliance gap)
--
-- 목적: 같은 (제품, 영양소) 가 3국에서 다른 judgment 를 받는 케이스 식별.
--   - 다국가 인프라(v_compliance_results) 의 핵심 활용
--   - 임계값 차이가 실제 진단에 미치는 영향 정량화
--   - 핵심 패턴: "FDA(US) 적합 → CODEX 위반"
--
-- 임계값 차이 (100g):
--   sodium       : US 460 / EU 480 / CODEX 400 → US·EU·CODEX 모두 다름
--   saturated_fat: US 4   / EU 4   / CODEX 4   → 동일
--   sugars       : US 10  / EU 18  / CODEX 10  → EU 가 외형상 느슨 (※ surrogate 비교)
--   energy       : US 400 / EU 400 / CODEX 400 → 동일
--
-- 예상: sodium / sugars 에서만 판정 차이 발생. sat_fat·energy 는 임계값 동일 → 차이 없음.
-- ============================================================

-- 10-A. 영양소별 판정 차이 빈도 (전체 측정 대비)
WITH per_country AS (
    SELECT
        product_id,
        nutrient_code,
        MAX(CASE WHEN country_code = 'US'    THEN judgment END) AS us_j,
        MAX(CASE WHEN country_code = 'EU'    THEN judgment END) AS eu_j,
        MAX(CASE WHEN country_code = 'CODEX' THEN judgment END) AS codex_j
    FROM v_compliance_results
    GROUP BY product_id, nutrient_code
)
SELECT
    nutrient_code,
    COUNT(*)                                             AS total_measured,
    COUNT(*) FILTER (WHERE us_j    != codex_j)           AS us_codex_diff,
    COUNT(*) FILTER (WHERE us_j    != eu_j)              AS us_eu_diff,
    COUNT(*) FILTER (WHERE eu_j    != codex_j)           AS eu_codex_diff,
    COUNT(*) FILTER (WHERE us_j != eu_j
                       OR eu_j != codex_j
                       OR us_j != codex_j)               AS any_diff,
    ROUND(100.0 * COUNT(*) FILTER (WHERE us_j != eu_j
                                      OR eu_j != codex_j
                                      OR us_j != codex_j)
          / NULLIF(COUNT(*), 0), 2)                      AS any_diff_pct
FROM per_country
GROUP BY nutrient_code
ORDER BY any_diff DESC;


-- 10-B. "FDA(US) 적합 → CODEX 위반" 핵심 패턴 (영양소별)
WITH per_country AS (
    SELECT
        product_id,
        nutrient_code,
        MAX(CASE WHEN country_code = 'US'    THEN judgment END) AS us_j,
        MAX(CASE WHEN country_code = 'CODEX' THEN judgment END) AS codex_j
    FROM v_compliance_results
    GROUP BY product_id, nutrient_code
)
SELECT
    nutrient_code,
    COUNT(*) FILTER (WHERE us_j != 'high' AND codex_j  = 'high') AS us_ok_codex_high,
    COUNT(*) FILTER (WHERE us_j  = 'high' AND codex_j != 'high') AS us_high_codex_ok,
    COUNT(*) FILTER (WHERE us_j  = 'high' AND codex_j  = 'high') AS both_high,
    COUNT(*) FILTER (WHERE us_j != 'high' AND codex_j != 'high') AS both_ok
FROM per_country
GROUP BY nutrient_code
ORDER BY nutrient_code;


-- 10-C. 판정 차이 케이스 — 대표 제품 (sodium 만 출력, value_per_100g 가까운 경계 우선)
WITH per_country AS (
    SELECT
        product_id,
        product_name,
        category,
        nutrient_code,
        value_per_100g,
        MAX(CASE WHEN country_code = 'US'    THEN judgment END)   AS us_j,
        MAX(CASE WHEN country_code = 'EU'    THEN judgment END)   AS eu_j,
        MAX(CASE WHEN country_code = 'CODEX' THEN judgment END)   AS codex_j,
        MAX(CASE WHEN country_code = 'US'    THEN percent_dv END) AS us_pdv,
        MAX(CASE WHEN country_code = 'EU'    THEN percent_dv END) AS eu_pdv,
        MAX(CASE WHEN country_code = 'CODEX' THEN percent_dv END) AS codex_pdv
    FROM v_compliance_results
    GROUP BY product_id, product_name, category, nutrient_code, value_per_100g
)
SELECT
    nutrient_code,
    product_name,
    category,
    value_per_100g,
    us_j, eu_j, codex_j,
    us_pdv, eu_pdv, codex_pdv
FROM per_country
WHERE us_j != eu_j OR eu_j != codex_j OR us_j != codex_j
ORDER BY nutrient_code, value_per_100g;
