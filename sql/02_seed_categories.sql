-- ============================================================
-- 02_seed_categories.sql
-- 식품 카테고리 마스터 시드 데이터 (초기 6종)
-- 추후 ETL 단계에서 1차 프로젝트 food.parquet 의 category_top 분포에 맞춰 보강 예정
-- ============================================================

INSERT INTO categories (category_name, description) VALUES
    ('Snacks',    '스낵류 (과자, 칩, 시리얼바 등)'),
    ('Beverages', '음료류 (탄산음료, 주스, 커피, 차 등)'),
    ('Dairy',     '유제품 (우유, 요거트, 치즈 등)'),
    ('Meals',     '식사류 (간편식, 밀키트, 라면 등)'),
    ('Sweets',    '디저트·과자류 (초콜릿, 사탕, 케이크 등)'),
    ('Other',     '기타 (위 분류에 속하지 않는 식품)')
ON CONFLICT (category_name) DO NOTHING;

SELECT * FROM categories ORDER BY category_id;
