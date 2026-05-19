-- ============================================================
-- Q5. VIEW 활용 종합 진단 — 위험도 분포 + 각 등급 대표 5개 제품
--
-- 5-A: v_risk_score 의 risk_level 분포 (전체 2,493건 기준)
-- 5-B: 각 등급별 대표 제품 5개 (high_count → moderate_count 내림차순)
-- ============================================================

-- 5-A. 위험도 분포 (전체 제품 기준)
SELECT
    risk_level,
    COUNT(*)                                            AS product_n,
    ROUND(COUNT(*)::numeric
          / SUM(COUNT(*)) OVER () * 100, 2)             AS share_pct
FROM v_risk_score_us
GROUP BY risk_level
ORDER BY
    CASE risk_level
        WHEN 'high'        THEN 1
        WHEN 'medium'      THEN 2
        WHEN 'low'         THEN 3
        WHEN 'undiagnosed' THEN 4
    END;

-- 5-B. 각 등급별 대표 제품 5개
WITH ranked AS (
    SELECT
        risk_level,
        product_id,
        product_name,
        category,
        category_source,
        high_count,
        moderate_count,
        low_count,
        null_count,
        ROW_NUMBER() OVER (
            PARTITION BY risk_level
            ORDER BY high_count DESC, moderate_count DESC, product_id
        )                                              AS rn
    FROM v_risk_score_us
)
SELECT
    risk_level,
    rn,
    product_name,
    category,
    category_source,
    high_count,
    moderate_count,
    low_count,
    null_count
FROM ranked
WHERE rn <= 5
ORDER BY
    CASE risk_level
        WHEN 'high'        THEN 1
        WHEN 'medium'      THEN 2
        WHEN 'low'         THEN 3
        WHEN 'undiagnosed' THEN 4
    END,
    rn;
