-- ============================================================
-- 01_schema.sql
-- 표준학개론 2차 프로젝트: FDA 식품 라벨링 적합성 진단 DB 스키마
-- 테이블 6개(필수 4 + 선택 확장 2) + 인덱스 2개 생성
-- ============================================================

-- ----- 재실행 안전성: 의존 역순으로 DROP -----
DROP TABLE IF EXISTS product_allergens  CASCADE;
DROP TABLE IF EXISTS product_nutrients  CASCADE;
DROP TABLE IF EXISTS allergens          CASCADE;
DROP TABLE IF EXISTS products           CASCADE;
DROP TABLE IF EXISTS nutrient_limits    CASCADE;
DROP TABLE IF EXISTS categories         CASCADE;

-- ============================================================
-- 1. categories : 식품 카테고리 마스터
-- ============================================================
CREATE TABLE categories (
    category_id     SERIAL PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  categories                IS '식품 카테고리 마스터';
COMMENT ON COLUMN categories.category_id    IS '카테고리 ID (PK)';
COMMENT ON COLUMN categories.category_name  IS '카테고리명 (예: 과자류, 음료, 유제품)';
COMMENT ON COLUMN categories.description    IS '카테고리 설명';
COMMENT ON COLUMN categories.created_at     IS '레코드 생성 시각';

-- ============================================================
-- 2. nutrient_limits : FDA Daily Value 기반 영양소 임계값 기준
-- ============================================================
CREATE TABLE nutrient_limits (
    nutrient_code        VARCHAR(30)   PRIMARY KEY,
    nutrient_name_kr     VARCHAR(50)   NOT NULL,
    nutrient_name_en     VARCHAR(50)   NOT NULL,
    unit                 VARCHAR(10)   NOT NULL,
    daily_value          NUMERIC(10,2) NOT NULL,
    high_threshold_100g  NUMERIC(10,2) NOT NULL,
    threshold_ratio      NUMERIC(4,2)  DEFAULT 0.20,
    is_public_concern    BOOLEAN       DEFAULT FALSE,
    description          TEXT
);

COMMENT ON TABLE  nutrient_limits                        IS 'FDA Daily Value 기반 영양소 임계값 기준';
COMMENT ON COLUMN nutrient_limits.nutrient_code          IS '영양소 코드 (sodium / sugars / saturated_fat / energy)';
COMMENT ON COLUMN nutrient_limits.nutrient_name_kr       IS '영양소 한글명 (보고서/ERD 일관성을 위해 _kr 사용)';
COMMENT ON COLUMN nutrient_limits.nutrient_name_en       IS '영양소 영문명';
COMMENT ON COLUMN nutrient_limits.unit                   IS '단위 (mg, g, kcal)';
COMMENT ON COLUMN nutrient_limits.daily_value            IS '1일 권장량 (FDA Daily Value)';
COMMENT ON COLUMN nutrient_limits.high_threshold_100g    IS '100g당 고함량 임계값 (DV의 20%)';
COMMENT ON COLUMN nutrient_limits.threshold_ratio        IS '임계값 산정 비율 (기본 0.20 = 20%)';
COMMENT ON COLUMN nutrient_limits.is_public_concern      IS 'FDA 공중보건 우려 영양소 여부 (sodium/sugars/saturated_fat=TRUE)';
COMMENT ON COLUMN nutrient_limits.description            IS '영양소 설명 (선택)';

-- ============================================================
-- 3. products : 제품 마스터 (Open Food Facts 한국 식품)
-- ============================================================
CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    product_code     VARCHAR(50)  UNIQUE,
    product_name     VARCHAR(255) NOT NULL,
    brand            VARCHAR(100),
    category_id      INT          REFERENCES categories(category_id) ON DELETE SET NULL,
    category_source  VARCHAR(10)  NOT NULL DEFAULT 'other',
    serving_size_g   NUMERIC(10,2),
    country          VARCHAR(50)  DEFAULT 'Korea',
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  products                   IS '식품 제품 마스터 (Open Food Facts 한국 식품 2,493건)';
COMMENT ON COLUMN products.product_id        IS '제품 ID (PK)';
COMMENT ON COLUMN products.product_code      IS '제품 코드 / 바코드 (EAN)';
COMMENT ON COLUMN products.product_name      IS '제품명';
COMMENT ON COLUMN products.brand             IS '브랜드명';
COMMENT ON COLUMN products.category_id       IS '카테고리 FK';
COMMENT ON COLUMN products.category_source   IS '카테고리 매핑 출처: tags(categories_tags) / top(category_top) / free(categories 자유텍스트) / name(product_name) / other';
COMMENT ON COLUMN products.serving_size_g    IS '1회 제공량 (g)';
COMMENT ON COLUMN products.country           IS '판매 국가 (기본: Korea)';
COMMENT ON COLUMN products.created_at        IS '레코드 생성 시각';

-- ============================================================
-- 4. product_nutrients : 제품별 영양소 함량 (100g 기준)
-- ============================================================
CREATE TABLE product_nutrients (
    nutrient_row_id   SERIAL PRIMARY KEY,
    product_id        INT           NOT NULL REFERENCES products(product_id)             ON DELETE CASCADE,
    nutrient_code     VARCHAR(30)   NOT NULL REFERENCES nutrient_limits(nutrient_code),
    amount_per_100g   NUMERIC(10,2) NOT NULL,
    UNIQUE (product_id, nutrient_code)
);

COMMENT ON TABLE  product_nutrients                  IS '제품별 영양소 함량 (100g 기준)';
COMMENT ON COLUMN product_nutrients.nutrient_row_id  IS '레코드 ID (PK)';
COMMENT ON COLUMN product_nutrients.product_id       IS '제품 FK';
COMMENT ON COLUMN product_nutrients.nutrient_code    IS '영양소 코드 FK';
COMMENT ON COLUMN product_nutrients.amount_per_100g  IS '100g당 함량 (단위는 nutrient_limits.unit 참조)';

-- ============================================================
-- 5. allergens : 알레르기 유발 성분 마스터 (선택 확장)
-- ============================================================
CREATE TABLE allergens (
    allergen_id       SERIAL PRIMARY KEY,
    allergen_code     VARCHAR(30) NOT NULL UNIQUE,
    allergen_name_ko  VARCHAR(50) NOT NULL,
    description       TEXT
);

COMMENT ON TABLE  allergens                     IS '알레르기 유발 성분 마스터';
COMMENT ON COLUMN allergens.allergen_id         IS '알레르기 ID (PK)';
COMMENT ON COLUMN allergens.allergen_code       IS '알레르기 코드 (예: milk, egg, peanut)';
COMMENT ON COLUMN allergens.allergen_name_ko    IS '알레르기 한글명';
COMMENT ON COLUMN allergens.description         IS '설명';

-- ============================================================
-- 6. product_allergens : 제품-알레르기 매핑 (선택 확장)
-- ============================================================
CREATE TABLE product_allergens (
    product_id    INT NOT NULL REFERENCES products(product_id)   ON DELETE CASCADE,
    allergen_id   INT NOT NULL REFERENCES allergens(allergen_id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, allergen_id)
);

COMMENT ON TABLE  product_allergens               IS '제품-알레르기 매핑';
COMMENT ON COLUMN product_allergens.product_id    IS '제품 FK';
COMMENT ON COLUMN product_allergens.allergen_id   IS '알레르기 FK';

-- ============================================================
-- 인덱스 (FK 컬럼은 PostgreSQL이 자동 생성하지 않으므로 명시)
-- ============================================================
CREATE INDEX idx_products_category_id            ON products(category_id);
CREATE INDEX idx_product_nutrients_nutrient_code ON product_nutrients(nutrient_code);

-- ============================================================
-- 완료 메시지
-- ============================================================
SELECT '✅ 01_schema.sql 실행 완료 - 테이블 6개 + 인덱스 2개 생성' AS message;
