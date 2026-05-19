-- ============================================================
-- 05_multi_country_migration.sql
-- Week 4 마이그레이션 — 옵션 B (정규화)
--   단일국 nutrient_limits  →  nutrients (정체성) + nutrient_limits (국가별 표준값)
--
-- 사전 조건: Week 1~3 스키마/시드가 적재된 상태 + pg_dump 백업 완료
-- 효과:
--   1. v_compliance_results / v_risk_score CASCADE 삭제 (컬럼 의존성 해소)
--   2. nutrients 신규 테이블 (4행, 영양소 정체성)
--   3. product_nutrients.FK 이동: nutrient_limits → nutrients
--   4. nutrient_limits 재구조화 (PK = (country_code, nutrient_code))
--   5. 기존 4행 데이터는 country_code='US' 로 보존
--   6. EU · CODEX 각 4행 적재 → 총 12행
--   7. VIEW 재생성 (Step 4.5 회귀 검증용 — Week 3 호환 형태로 임시 복원)
--      Step 5 에서 듀얼 VIEW (v_compliance_results 다국가 + v_compliance_us 필터) 로 교체 예정
-- ============================================================

BEGIN;

-- ============================================================
-- Step A. 의존 VIEW 삭제 (CASCADE 로 양쪽 한꺼번에)
-- ============================================================
DROP VIEW IF EXISTS v_risk_score          CASCADE;
DROP VIEW IF EXISTS v_compliance_results  CASCADE;

-- ============================================================
-- Step B. nutrients 마스터 테이블 신설 + 기존 정체성 4행 이전
-- ============================================================
CREATE TABLE IF NOT EXISTS nutrients (
    nutrient_code      VARCHAR(30) PRIMARY KEY,
    nutrient_name_kr   VARCHAR(50) NOT NULL,
    nutrient_name_en   VARCHAR(50) NOT NULL,
    unit               VARCHAR(10) NOT NULL,
    is_public_concern  BOOLEAN DEFAULT FALSE,
    description        TEXT
);

COMMENT ON TABLE  nutrients                     IS '영양소 정체성 마스터 (국가 무관)';
COMMENT ON COLUMN nutrients.nutrient_code       IS '영양소 코드 (PK)';
COMMENT ON COLUMN nutrients.is_public_concern   IS 'FDA Nutrient of Public Health Concern 여부';

INSERT INTO nutrients (
    nutrient_code, nutrient_name_kr, nutrient_name_en, unit, is_public_concern, description
)
SELECT
    nutrient_code, nutrient_name_kr, nutrient_name_en, unit, is_public_concern, description
FROM nutrient_limits
ON CONFLICT (nutrient_code) DO NOTHING;

-- ============================================================
-- Step C. product_nutrients FK 이동: nutrient_limits → nutrients
-- ============================================================
ALTER TABLE product_nutrients
    DROP CONSTRAINT IF EXISTS product_nutrients_nutrient_code_fkey;

ALTER TABLE product_nutrients
    ADD CONSTRAINT product_nutrients_nutrient_code_fkey
    FOREIGN KEY (nutrient_code) REFERENCES nutrients(nutrient_code);

-- ============================================================
-- Step D. nutrient_limits 재구조화
-- ============================================================
ALTER TABLE nutrient_limits DROP CONSTRAINT IF EXISTS nutrient_limits_pkey;

ALTER TABLE nutrient_limits
    ADD COLUMN IF NOT EXISTS country_code VARCHAR(10) NOT NULL DEFAULT 'US';
ALTER TABLE nutrient_limits ALTER COLUMN country_code DROP DEFAULT;

ALTER TABLE nutrient_limits ADD COLUMN IF NOT EXISTS source          VARCHAR(200);
ALTER TABLE nutrient_limits ADD COLUMN IF NOT EXISTS effective_date  DATE;
ALTER TABLE nutrient_limits ADD COLUMN IF NOT EXISTS sugar_type      VARCHAR(20);

-- 정체성 컬럼 제거 (nutrients 로 이전됨) — 이 시점에 VIEW 가 사라져 있어 안전
ALTER TABLE nutrient_limits DROP COLUMN IF EXISTS nutrient_name_kr;
ALTER TABLE nutrient_limits DROP COLUMN IF EXISTS nutrient_name_en;
ALTER TABLE nutrient_limits DROP COLUMN IF EXISTS unit;
ALTER TABLE nutrient_limits DROP COLUMN IF EXISTS is_public_concern;
ALTER TABLE nutrient_limits DROP COLUMN IF EXISTS description;

ALTER TABLE nutrient_limits
    ADD CONSTRAINT nutrient_limits_pkey PRIMARY KEY (country_code, nutrient_code);

ALTER TABLE nutrient_limits
    ADD CONSTRAINT nutrient_limits_nutrient_code_fkey
    FOREIGN KEY (nutrient_code) REFERENCES nutrients(nutrient_code);

ALTER TABLE nutrient_limits
    ADD CONSTRAINT nutrient_limits_sugar_type_chk
    CHECK (sugar_type IS NULL OR sugar_type IN ('added', 'total', 'free'));

COMMENT ON COLUMN nutrient_limits.country_code     IS '표준 발행 국가/기구 (US / EU / CODEX)';
COMMENT ON COLUMN nutrient_limits.source           IS '근거 규정 (예: 21 CFR 101.9)';
COMMENT ON COLUMN nutrient_limits.effective_date   IS '규정 효력 발생일';
COMMENT ON COLUMN nutrient_limits.sugar_type       IS '당류 정의 종류 (added / total / free / NULL)';

-- ============================================================
-- Step E. US 4행 보강 (source, effective_date, sugar_type)
-- ============================================================
UPDATE nutrient_limits SET
    source         = '21 CFR 101.9',
    effective_date = DATE '2016-05-27',
    sugar_type     = CASE WHEN nutrient_code = 'sugars' THEN 'added' END
WHERE country_code = 'US';

-- ============================================================
-- Step F. EU (Regulation 1169/2011) 4행
-- ============================================================
INSERT INTO nutrient_limits (
    country_code, nutrient_code, daily_value, high_threshold_100g,
    threshold_ratio, source, effective_date, sugar_type
) VALUES
    ('EU', 'sodium',        2400.00, 480.00, 0.20, 'Regulation 1169/2011', DATE '2014-12-13', NULL),
    ('EU', 'saturated_fat',   20.00,   4.00, 0.20, 'Regulation 1169/2011', DATE '2014-12-13', NULL),
    ('EU', 'sugars',          90.00,  18.00, 0.20, 'Regulation 1169/2011', DATE '2014-12-13', 'total'),
    ('EU', 'energy',        2000.00, 400.00, 0.20, 'Regulation 1169/2011', DATE '2014-12-13', NULL)
ON CONFLICT (country_code, nutrient_code) DO UPDATE SET
    daily_value         = EXCLUDED.daily_value,
    high_threshold_100g = EXCLUDED.high_threshold_100g,
    source              = EXCLUDED.source,
    effective_date      = EXCLUDED.effective_date,
    sugar_type          = EXCLUDED.sugar_type;

-- ============================================================
-- Step G. CODEX (CAC/GL 2-1985 + WHO) 4행
-- ============================================================
INSERT INTO nutrient_limits (
    country_code, nutrient_code, daily_value, high_threshold_100g,
    threshold_ratio, source, effective_date, sugar_type
) VALUES
    ('CODEX', 'sodium',        2000.00, 400.00, 0.20, 'CAC/GL 2-1985 (NRV-NCD)', DATE '2013-07-08', NULL),
    ('CODEX', 'saturated_fat',   20.00,   4.00, 0.20, 'CAC/GL 2-1985 (NRV-NCD)', DATE '2013-07-08', NULL),
    ('CODEX', 'sugars',          50.00,  10.00, 0.20, 'WHO Sugars Guideline',    DATE '2015-03-04', 'free'),
    ('CODEX', 'energy',        2000.00, 400.00, 0.20, 'WHO Recommendation',      DATE '2015-03-04', NULL)
ON CONFLICT (country_code, nutrient_code) DO UPDATE SET
    daily_value         = EXCLUDED.daily_value,
    high_threshold_100g = EXCLUDED.high_threshold_100g,
    source              = EXCLUDED.source,
    effective_date      = EXCLUDED.effective_date,
    sugar_type          = EXCLUDED.sugar_type;

-- ============================================================
-- Step H. VIEW 재생성 — Week 3 호환 임시 형태 (Step 4.5 회귀 검증용)
--   Step 5 에서 듀얼 VIEW 로 다시 교체.
-- ============================================================
CREATE VIEW v_compliance_results AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name        AS category,
    p.category_source,
    pn.nutrient_code,
    n.nutrient_name_kr,
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
                                AND nl.country_code = 'US'
LEFT JOIN  categories        c  ON c.category_id    = p.category_id;

COMMENT ON VIEW v_compliance_results IS
'(Week 4 임시) Week 3 호환 단일국 진단 VIEW. Step 5 에서 다국가 / _us 분리 예정.';

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
'(Week 4 임시) Week 3 호환 제품별 위험도. v_compliance_results 가 US 만 포함하므로 단일국 의미 유지.';

COMMIT;

-- ============================================================
-- 검증
-- ============================================================
SELECT '✅ migration complete' AS status;

SELECT 'nutrients'                AS t, count(*) FROM nutrients
UNION ALL
SELECT 'nutrient_limits total',      count(*) FROM nutrient_limits
UNION ALL
SELECT 'nutrient_limits US',         count(*) FROM nutrient_limits WHERE country_code = 'US'
UNION ALL
SELECT 'nutrient_limits EU',         count(*) FROM nutrient_limits WHERE country_code = 'EU'
UNION ALL
SELECT 'nutrient_limits CODEX',      count(*) FROM nutrient_limits WHERE country_code = 'CODEX'
UNION ALL
SELECT 'v_compliance_results rows',  count(*) FROM v_compliance_results
UNION ALL
SELECT 'v_risk_score rows',          count(*) FROM v_risk_score;
