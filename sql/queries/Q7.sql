-- ============================================================
-- Q7. NULL 탐지 — 영양소별 결측 비율 + undiagnosed 제품 식별
--
-- Week 2 발견 재확인:
--   - OFF 원본의 본질적 한계 (NULL: energy 15% / sugars 33% / sat_fat 40% / sodium 47%)
--   - phantom 0 회피를 위해 NULL 보존 정책 유지
-- ============================================================

-- 7-A. 영양소별 결측 비율 (전체 2,493 제품 대비)
--   nutrient_name_kr 가 마이그레이션 시 nutrient_limits 에서 nutrients 로 이동했으므로
--   driver 테이블을 nutrients 로 교체. nutrient_limits 자체는 결측 계산에 불필요.
SELECT
    n.nutrient_code,
    n.nutrient_name_kr,
    COUNT(pn.product_id)                                 AS present_n,
    2493 - COUNT(pn.product_id)                          AS null_n,
    ROUND((2493 - COUNT(pn.product_id))::numeric
          / 2493 * 100, 2)                               AS null_pct
FROM       nutrients         n
LEFT JOIN  product_nutrients pn ON pn.nutrient_code = n.nutrient_code
GROUP BY n.nutrient_code, n.nutrient_name_kr
ORDER BY null_pct;

-- 7-B. 제품별 가용 영양소 수 분포 (COALESCE / FILTER)
SELECT
    diagnosed_count                                      AS available_nutrients,
    null_count                                           AS null_nutrients,
    COUNT(*)                                             AS product_n,
    ROUND(COUNT(*)::numeric
          / SUM(COUNT(*)) OVER () * 100, 2)              AS share_pct
FROM v_risk_score_us
GROUP BY diagnosed_count, null_count
ORDER BY diagnosed_count DESC;

-- 7-C. undiagnosed 제품 (4개 영양소 모두 NULL) 카테고리 출처별 분포
SELECT
    COALESCE(category, '(NULL)')                         AS category,
    category_source,
    COUNT(*)                                             AS product_n
FROM v_risk_score_us
WHERE risk_level = 'undiagnosed'
GROUP BY category, category_source
ORDER BY product_n DESC;
