-- ============================================================
-- Q2. 카테고리별 위반(high) 비율 — 신뢰 그룹 vs 전체 비교
--
-- 분모: 카테고리별 진단된 (제품, 영양소) 쌍 수 (NULL 제외)
-- 분자: high 판정 수
-- 추가: WHERE category != 'Other' 조건의 효과 비교
-- ============================================================

-- 2-A. 모든 카테고리 (Other 포함)
SELECT
    COALESCE(category, '(NULL)')                                  AS category,
    COUNT(*)                                                      AS diagnosed_n,
    COUNT(*) FILTER (WHERE judgment = 'high')                     AS high_n,
    ROUND(COUNT(*) FILTER (WHERE judgment = 'high')::numeric
          / NULLIF(COUNT(*), 0) * 100, 2)                         AS high_pct
FROM v_compliance_results
GROUP BY category
ORDER BY high_pct DESC;

-- 2-B. Other 제외 — 분류된 카테고리만
SELECT
    'classified (excl. Other)'                                    AS scope,
    COUNT(*)                                                      AS diagnosed_n,
    COUNT(*) FILTER (WHERE judgment = 'high')                     AS high_n,
    ROUND(COUNT(*) FILTER (WHERE judgment = 'high')::numeric
          / NULLIF(COUNT(*), 0) * 100, 2)                         AS high_pct
FROM v_compliance_results
WHERE category != 'Other'
UNION ALL
SELECT
    'Other only',
    COUNT(*),
    COUNT(*) FILTER (WHERE judgment = 'high'),
    ROUND(COUNT(*) FILTER (WHERE judgment = 'high')::numeric
          / NULLIF(COUNT(*), 0) * 100, 2)
FROM v_compliance_results
WHERE category = 'Other'
UNION ALL
SELECT
    'all',
    COUNT(*),
    COUNT(*) FILTER (WHERE judgment = 'high'),
    ROUND(COUNT(*) FILTER (WHERE judgment = 'high')::numeric
          / NULLIF(COUNT(*), 0) * 100, 2)
FROM v_compliance_results;
