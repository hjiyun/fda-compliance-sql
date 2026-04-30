# 표준학개론 2차 프로젝트

## 프로젝트 개요

FDA 식품 라벨링 표준을 PostgreSQL DB로 정형화하고, SQL 룰 엔진으로 한국 식품 2,493건의 적합성을 자동 진단하는 시스템 구축.

- **기간**: 2026년 5월 2주 ~ 6월 3주 (총 6주)
- **데이터 출처**: Open Food Facts 한국 식품 2,493건 (1차 프로젝트와 동일 데이터)

## 기술 스택

- **DB**: PostgreSQL 18 (Docker 컨테이너 `fda-postgres`에서 실행 중)
  - DB명: `fda_compliance`
  - 사용자: `fda_admin`
  - 비밀번호: `<local-dev-password>` (로컬 개발용, 공개 레포에는 노출하지 않음)
- **ETL**: Python (pandas, psycopg2) — 2주차 진행 예정

## 분석 대상 영양소 4종

임계값은 모두 Daily Value의 20% 기준 (100g당).

| 영양소 | 영문 키 | Daily Value | 100g 임계값 |
|---|---|---|---|
| 나트륨 | `sodium` | 2300 mg | 460 mg |
| 당류 | `sugars` | 50 g | 10 g |
| 포화지방 | `saturated_fat` | 20 g | 4 g |
| 에너지 | `energy` | 2000 kcal | 400 kcal |

## 테이블 구조 (확정)

### 필수 테이블 (4개)
- `categories` — 식품 카테고리
- `products` — 제품 마스터
- `nutrient_limits` — 영양소 임계값 기준
- `product_nutrients` — 제품별 영양소 함량

### 선택 확장 테이블 (2개)
- `allergens` — 알레르기 유발 성분
- `product_allergens` — 제품-알레르기 매핑

### VIEW (2개 예정)
- `v_compliance_results` — 적합성 진단 결과
- `v_risk_score` — 위험 점수 산출

## 작업 시 참고 사항

- 영양소 키와 임계값을 변경할 때는 `nutrient_limits` 테이블과 본 문서를 함께 갱신할 것.
- 1차 프로젝트와 동일한 Open Food Facts 데이터셋을 재사용하므로 데이터 정합성 비교 시 1차 산출물을 참조 가능.
