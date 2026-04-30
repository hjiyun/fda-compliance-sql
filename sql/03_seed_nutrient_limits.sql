-- ============================================================
-- 03_seed_nutrient_limits.sql
-- FDA Daily Value 기반 영양소 임계값 시드 (4종)
-- 임계값 = Daily Value × 20% (100g 기준)
-- ============================================================

INSERT INTO nutrient_limits (
    nutrient_code,
    nutrient_name_kr,
    nutrient_name_en,
    unit,
    daily_value,
    high_threshold_100g,
    threshold_ratio,
    is_public_concern,
    description
) VALUES
    ('sodium',        '나트륨',   'Sodium',        'mg',   2300,  460, 0.20, TRUE,  NULL),
    ('sugars',        '당류',     'Sugars',        'g',      50,   10, 0.20, TRUE,  NULL),
    ('saturated_fat', '포화지방', 'Saturated Fat', 'g',      20,    4, 0.20, TRUE,  NULL),
    ('energy',        '에너지',   'Energy',        'kcal', 2000,  400, 0.20, FALSE, NULL)
ON CONFLICT (nutrient_code) DO UPDATE SET
    nutrient_name_kr     = EXCLUDED.nutrient_name_kr,
    nutrient_name_en     = EXCLUDED.nutrient_name_en,
    unit                 = EXCLUDED.unit,
    daily_value          = EXCLUDED.daily_value,
    high_threshold_100g  = EXCLUDED.high_threshold_100g,
    threshold_ratio      = EXCLUDED.threshold_ratio,
    is_public_concern    = EXCLUDED.is_public_concern;

SELECT * FROM nutrient_limits ORDER BY nutrient_code;
