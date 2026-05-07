# Week 2 — 데이터 ETL 및 핵심 발견

> **기간**: 2026.05.07 ~ 2026.05.13
> **상태**: ✅ 완료

---

## 목표

- Open Food Facts 한국 식품의 PostgreSQL 적재
- 4개 영양소(energy / sugars / saturated_fat / sodium) 추출 및 단위 정규화
- 카테고리 매핑 및 데이터 무결성 검증
- 1차 프로젝트 산출물과의 정합성·차이 정량화

---

## 결과 요약

| 항목 | 값 | 비고 |
|---|---:|---|
| `products` | **2,493 건** | tbt 큐레이션 ∩ df_raw |
| `product_nutrients` | **6,589 건** | 결측·이상치 NULL 처리 후 |
| 카테고리 분류율 | **42.6 %** (1,062 / 2,493) | 4-tier fallback 적용 |
| `Other` 비율 | 57.4 % (1,431) | 1차 시도(89.6 %)에서 32.2 pp 개선 |
| 4개 영양소 NULL 비율 | energy 15.0 % / sugars 33.4 % / saturated_fat 39.8 % / sodium 47.5 % | OFF 원본의 본질적 한계 |
| ETL 코드 | `etl/load_data.py` 단일 진입점 | TRUNCATE + INSERT 멱등 |

---

## 핵심 발견 3가지

### 발견 1 — 1차 프로젝트의 phantom 0 위험 (셀 기준 23.9 %)

1차 프로젝트의 [02_extract_nutrition.py](../../food/02_extract_nutrition.py) 는 영양소 결측을 일괄 `0` 으로 대치한다. 본 프로젝트의 NULL 보존 추출 결과와 비교하면, 1차의 `0` 셀 대다수가 실제로는 결측이었음이 드러난다.

| 영양소 | 1차의 0 행 | 본 NULL 행 | phantom 0 (1차=0 ∩ 본=NULL) |
|---|---:|---:|---:|
| energy | 397 | 373 | **373** |
| sugars | 963 | 832 | **830** |
| saturated_fat | (1차 컬럼 자체 없음) | 993 | — |
| sodium | 1,253 | 1,185 | **1,183** |

- 4개 영양소 합산 phantom 0 셀: **2,386** (4 × 2,493 = 9,972 셀의 23.9 %)
- 1차 프로젝트는 통계 학습 모델을 위한 0-대치가 합리적인 처리였으나, 본 프로젝트의 표준 기반 룰 엔진에서는 NULL 보존 정책이 필요함을 확인하였다. 동일 데이터를 룰 엔진에 그대로 사용했을 경우 phantom 0 이 자동으로 '적합' 판정되어 위양성 적합 분류가 발생할 수 있다.
- 본 프로젝트는 nutriments 원본에서 직접 재추출하여 결측을 NULL 로 보존, 해당 (제품, 영양소) 쌍을 진단 결과에서 제외함으로써 위양성 적합을 구조적으로 회피한다.

**부가 발견**: 1차 프로젝트의 final_merged_data 단계에서 `saturated_fat_100g` 컬럼이 누락되어 있었다 ([merge.py](../../food/merge.py) 가 일부 영양소만 병합). 본 프로젝트는 nutriments 원본에서 saturated_fat 을 직접 추출하여 1,500건의 신규 진단 데이터를 확보하였다.

### 발견 2 — 한국 식품의 카테고리 메타데이터 부재 (~85 % 결측)

세 source 모두 결측 비율이 거의 동일:

| Source | 결측/Unknown 비율 |
|---|---:|
| `categories_tags` (OFF 원본 태그) | **85.1 %** (2,121 / 2,493) |
| `category_top` (1차 큐레이션) | **85.1 %** (2,121 = "Unknown") |
| `categories` (자유텍스트) | **83.8 %** (2,088 / 2,493 결측 또는 빈 문자열) |

→ 어느 한 source 만으로는 50 % 이상 분류 불가. 다만 4-tier fallback 결합으로 분류 가능 행을 1,062 건(42.6 %)까지 확장.

| Tier 누적 | 매핑 행 | 비율 | 추가 기여 |
|---|---:|---:|---:|
| ① `categories_tags` 만 | 266 | 10.7 % | (기준) |
| + ② `category_top` | 300 | 12.0 % | +34 |
| + ③ `categories` 자유텍스트 | 300 | 12.0 % | **+0** |
| + ④ `product_name` | **1,062** | **42.6 %** | **+762** |

- tier 4 (product_name) 가 압도적 기여 — `product_name = ndarray of {lang, text}` 구조를 다국어 모두 합쳐 키워드 매칭
- tier 3 (categories 자유텍스트) 는 0 건 — `categories_tags` 비결측 행과 거의 완전 중복. 향후 제거 가능하지만 보존 비용이 낮아 유지

**표준학적 시사점**: 한국 식품의 OFF 등재 시 메타데이터 표준(특히 IFCSF 카테고리 트리) 적용이 미흡함을 정량적으로 확인. 1차 프로젝트가 분류 모델 학습을 위해 `category_top` 컬럼을 직접 활용했음에도 Unknown 85 % 였다는 사실은, 이 문제가 단일 데이터셋이 아닌 **국제 식품 데이터베이스 등재 관행 자체의 구조적 격차**임을 시사한다.

### 발견 3 — 카테고리 미분류 식품군의 sodium 위험 집중 ★

분류된 1,062건과 미분류(Other) 1,431건의 영양소 분포를 SQL 로 직접 비교:

| 영양소 | 그룹 | n | median | mean | FDA 임계값 |
|---|---|---:|---:|---:|---:|
| **sodium (mg/100g)** | 분류 | 657 | **136** | 366 | 460 |
|  | **Other** | 651 | **360** | **528** | 460 |
| energy (kcal/100g) | 분류 | 977 | 179 | 239 | 400 |
|  | Other | 1,143 | 210 | 250 | 400 |
| sugars (g/100g) | 분류 | 809 | 6.0 | 10.6 | 10 |
|  | Other | 852 | 5.0 | 9.3 | 10 |
| saturated_fat (g/100g) | 분류 | 736 | 2.3 | 4.9 | 4 |
|  | Other | 764 | 1.7 | 3.6 | 4 |

- Other 그룹 sodium **median 360 mg** = 분류 그룹(136 mg)의 **2.6배**
- Other 그룹 sodium **mean 528 mg** > **FDA 임계값 460 mg** — 즉 Other 그룹은 평균적으로 이미 위반 상태
- 다른 세 영양소는 두 그룹 간 큰 차이 없음 → **sodium 만의 특수성**

**보고서 framing 후보 1**

> OFF 한국 식품 2,493건 중 categories_tags 비결측은 14.9 %(372건)에 그쳤다. 본 연구는 categories_tags / category_top / categories 자유텍스트 / product_name 의 4단계 fallback 매핑을 통해 시드 6개 카테고리로 분류 가능한 행을 1,062건(42.6 %)까지 확장했으나, 여전히 1,431건(57.4 %)이 분류 불가(Other)로 남았다. 이는 1차 프로젝트의 분류 모델이 직접 활용한 category_top 컬럼에서 'Unknown' 비율이 85.1 % 였던 것과 일관되며, 한국 식품의 국제 데이터베이스 등재 시 메타데이터 표준화 부족이 주요 요인 중 하나로 파악된다.

**보고서 framing 후보 2**

> 분류 그룹과 Other 그룹의 sodium 함량 분포를 비교하면, Other 그룹의 median 은 360 mg/100g 으로 분류 그룹(136 mg/100g)의 2.6배에 달하며, 평균값(528 mg/100g)은 FDA 임계값(460 mg/100g)을 이미 초과한다. 즉 카테고리 정보가 부재한 식품군에 오히려 영양 위험이 집중되어 있어, 메타데이터 표준화 부재가 단순한 데이터 품질 문제를 넘어 소비자 영양 위험 정보 가시성의 구조적 격차로 이어진다.

---

## 버그 발견 · 수정

### `product_name` = ndarray of dicts (다국어 라벨)

- **증상**: 1차 적재 후 DB의 모든 행이 `product_name = '(no name)'` 로 들어감
- **원인**: OFF parquet 의 `product_name` 컬럼은 `ndarray([{lang, text}, ...])` 구조의 다국어 라벨 모음. 적재 코드가 `isinstance(name, str)` 만 체크하여 모든 행을 거부 → fallback `(no name)` 으로 일괄 대치
- **해결**: `extract_name(arr)` 함수 추가 — `lang` 우선순위 `main → ko → en → 첫 dict → "(no name)"`. 카테고리 매핑 tier 4 에서는 모든 dict 의 text 를 합친 `name_blob` 으로 다국어 키워드 동시 매칭
- **효과**:
  - product_name 정상 추출 91.2 % (2,273 / 2,493)
  - tier 4 카테고리 매핑 762 건 추가 → 전체 분류율 10.7 % → 42.6 %
- **배운 점**: 외부 데이터의 컬럼 자료형은 단순 `str` 로 가정하지 않는다. parquet/struct 컬럼은 ndarray·dict 가 흔하므로, `type(sample).__name__` 사전 검증을 ETL 표준 절차로 둔다.

---

## 부수 검증

### sodium unit 정규화 검증

OFF nutriments 의 `unit` 필드가 `g` / `mg` / `µg` 로 혼재되어 단위 변환 정확도를 검증:

| unit | n | min | median | p95 | max |
|---|---:|---:|---:|---:|---:|
| g | 1,265 | 0 | **0.278** | 1.456 | 695.6 |
| mg | 44 | 0 | **0.169** | 0.832 | 1.66 |
| µg | 1 | 0.0002 | 0.0002 | 0.0002 | 0.0002 |

- unit=g 와 unit=mg 의 100g 값 분포가 거의 동일 (median 0.278 vs 0.169) → **OFF 가 100g 필드를 g 단위로 사전 정규화**한 것을 확인. unit 필드는 사용자 입력 표시용
- **결정적 확증**: sodium / salt 비율 median **0.4000** (n=1,240) — NaCl→Na 환산 이론값 0.394 와 정확히 일치. 두 영양소가 일관된 g 단위로 저장되었다는 화학적 일관성 증거
- **정성 검증**: unit=mg 인 `Shin Ramyun (신라면)` 의 `100g=1.49 g` → ×1000 = **1,490 mg/100g**. 신라면 영양표시 라벨의 sodium 함량과 일치
- **결론**: 모든 sodium 행 ×1000 로 일괄 변환하는 현재 로직 유지. unit 필드 분기 불필요

### sodium 47.5 % 결측의 원인 — salt fallback은 무용

| 케이스 | 행 수 |
|---|---:|
| sodium 만 가용 | 0 |
| salt 만 가용 | **0** |
| 둘 다 가용 | 1,310 |
| 둘 다 결측 | 1,183 |

- OFF 입력 시 sodium 과 salt 가 자동으로 짝으로 채워지거나 짝으로 비어있음 → `salt × 0.4 → sodium` fallback 적용 가능 행이 0건
- sodium 47.5 % 결측은 OFF 원본 자체의 한계이며 추가 추출 로직으로 줄일 수 없음

---

## ETL 진화 과정 (수치로 보는 개선)

### v1 — 단일 매핑 (categories_tags 만)
- 카테고리 분류율: **258 건** (10.4 %)
- product_name 적재: 0 건 정상 (전부 `(no name)` 버그)

### v2 — 4-tier fallback + product_name 버그 수정
- 카테고리 분류율: **1,062 건** (42.6 %) — × 4.1배
- product_name 적재: 2,273 건 정상 (91.2 %)

### tier 별 누적 기여 분석

| 누적 단계 | 매핑 행 | 비율 | 추가 기여 |
|---|---:|---:|---:|
| ① `tags` 만 | 266 | 10.7 % | (기준선) |
| + ② `category_top` | 300 | 12.0 % | +34 |
| + ③ `categories` 자유텍스트 | 300 | 12.0 % | **+0** |
| + ④ `product_name` | **1,062** | **42.6 %** | **+762** |

- tier 4 (product_name) 가 단일 최대 기여 — 762 건
- tier 3 (categories 자유텍스트) 는 현재 0 건 추가. tier 1 비결측 행과 거의 완전 중복

---

## 의사결정 로그

### `category_source` 컬럼 추가 결정

- **추가 이유**: 매핑 출처별 신뢰도 추적 가능 (`tags` > `top` > `free` > `name` > `other`)
- **활용 1**: Week 3 분석에서 `WHERE category_source != 'other'` 로 신뢰 그룹만 분리 가능
- **활용 2**: Q8 신규 분석 — `category_source` 별 위반 비율 비교 (low confidence 매핑이 분석 결과에 영향을 주는지)
- **대안 검토**: VIEW 에서 매번 계산 — 거부. ETL 시점 결정값을 물리 컬럼으로 보존하는 편이 재현성·디버깅 모두 유리

### tier 3 (`categories` 자유텍스트) 유지 결정

- 현재 0 건 기여. 제거하면 코드 단순화 가능
- 그러나: 향후 OFF 가 `categories_tags` 만 결측인 행에 자유텍스트만 채울 가능성 있음
- 제거 비용은 낮지만 보존 비용도 낮으므로 **유지**. 차후 1년 이상 0 건이면 재검토

### schema 변경: ALTER TABLE IF NOT EXISTS

- products 테이블만 DROP/CREATE 시 `product_nutrients` 의 FK 도 함께 사라짐 → FK 복구 필요
- ALTER TABLE 은 데이터·FK 모두 보존하면서 컬럼만 추가 → 더 안전
- ETL 스크립트 첫 단계에서 `ALTER ... IF NOT EXISTS` 로 보장 → 멱등 마이그레이션

---

## 학습 노트

### 데이터 처리

- `nutriments` 같은 struct 컬럼은 parquet → pandas 시 `ndarray of dicts` 로 들어옴. 단순 `dict.get(key)` 가 아니라 ndarray 순회 후 `name` 필드 매칭 필요
- 다국어 메타데이터의 우선순위 설계 — `main → ko → en → first` 패턴은 OFF 외에도 일반적
- 키워드 매칭의 우선순위 = 구체 → 일반. "Strawberry Yogurt" 의 `yogurt` 가 (Snacks 의 `cookie` 에 우선해) Dairy 로 매핑되는 식

### ETL 검증 방법

- **도메인 지식 활용**: NaCl→Na 환산 0.394 를 단위 검증 기준으로 사용
- **외부 라벨과 대조**: 신라면 sodium 1,490 mg/100g 는 시판 영양표시와 일치 → 단위 변환 로직 정성 검증
- **정량 단순 통계 + 정성 표본 점검** 을 항상 함께 — 단위 분포 비교 + 실제 행 샘플 출력

### 데이터베이스 설계

- **물리 컬럼 vs VIEW 계산**: 결정값(매핑 source 등) 은 물리 컬럼으로. 파생값(적합성 결과 등) 은 VIEW
- **TRUNCATE + INSERT 패턴**: ETL 멱등성 + 자동 ID 재할당. ON CONFLICT 보다 단순
- **`ALTER TABLE IF NOT EXISTS`**: 운영 중 마이그레이션. FK·데이터·인덱스 모두 보존

---

## Week 3 계획

### 기존 7개 SQL

- [ ] `v_compliance_results` VIEW — 4개 영양소별 임계값 초과 여부
- [ ] `v_risk_score` VIEW — 위반 영양소 수·정도 가중 점수
- [ ] **Q1**: 영양소별 전체 위반 비율
- [ ] **Q2**: 카테고리별 위반 비율 — 신뢰 그룹(`category_source != 'other'`) vs 전체 비교
- [ ] **Q3**: 위반 영양소 조합 패턴 (4 영양소의 16개 조합 분포)
- [ ] **Q4**: 카테고리 내 함량 순위 (윈도우 함수 RANK / NTILE)
- [ ] **Q7**: NULL 탐지 — Week 2 발견 패턴(phantom 0, OFF 결측)을 SQL 로 재확인

### Q8 신규 (Week 2 발견 활용)

- [ ] **Q8**: `category_source` 별 위반 비율 — 분류 신뢰도와 영양 위험의 상관관계 검증
- [ ] **Q8-1**: "sodium 위험은 미분류군에 집중" 가설을 SQL 로 검증 (median + KS 검정 수준)

---

## 부산물 — Week 2 의 데이터 자산

- `data/raw/df_raw.parquet` — 한국 식품 8,372 건 1차 추출본 (gitignore)
- `etl/extract_korean_products.py` — food.parquet 에서 한국 제품 재추출 (재현용)
- `etl/explore_data.py` — 데이터 탐색 보조 (nutriments 구조 파악용)
- `etl/load_data.py` — ETL 메인 (4-tier 카테고리 + 검증 통계 통합)
- `.env.example` — DB 자격증명 템플릿 (`.env` 는 gitignore)

---

## 결론

> Week 2 의 가치는 단순한 데이터 적재가 아니라, 룰 기반 진단 시스템을 위한 데이터 정책을 설계하고, 그 과정에서 한국 식품 데이터의 구조적 특성을 정량적으로 발견한 것에 있다.
