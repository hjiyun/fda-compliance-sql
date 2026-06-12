-- ============================================================
-- 07_burden_score.sql
-- 부정 영양소 종합 부담 점수 (축약 Nutri-Score) — Level 2 경량 구현
--
-- 목적: 기존 Level 1 룰 엔진의 "영양소 간 상호작용 미반영" 한계 보완.
--   룰 엔진은 영양소별로 행이 분리되어 "여러 영양소가 동시에 높은 제품"과
--   "하나만 높은 제품"을 종합 구분하지 못한다. (제품 × 국가) 단위로 4영양소
--   점수를 SUM 하면 그 누적(상호작용) 효과가 점수로 드러난다.
--
-- 설계 원칙 (자의성 방지):
--   1. 배점을 새로 만들지 않는다. 기존 judgment 3단계(v_compliance_results,
--      21 CFR 101.13 의 5%/20% DV 기준)를 그대로 점수로 환산:
--        high (%DV ≥ 20)        → 2점
--        moderate (5 ≤ %DV < 20) → 1점
--        low (%DV < 5)          → 0점
--      → 배점이 기존 표준 임계값에서 파생되므로 새 숫자 도입 없음.
--   2. 동등 가중(가중치 없음). 가중은 정당화 부담만 키워 향후 과제로 남김.
--   3. 국가별 각각 산출 — country 필터 없이 JOIN 된 구조를 유지해 한 제품이
--      FDA/EU/CODEX 종합 점수를 각각 갖는다(다국가 비교 정체성).
--
-- NULL 보존 정책 유지: 결측 영양소는 v_compliance_results 의 INNER JOIN 으로
--   행 자체가 없어 SUM 에서 자동 제외된다. nutrients_assessed 로 몇 개 영양소가
--   평가됐는지 드러내, 4개 평가 제품과 2개 평가 제품을 같은 선상에서 비교하지
--   않도록 한다. (4영양소 전부 결측인 366 제품은 본 VIEW 에 행이 없음.)
--
-- 사전 조건: 06_dual_views.sql (v_compliance_results) 적용 완료.
-- ============================================================

BEGIN;

DROP VIEW IF EXISTS v_nutrient_burden_score CASCADE;

CREATE VIEW v_nutrient_burden_score AS
SELECT
    product_id,
    country_code,
    SUM(CASE judgment WHEN 'high'     THEN 2
                      WHEN 'moderate' THEN 1
                      ELSE 0 END)                       AS burden_score,
    COUNT(*)                                            AS nutrients_assessed,
    CASE
        WHEN SUM(CASE judgment WHEN 'high'     THEN 2
                               WHEN 'moderate' THEN 1
                               ELSE 0 END) = 0          THEN '부담 없음'
        WHEN SUM(CASE judgment WHEN 'high'     THEN 2
                               WHEN 'moderate' THEN 1
                               ELSE 0 END) <= 3         THEN '주의'
        ELSE                                                 '고부담'
    END                                                 AS burden_grade
FROM v_compliance_results
GROUP BY product_id, country_code;

COMMENT ON VIEW v_nutrient_burden_score IS
'부정 영양소 종합 부담 점수(축약 Nutri-Score). judgment(high=2/moderate=1/low=0) 를
 (제품×국가) 단위로 SUM. 동등가중·부정영양소만 — 완전한 영양품질 평가 아님.';

COMMIT;

-- ============================================================
-- 검증 1 — 대표 사례 (신라면 id=6, 서울우유 id=595) 3국 비교
-- ============================================================
SELECT b.product_id, p.product_name, b.country_code,
       b.burden_score, b.nutrients_assessed, b.burden_grade
FROM v_nutrient_burden_score b
JOIN products p ON p.product_id = b.product_id
WHERE b.product_id IN (6, 595)
ORDER BY b.product_id,
         CASE b.country_code WHEN 'EU' THEN 1 WHEN 'US' THEN 2 ELSE 3 END;

-- ============================================================
-- 검증 2 — 국가별 burden_score 분포 (0 ~ 8)
-- ============================================================
SELECT country_code, burden_score, COUNT(*) AS n_products
FROM v_nutrient_burden_score
GROUP BY country_code, burden_score
ORDER BY country_code, burden_score;
