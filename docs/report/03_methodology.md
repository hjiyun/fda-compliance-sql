# 3. 연구 방법론

본 장은 본 연구의 분석 파이프라인을 *데이터셋 → 데이터베이스 설계 → ETL → SQL 분석* 의 4 단계로 기술한다. 3.1 절에서는 분석 대상 한국 식품 2,493 건의 출처와 큐레이션 정책을, 3.2 절에서는 다국가 표준을 단일 스키마에 적재하기 위한 데이터베이스 설계를, 3.3 절에서는 Open Food Facts 원본 데이터의 추출·변환·적재(ETL) 절차를, 3.4 절에서는 적합성 진단을 위한 SQL 분석 기법과 통계 검증을 다룬다. 각 절의 *방법론적 결정의 부산물* 로 발생한 한계는 해당 절 끝에 명시하며, *결과 해석상의 한계* 는 본 장에서 다루지 않고 5 장으로 미룬다.

## 3.1 데이터셋

### 3.1.1 데이터 출처 — Open Food Facts (OFF)

본 연구의 분석 대상 데이터는 **Open Food Facts** (이하 OFF) 의 공개 데이터 덤프에서 추출하였다. OFF 는 2012 년에 시작된 시민 참여형 식품 데이터베이스로, 전 세계 자원봉사자가 제품 라벨의 영양 성분 · 성분 목록 · 카테고리 · 바코드 등을 입력하고 다중 검증하는 방식으로 운영된다. 본 연구 시점(2026 년 5 월) 기준 OFF 에는 약 350 만 건 이상의 제품이 등재되어 있으며, 그중 한국 식품(`countries_tags` 에 `en:south-korea` 또는 `en:korea` 가 포함된 행) 은 약 8,000 여 건으로 확인된다.

OFF 데이터의 표준학적 특성은 2.3.3 절에서 논의한 *시민 참여 데이터의 구조적 메타데이터 한계* 를 동반한다. 특히 카테고리 메타데이터는 자유 텍스트(`categories`) · 영문 표준화 태그(`categories_tags`) · 단일 최상위 분류(`category_top`) 의 다층 구조로 등재되어 있고, 한국 식품 표본에서는 이 세 필드 모두에서 결측이 흔하다. 본 연구는 이러한 결측을 완화하기 위해 4-tier fallback 매핑 정책을 적용한다(3.3.2 절). 한편 영양소 측정값은 OFF 의 `nutriments` 필드에 100 g 기준으로 정규화되어 등재되어 있으며, 본 연구의 핵심 4 영양소(energy · sugars · saturated_fat · sodium) 모두 100 g 단위로 추출 가능하다. 다만 영양소별 결측률은 sodium 47.5 %, saturated_fat 39.8 %, sugars 33.4 %, energy 15.0 % 의 분포를 보여 OFF 의 구조적 한계가 영양소마다 비대칭으로 나타난다.

### 3.1.2 분석 대상 큐레이션 — 2,493 건의 선별

본 연구는 1차 프로젝트("합성데이터 기반 TBT 식품 위반 탐지 AI 시스템") 에서 큐레이션한 한국 식품 2,493 건을 동일하게 분석 대상으로 채택한다. 동일 모집단 유지는 *데이터 기반 분류 결과* (1차) 와 *룰 기반 적합성 결과* (본 연구) 의 직접 비교 가능성을 확보하기 위한 결정이다. 큐레이션 절차는 다음 세 단계로 요약된다.

먼저 OFF 원본에서 한국이 `countries_tags` 에 포함된 약 8,372 건을 1차 추출하고, 그중 1차 프로젝트의 TBT 분석 산출물(`tbt_analysis_result.parquet`, 제품 코드 단위) 과 OFF 원본의 교집합을 취하여 **2,493 건** 으로 확정한다. 마지막으로 영양소 값은 1차 프로젝트가 결측을 `0` 으로 대치한 wide 형식 컬럼(`energy_100g`, `sugars_100g` 등) 을 사용하지 않고, OFF 원본의 `nutriments` 딕셔너리에서 직접 재추출하여 결측을 NULL 로 보존한다.

NULL 보존 정책의 표준학적 근거는 *위양성 적합 판정의 회피* 에 있다. 1차 프로젝트는 분류 모델 학습을 위해 결측을 `0` 으로 대치하는 통계적 처리를 채택하였으나, 룰 기반 적합성 진단에서 결측을 `0` 으로 처리하면 실제로는 측정되지 않은 영양소를 "임계값 미만 = 적합" 으로 잘못 판정할 위험이 발생한다. 본 연구는 결측 (제품, 영양소) 쌍을 `product_nutrients` 테이블에 행 자체를 삽입하지 않는 방식으로 보존하며, 진단 VIEW (3.4.1 절) 의 INNER JOIN 구조에 의해 결측 행이 진단 결과에서 자동으로 제외되도록 설계하였다. 본 데이터셋에서 1차의 `0` 대치 셀과 본 연구의 NULL 재추출 결과가 일치하는 *phantom 0* 셀은 합계 2,386 셀(9,972 셀의 23.9 %) 로 측정되었으며, 이는 NULL 보존 정책의 정량적 정당성을 뒷받침한다.

> **방법론적 한계 — NULL 보존의 trade-off.** NULL 보존은 위양성 적합을 회피하는 대신 *진단 가능한 (제품, 영양소) 쌍의 수 자체* 를 감소시킨다(9,972 → 6,589, −33.9 %). 특히 sodium 의 결측률(47.5 %) 이 가장 높아 sodium 진단 표본이 4 영양소 중 가장 작으며, 이는 통계 검증의 검정력에도 영향을 미친다. 본 trade-off 가 결과 해석에 미치는 영향은 5 장 5.3.3 절에서 다시 다룬다.

### 3.1.3 데이터 특성

큐레이션 결과 적재된 2,493 건의 기본 특성은 다음과 같다. (1) **카테고리 분류율** 은 4-tier fallback 매핑 후 42.6 % (1,062 건), 미분류(`Other`) 57.4 % (1,431 건) 이며, 1차 fallback 만 사용 시(`categories_tags` 단독) 분류율 10.4 % 대비 약 32 pp 의 개선을 달성하였다. (2) **영양소 결측률** 은 sodium 47.5 %, saturated_fat 39.8 %, sugars 33.4 %, energy 15.0 % 의 분포를 보이며, 4 영양소 모두 NULL 인 *undiagnosed* 제품은 366 건(14.7 %) 이다. (3) **국가 정보** 는 모든 제품이 한국(`country = 'Korea'`) 으로 단일하다.

## 3.2 데이터베이스 설계

### 3.2.1 스키마 설계 원칙

본 연구의 데이터베이스 스키마는 다음 네 가지 원칙을 따라 설계되었다.

첫째, **정체성 - 표준 분리** 원칙이다. 영양소의 정체성 정보(이름·단위·공중보건 우려 영양소 여부 등 국가 무관 속성) 와 국가별 표준값(daily_value, high_threshold_100g, source, effective_date 등) 을 별도 테이블로 분리하여 표준값이 국가별로 갱신될 때 정체성 정보의 중복을 회피한다.

둘째, **다국가 확장성** 원칙이다. 표준값 테이블의 PK 를 `(country_code, nutrient_code)` 복합 키로 설계하여, 새 국가 추가 시 별도의 스키마 변경 없이 행 추가만으로 확장된다.

셋째, **외래키 무결성** 원칙이다. 모든 참조 관계에 FK 제약을 명시하여 참조 무결성을 데이터베이스 수준에서 보장하며, 의존성에 따라 `CASCADE` (제품 삭제 시 영양소 행 동반 삭제) 또는 `SET NULL` (카테고리 삭제 시 참조만 해제) 정책을 구분 적용한다.

넷째, **재현성** 원칙이다. 모든 DDL 은 단일 SQL 스크립트로 관리되며, `DROP IF EXISTS` 로 시작하여 환경 재초기화가 단일 실행으로 가능하도록 설계되었다.

### 3.2.2 데이터베이스 구조 — 개관

본 연구의 데이터베이스는 **6 개 물리 테이블** 과 **4 개 VIEW** 로 구성된다. 핵심 구조는 다음과 같이 요약된다.

- 영양소 정체성 마스터(`nutrients`, 4 행) 와 국가별 표준값(`nutrient_limits`, 3 국 × 4 영양소 = 12 행) 이 정체성 - 표준 분리 원칙에 따라 별도 테이블로 구성된다.
- 한국 식품 제품 마스터(`products`, 2,493 행) 와 (제품, 영양소) 함량의 롱 포맷(`product_nutrients`, 6,589 행) 이 분석 단위의 코어를 이룬다.
- 카테고리 마스터(`categories`, 6 행) 가 `products.category_id` FK 로 연결되며, **`products.category_source`** 컬럼이 4-tier 매핑의 출처(`tags`/`top`/`free`/`name`/`other`) 를 행 단위로 추적한다. 이는 Q8 의 가설 검증(Trusted vs Other 비교) 의 데이터 기반이다.
- 알레르겐 확장 테이블 2 개(`allergens`, `product_allergens`) 는 향후 라벨링 차원 확장을 위해 선언만 되어 있으며, 본 연구에서는 미적재(0 행) 상태이다.
- 4 개 VIEW (`v_compliance_results`, `v_compliance_us`, `v_risk_score`, `v_risk_score_us`) 가 적합성 진단의 논리 계층을 형성한다(3.4.1 절).

전체 테이블 관계와 컬럼 정의는 [그림 3.1: ERD](../ERD.png) 와 GitHub 공개 레포지토리의 [sql/01_schema.sql](../../sql/01_schema.sql) (물리 테이블) · [sql/06_dual_views.sql](../../sql/06_dual_views.sql) (VIEW) 에서 재현 가능한 형태로 확인할 수 있다.

### 3.2.3 다국가 `nutrient_limits` 적재 — 3 국 × 4 영양소 = 12 행

본 연구 다국가 비교의 핵심은 `nutrient_limits` 테이블에 3 국 × 4 영양소 = 12 행을 적재하는 것이다. 적재된 행과 각 표준의 근거 규정은 [표 3.1] 과 같다.

**[표 3.1] 다국가 `nutrient_limits` 적재 (12 행)**

| country | nutrient | daily_value | high_threshold_100g | unit | sugar_type | source |
|---|---|---:|---:|---|---|---|
| US | sodium | 2,300 | 460 | mg | — | 21 CFR 101.9 |
| US | sugars | 50 | 10 | g | added | 21 CFR 101.9 |
| US | saturated_fat | 20 | 4 | g | — | 21 CFR 101.9 |
| US | energy | 2,000 | 400 | kcal | — | 21 CFR 101.9 |
| EU | sodium | 2,400 | 480 | mg | — | Regulation 1169/2011 |
| EU | sugars | 90 | 18 | g | **total** | Regulation 1169/2011 |
| EU | saturated_fat | 20 | 4 | g | — | Regulation 1169/2011 |
| EU | energy | 2,000 | 400 | kcal | — | Regulation 1169/2011 |
| CODEX | sodium | 2,000 | **400** ★ | mg | — | CAC/GL 2-1985 (NRV-NCD) |
| CODEX | sugars | 50 | 10 | g | **free** | WHO Sugars Guideline |
| CODEX | saturated_fat | 20 | 4 | g | — | CAC/GL 2-1985 (NRV-NCD) |
| CODEX | energy | 2,000 | 400 | kcal | — | WHO Recommendation |

★ CODEX sodium 400 mg/100g 이 3 국 중 가장 엄격하며, 본 연구의 핵심 cross-country 비교 축이다.

12 행 적재는 마이그레이션 스크립트([sql/05_multi_country_migration.sql](../../sql/05_multi_country_migration.sql)) 에서 수행되며, `ON CONFLICT (country_code, nutrient_code) DO UPDATE` 절을 통해 멱등성을 보장한다. `sugar_type` 컬럼(added / total / free) 은 sugars 의 정의가 국가별로 다르다는 표준학적 사실을 데이터 모델에 직접 반영한 것으로, surrogate 비교 시 해석의 단서로 활용된다.

> **방법론적 한계 — sodium 환산 정확도.** EU 의 sodium 일일 기준치(2,400 mg) 는 *소금(salt) 6 g* 을 sodium 환산한 값이다. 정확한 변환 계수는 NaCl 분자량(58.5) 중 Na (23) 의 비율, 즉 0.394 이며, 이를 적용하면 6 g × 0.394 = 2,364 mg 이다. 본 연구는 EU 의 *공식 표시 관행* 인 2,400 mg 을 그대로 채택하였으며, 이는 약 1.5 % 의 정확도 손실을 수반한다. 본 한계가 EU-US 비교 결과 해석에 미치는 영향은 5 장 5.3.3 절에서 다시 다룬다.

> **방법론적 한계 — 100 g 기준 임계값 통일.** FDA 의 공식 "high in" 표시 자격은 1 회 제공량(RACC) 기반이나, 본 연구는 OFF 의 RACC 정보 가용성이 낮아 100 g 기준으로 통일하였다. 따라서 본 연구의 "위반(high)" 판정은 공식 라벨 표시 자격과 정확히 일치하지 않는 *적합성 분포 탐색의 surrogate 지표* 이며, 본 surrogate 지표가 결과 해석에 미치는 영향은 5 장 5.3.3 절에서 다시 다룬다.

## 3.3 ETL 파이프라인

### 3.3.1 데이터 추출 (Extract)

본 연구의 ETL 은 단일 Python 스크립트([etl/load_data.py](../../etl/load_data.py)) 로 구현되며, TRUNCATE + INSERT 의 멱등 적재 패턴을 따른다. 추출 단계는 세 가지 원천 데이터를 결합한다. 첫째, `df_raw.parquet` 은 OFF 한국 식품 약 8,372 건의 원본 행으로, 바코드(`code`) · 다국어 제품명(`product_name`) · 영양소 딕셔너리(`nutriments`) · 카테고리 관련 필드들을 그대로 보유한다. 둘째, `tbt_analysis_result.parquet` 은 1차 프로젝트의 TBT 큐레이션 산출물(제품 코드 단위, 2,493 건) 로서 본 연구의 분석 대상을 정의한다. 셋째, `final_merged_data.parquet` 은 1차 프로젝트의 wide 형식 영양소 데이터로, 본 연구는 *영양소 값 자체* 는 사용하지 않고 카테고리 매핑의 보조 정보로만 활용한다. 추출 단계의 핵심 결정은 *영양소 값을 `df_raw.nutriments` 에서 직접 재추출* 하는 NULL 보존 정책이다(3.1.2 절).

### 3.3.2 데이터 변환 (Transform)

변환 단계는 *4-tier fallback 카테고리 매핑* 과 *영양소 값의 단위 정규화 · 이상치 처리* 의 두 작업으로 구성된다.

**4-tier fallback 카테고리 매핑.** OFF 의 카테고리 메타데이터가 약 85 % 결측인 상황에서 분류율을 최대화하기 위해 본 연구는 4 단계 fallback 절차를 적용한다. 우선 1 단계로 OFF 표준 영문 태그(`categories_tags`) 에 대해 도메인별 키워드 리스트와의 일치 여부를 검사한다(예: `en:dairies` → Dairy, `en:beverages-and-drinks` → Beverages). 매칭이 실패하면 2 단계로 `category_top` 의 약 40 종 표준화/비표준화 표기를 단일 카테고리로 정규화한다(예: `Ko:과자` → Snacks, `Fr:Tteokbokki` → Meals). 3 단계는 자유 텍스트 `categories` 필드의 키워드 매칭(라틴 알파벳 워드 바운더리, 한국어 부분 일치), 4 단계는 `product_name` 의 다국어 dict 텍스트에 대한 키워드 매칭이다. 4 단계 모두 실패하면 `Other` (`category_source = 'other'`) 로 분류한다. 각 단계의 매핑 출처는 `products.category_source` 컬럼(`tags`/`top`/`free`/`name`/`other`) 에 기록되어, 이후 Q8 가설 검증의 그룹 정의(Trusted = `tags` 또는 `top`, Inferred = `name`, Other = `other`) 의 데이터 기반이 된다.

매핑 우선순위는 Dairy → Beverages → Sweets → Meals → Snacks 의 순서이며, 이는 1 차 프로젝트의 분류 빈도 분포와 도메인 지식을 결합한 결정이다. 키워드 충돌이 발생하는 경계 사례(예: "cheese pork cutlet" 의 `cheese` 키워드로 인한 Dairy 오분류) 는 4 장의 정성적 관찰에서 다시 다룬다.

**영양소 단위 정규화 및 이상치 처리.** 단위 정규화는 sodium 의 g → mg 환산(× 1000) 과 energy 의 kJ → kcal 환산(÷ 4.184) 두 가지로 한정된다. 이상치는 음수 값, g/100g 100 초과 값, energy 4,000 kcal/100g 초과 값을 모두 NULL 처리한다(이는 입력 오류 또는 단위 누락의 가능성이 높은 값들이다). 다국어 `product_name` 은 `main → ko → en → 첫 dict 의 text` 의 우선순위로 단일 문자열을 추출하며, 모든 추출 실패 시 `"(no name)"` 으로 적재한다(220 건, 8.8 %).

> **방법론적 한계 — 4-tier 매핑의 잔여 57 % Other.** 4-tier 매핑 후에도 분류 불가능한 1,431 건(57.4 %) 이 `Other` 군으로 남는다. 이는 OFF 한국 식품 메타데이터의 본질적 한계 — 자유 텍스트 입력 비율이 높고 표준 태그 부여가 자원봉사자 기여에 의존한다는 점 — 의 직접적 산물이다. `Other` 군의 잔존이 Q8 가설 검증의 핵심 표본(Trusted vs Other) 자체를 구성하므로, 본 잔여 비율이 단순히 데이터 결함이 아니라 *분석 대상* 임을 강조해 둔다. 본 한계가 결과 해석에 미치는 영향(특히 Q8 결과의 인과 식별 문제) 은 5 장 5.3.2 절과 5.3.3 절에서 다시 다룬다.

### 3.3.3 데이터 적재 (Load)

최종 적재 결과는 `products` 2,493 행, `product_nutrients` 6,589 행(= 9,972 − NULL 3,383) 이며, 카테고리 매핑 출처 분포는 `tags` 152 · `top` 313 · `free` 1 · `name` 596 · `other` 1,431 로 분류율 42.6 % 를 달성한다. 적재는 `TRUNCATE + INSERT` 의 멱등 패턴과 `psycopg2.extras.execute_values` 의 batch INSERT 로 수 초 내 완료된다.

## 3.4 SQL 분석 기법

### 3.4.1 핵심 VIEW 설계 — 듀얼 구조

본 연구의 적합성 진단은 4 개 VIEW 의 듀얼 구조로 구현된다. `v_compliance_results` 는 (제품 × 영양소 × 국가) 단위 19,767 행(= 6,589 × 3 국) 의 다국가 진단 VIEW 이고, `v_compliance_us` 는 그 US 슬라이스인 6,589 행 wrapper VIEW 이다. 같은 방식으로 `v_risk_score` (7,479 행, 다국가) 와 `v_risk_score_us` (2,493 행, US 슬라이스) 도 듀얼로 정의된다. 단일국 wrapper VIEW 들은 Week 3(단일국) 산출물 — Q1 ~ Q8 — 과의 회귀 호환성을 보장하기 위한 backward-compat 계층이며, 신규 다국가 분석(Q9 ~ Q10) 만 본체 다국가 VIEW 를 직접 참조한다.

본 연구의 룰 엔진 핵심은 `v_compliance_results` 의 다음 정의에 응축되어 있다.

```sql
CREATE VIEW v_compliance_results AS
SELECT
    p.product_id, p.category_source,
    pn.nutrient_code, n.nutrient_name_kr, nl.country_code,
    pn.amount_per_100g                                   AS value_per_100g,
    ROUND(pn.amount_per_100g / nl.daily_value * 100, 2)  AS percent_dv,
    CASE
        WHEN pn.amount_per_100g / nl.daily_value * 100 >= 20 THEN 'high'
        WHEN pn.amount_per_100g / nl.daily_value * 100 >= 5  THEN 'moderate'
        ELSE                                                      'low'
    END                                                  AS judgment
FROM       product_nutrients pn
INNER JOIN products          p  ON p.product_id     = pn.product_id
INNER JOIN nutrients         n  ON n.nutrient_code  = pn.nutrient_code
INNER JOIN nutrient_limits   nl ON nl.nutrient_code = pn.nutrient_code
LEFT JOIN  categories        c  ON c.category_id    = p.category_id;
```

위 정의에서 핵심은 세 가지이다. 첫째, `nutrient_limits` 와의 JOIN 에 *국가 필터를 걸지 않으므로* 한 (제품, 영양소) 측정값이 자동으로 3 국 행으로 확장된다 — 이것이 다국가 view 가 단일국 view 의 약 3 배 행 수를 갖는 이유이다. 둘째, `judgment` 컬럼의 3 단계 CASE 식이 21 CFR 101.13 의 5 %/20 % 기준 — `low` (< 5 % DV), `moderate` (5 ~ 20 %), `high` (≥ 20 %, "high in" 표시 자격) — 을 SQL 한 곳에 정형화한다. 셋째, `product_nutrients` 와의 INNER JOIN 으로 인해 결측 (제품, 영양소) 쌍이 자동 제외되어 NULL 보존 정책이 view 수준에서 강제된다(3.1.2 절).

`v_risk_score` 는 위 (제품, 영양소, 국가) 행을 (제품, 국가) 단위로 집계한 뒤, `risk_level = high (high_count ≥ 2) / medium (high_count = 1 ∨ moderate_count ≥ 2) / low / undiagnosed (diagnosed_count = 0)` 의 룰로 종합 위험도를 부여한다. `undiagnosed` 등급은 4 영양소 모두 NULL 인 366 제품을 명시적으로 분리하기 위한 분류이며, NULL 보존 정책의 직접적 산물이다.

### 3.4.2 분석 쿼리 개요 (Q1 ~ Q10)

본 연구는 총 10 개의 분석 쿼리를 작성하였으며, Q1 ~ Q8 은 단일국(US) 분석, Q9 ~ Q10 은 다국가 비교 분석이다. [표 3.2] 는 10 쿼리의 목적과 핵심 SQL 기법을 요약한다.

**[표 3.2] 분석 쿼리 개요**

| # | 목적 | 핵심 SQL 기법 | 대상 |
|---|---|---|---|
| Q1 | 영양소별 · 카테고리별 high 분포 | GROUP BY, FILTER | US |
| Q2 | 카테고리별 위반율 (Other 포함/제외) | GROUP BY, UNION ALL | US |
| Q3 | 3-step CTE 다단계 진단 | WITH CTE, FILTER | US ★ |
| Q4 | 카테고리 내 영양소 함량 RANK top 5 | RANK() OVER PARTITION BY | US |
| Q5 | risk_level 분포 + 등급별 대표 제품 | ROW_NUMBER(), CASE 정렬 | US |
| Q6 | 제품당 high 영양소 개수 분포 | CASE WHEN bucket | US |
| Q7 | 영양소별 결측 비율 + undiagnosed 분포 | LEFT JOIN, IS NULL | US |
| Q8 | Trusted vs Other (가설 검증) | GROUP BY group_name | US ★ |
| Q9 | 국가 × 신뢰그룹 × 영양소 위반율 (36 셀) | GROUP BY country_code | 다국가 ★ |
| Q10 | 동일 제품의 국가별 판정 차이 | WITH CTE, MAX(CASE WHEN) | 다국가 ★ |

★ 본 절에서 SQL 코드 인용

각 쿼리는 [sql/queries/](../../sql/queries/) 폴더에 단일 SQL 파일로 보관되며, 결과 해석은 [docs/results/Q1.md ~ Q10.md](../results/) 에 별도 문서로 정리되어 있다. 본 절에서는 단순 GROUP BY · RANK 계열(Q1·Q2·Q4·Q6) 은 자연어 요약으로 갈음하고, *룰 엔진의 다단계 추론 패턴* 을 보여주는 Q3 와 *다국가 비교의 cross-tab 패턴* 을 보여주는 Q10 의 두 SQL 만 본문에 인용한다.

**Q3 — 3-step CTE 다단계 진단 (룰 엔진 추론 패턴).** Q3 는 적합성 진단을 *영양소 단위 판정 → 제품 단위 집계 → 위험도 분류* 의 3 단계 CTE 로 표현한다. 이는 룰 엔진의 정형적 추론 패턴 — 원자적 판정을 누적하여 종합 분류에 도달하는 — 의 SQL 시연이다.

```sql
WITH violation_check AS (         -- 1) (제품, 영양소) 단위 판정
    SELECT pn.product_id, pn.nutrient_code,
        CASE
            WHEN pn.amount_per_100g / nl.daily_value * 100 >= 20 THEN 'high'
            WHEN pn.amount_per_100g / nl.daily_value * 100 >= 5  THEN 'moderate'
            ELSE                                                      'low'
        END AS judgment
    FROM       product_nutrients pn
    INNER JOIN nutrient_limits   nl ON nl.nutrient_code = pn.nutrient_code
                                    AND nl.country_code = 'US'
),
risk_summary AS (                 -- 2) 제품 단위 카운트 집계
    SELECT product_id,
        COUNT(*) FILTER (WHERE judgment = 'high')      AS high_count,
        COUNT(*) FILTER (WHERE judgment = 'moderate')  AS moderate_count
    FROM violation_check
    GROUP BY product_id
)
SELECT                            -- 3) 위험도 분류 + 분포
    CASE
        WHEN high_count    >= 2  THEN 'high'
        WHEN high_count     = 1
          OR moderate_count >= 2 THEN 'medium'
        ELSE                          'low'
    END                                                AS risk_level,
    COUNT(*)                                           AS product_n
FROM risk_summary GROUP BY risk_level;
```

위 쿼리의 표준학적 의의는 *룰 엔진의 추론 단계가 SQL 의 CTE 단계와 정확히 1:1 대응* 된다는 점이다. 즉 v_risk_score VIEW 가 캡슐화하고 있는 다단계 분류 로직을 본 쿼리는 한 SQL 문 안에 펼쳐서 보여주며, view 의 블랙박스성을 회피하면서도 동일한 결과(진단 2,127 건 중 high 539 · medium 990 · low 598) 를 산출한다.

**Q10 — Cross-country 판정 차이 (다국가 비교 패턴).** Q10 은 같은 (제품, 영양소) 가 3 국에서 받은 judgment 를 cross-tab 으로 펼쳐 *국가별로 다른 판정을 받은 케이스* 를 식별한다. `MAX(CASE WHEN ...)` 패턴은 PostgreSQL 에서 동적 cross-tab 을 구현하는 표준 방법이다.

```sql
WITH per_country AS (             -- 1) 3국 행을 단일 행의 3컬럼으로 펼침
    SELECT product_id, nutrient_code,
        MAX(CASE WHEN country_code = 'US'    THEN judgment END) AS us_j,
        MAX(CASE WHEN country_code = 'EU'    THEN judgment END) AS eu_j,
        MAX(CASE WHEN country_code = 'CODEX' THEN judgment END) AS codex_j
    FROM v_compliance_results
    GROUP BY product_id, nutrient_code
)
SELECT nutrient_code,             -- 2) 영양소별 cross-country gap 집계
    COUNT(*) FILTER (WHERE us_j != codex_j)              AS us_codex_diff,
    COUNT(*) FILTER (WHERE us_j  = 'high'
                       AND codex_j != 'high')            AS us_high_codex_ok,
    COUNT(*) FILTER (WHERE us_j != 'high'
                       AND codex_j  = 'high')            AS us_ok_codex_high
FROM per_country
GROUP BY nutrient_code;
```

`per_country` CTE 는 3 국 행을 단일 행의 3 컬럼으로 펼치는 핵심이며, 이후 집계는 직관적인 `COUNT(*) FILTER (WHERE ...)` 로 표현된다. 본 쿼리의 결과 — sodium 95 케이스가 *US 적합 → CODEX 위반* — 가 4 장의 핵심 발견 중 하나이다. 본 패턴은 한국 식약처 등 새 국가가 추가될 경우 `MAX(CASE WHEN country_code = 'KR' ...)` 한 줄 추가만으로 확장된다.

### 3.4.3 통계 검증 — 비례 z-검정 (SQL + Python 하이브리드)

Q8 의 가설 검증 — *Trusted 그룹과 Other 그룹의 영양소별 위반율 차이가 통계적으로 유의한가* — 은 점 추정치(위반율 차이) 와 변동성(신뢰구간) 의 동시 보고가 필요하므로 SQL 만으로는 수행할 수 없다. 본 연구는 SQL 단계와 Python 단계를 하이브리드로 결합하여 처리한다. SQL 단계에서는 Q8.sql 이 `v_compliance_us × products` JOIN 으로 (group_name, nutrient_code, total_n, high_count, violation_rate) 12 행을 산출하고, Python 단계에서는 [analysis/q8_statistical_test.py](../../analysis/q8_statistical_test.py) 가 이 결과를 받아 8 개 비교쌍(Trusted vs Other × 4 영양소 + Trusted vs Inferred × 4 영양소) 에 대해 `statsmodels.stats.proportion.proportions_ztest` 와 `confint_proportions_2indep` 를 적용한다.

본 연구는 *통계적 유의(p < 0.05)* 와 *실용적 유의(|diff| > 10 pp)* 의 이중 기준을 채택한다. p-value 단독 기준은 표본이 크면 실용적으로 무의미한 차이까지 유의로 판정한다는 한계가 있는 반면, 효과 크기(10 pp) 는 본 연구 4 영양소의 전체 위반율(21 ~ 36 %) 의 약 1/3 에 해당하는 도메인 의미를 갖는 임계이다. 두 기준을 모두 통과해야 *실용 유의* 로 결론한다. 이 기준에 따라 4 비교쌍(Trusted vs Other × 4 영양소) 중 sodium (+10.98 pp, p = 0.003) 과 saturated_fat (−13.50 pp, p = 0.0002) 의 두 영양소만 실용 유의로 판정된다. 8 개 비교의 본페로니 보정(α = 0.05 / 8 = 0.00625) 후에도 sodium · saturated_fat 의 결론은 불변이다.

각 비교에는 Wald 95 % 신뢰구간을 함께 보고하여 점 추정치와 변동성을 동시 표시한다(예: sodium 의 Other − Trusted 차이는 +10.98 pp, 95 % CI [+4.16, +17.81]). 본 절차는 Q9 의 다국가 확장(3 국 × 4 영양소 × 3 그룹 = 36 셀) 에서도 동일하게 적용 가능한 일반화된 통계 분석 파이프라인을 제공한다.
