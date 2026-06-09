-- ============================================================
-- Q11. 한국 식품 2,493 건 라벨 표시 의무 전수 진단 (다국가)
--
-- 목적: 본 연구의 SQL 룰 엔진을 *수출 시장별 라벨 표시 의무*
--       의 정량 점검 도구로 활용한 실무 사례.
--
-- 분석 단위: (제품 × 국가) = 2,493 × 3 = 7,479 행
--
-- label_burden_level 정의 (제품의 4 영양소 중 high 판정 개수 기준):
--   safe              : 0 high  — 라벨 표시 의무 없음
--   single_warning    : 1 high  — 단일 영양소 "high in ..." 표시 의무
--   multiple_warning  : 2+ high — 다중 영양소 동시 경고 표시 의무
--   undiagnosed       : 4 영양소 모두 NULL — 진단 불가
--
-- 본 정의는 21 CFR 101.13 의 "high in ..." 표시 자격 (% DV ≥ 20 %)
-- 을 시장별 라벨 의무로 환산한 surrogate 기준이며, 본 연구의 100 g 기준
-- 통일(3.2.3 절) 가정에 종속한다.
--
-- 실무 활용:
--   (a) 수출 기업: 어느 국가 시장이 라벨 부담이 작은가
--   (b) 한국 식약처: 한국 식품의 국제 표준 정합성 사전 점검
--   (c) Streamlit 등 사전 점검 도구의 정량 토대
-- ============================================================

-- 11-A. 국가별 label_burden_level 분포 (집계)
--   CTE 로 burden 라벨을 먼저 부여한 뒤 외부에서 GROUP BY (PostgreSQL 의
--   ORDER BY CASE 별칭 참조 제약 회피 — Week 3 학습 노트 참조)
WITH burden AS (
    SELECT
        country_code,
        CASE
            WHEN diagnosed_count = 0     THEN 'undiagnosed'
            WHEN high_count     = 0      THEN 'safe'
            WHEN high_count     = 1      THEN 'single_warning'
            WHEN high_count    >= 2      THEN 'multiple_warning'
        END AS label_burden_level
    FROM v_risk_score
)
SELECT
    country_code,
    label_burden_level,
    COUNT(*)                                     AS product_n,
    ROUND(COUNT(*)::numeric
          / SUM(COUNT(*)) OVER (PARTITION BY country_code)
          * 100, 2)                              AS share_pct
FROM burden
GROUP BY country_code, label_burden_level
ORDER BY country_code,
         CASE label_burden_level
            WHEN 'safe'              THEN 1
            WHEN 'single_warning'    THEN 2
            WHEN 'multiple_warning'  THEN 3
            WHEN 'undiagnosed'       THEN 4
         END;


-- 11-B. 국가 × 영양소별 라벨 의무 빈도
--   (어느 영양소가 어느 시장에서 라벨 표시 의무를 가장 많이 유발하는가)
SELECT
    country_code,
    nutrient_code,
    COUNT(*) FILTER (WHERE judgment = 'high')      AS high_n,
    COUNT(*)                                       AS measured_n,
    ROUND(COUNT(*) FILTER (WHERE judgment = 'high')::numeric
          / NULLIF(COUNT(*), 0) * 100, 2)          AS high_pct
FROM v_compliance_results
GROUP BY country_code, nutrient_code
ORDER BY country_code, high_pct DESC;


-- 11-C. 시장 선택 시사 — 국가별 라벨 부담 요약 (3 국 직접 비교)
WITH burden AS (
    SELECT
        country_code,
        CASE
            WHEN diagnosed_count = 0     THEN 'undiagnosed'
            WHEN high_count     = 0      THEN 'safe'
            WHEN high_count     = 1      THEN 'single_warning'
            WHEN high_count    >= 2      THEN 'multiple_warning'
        END                                          AS label_burden_level
    FROM v_risk_score
)
SELECT
    country_code,
    COUNT(*) FILTER (WHERE label_burden_level = 'safe')             AS safe_n,
    COUNT(*) FILTER (WHERE label_burden_level = 'single_warning')   AS single_n,
    COUNT(*) FILTER (WHERE label_burden_level = 'multiple_warning') AS multiple_n,
    COUNT(*) FILTER (WHERE label_burden_level = 'undiagnosed')      AS undx_n,
    ROUND(COUNT(*) FILTER (WHERE label_burden_level IN
                                 ('safe', 'undiagnosed'))::numeric
          / COUNT(*) * 100, 2)                                       AS pass_pct
FROM burden
GROUP BY country_code
ORDER BY pass_pct DESC;


-- 11-D. (제품 × 국가) 단위 전수 진단 — CSV 산출용 평탄화 (7,479 행)
SELECT
    rs.product_id,
    rs.product_name,
    rs.category,
    rs.category_source,
    rs.country_code,
    rs.high_count,
    rs.moderate_count,
    rs.low_count,
    rs.diagnosed_count,
    rs.risk_level,
    CASE
        WHEN rs.diagnosed_count = 0     THEN 'undiagnosed'
        WHEN rs.high_count     = 0      THEN 'safe'
        WHEN rs.high_count     = 1      THEN 'single_warning'
        WHEN rs.high_count    >= 2      THEN 'multiple_warning'
    END                                          AS label_burden_level
FROM v_risk_score rs
ORDER BY rs.product_id, rs.country_code;
