# FDA 식품 라벨링 표준 기반 제품 적합성 자동 진단 시스템

> 표준학개론 2차 프로젝트 — 관계형 데이터베이스를 활용한 SQL 기반 룰 엔진 설계

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/status-in%20progress-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 프로젝트 개요

- 미국 FDA 식품 영양 표시 규정을 PostgreSQL 관계형 데이터베이스로 정형화
- SQL 쿼리 (JOIN / CASE / CTE / 윈도우 함수)로 한국 식품 **2,493건**의 적합성 자동 진단
- 1차 프로젝트(`synthetic-data-tbt-detection`)의 후속 연구
- **데이터 기반 학습 모델 → 표준 기반 룰 엔진**으로 접근 전환

> 📄 자세한 연구 배경, 방법론, 일정은 [연구 제안서](docs/proposal.pdf)를 참조하세요.

---

## 🔍 핵심 발견 (Week 2 시점)

본 프로젝트의 데이터 정책 설계 및 ETL 과정에서 다음 3가지를 정량적으로 확인하였습니다 ([상세는 Week 2 일지](docs/journal/week2.md) 참조).

1. **Phantom 0 위험 (셀 기준 23.9 %)** — 1차 프로젝트의 0-대치 영양소 컬럼을 그대로 룰 엔진에 사용했을 경우, 결측이 자동으로 "적합" 판정되어 위양성 적합 분류가 발생할 수 있다. 본 프로젝트는 NULL 보존 정책으로 회피.
2. **한국 식품의 카테고리 메타데이터 부재 (~85 % 결측)** — `categories_tags`, `category_top`, `categories` 자유텍스트 모두 결측 비율이 비슷하게 높음. 4-tier fallback 매핑으로 분류율을 10.4 % → **42.6 %** 까지 확장.
3. **카테고리 미분류 식품군의 sodium 위험 집중** — Other 그룹의 sodium 평균(528 mg/100g)이 분류 그룹(366 mg/100g)보다 높고, **FDA 임계값 460 mg 을 이미 초과**. 메타데이터 부재가 영양 위험 정보 가시성의 구조적 격차로 이어짐.

---

## 연구 목적

1. **표준 문서의 데이터베이스 정형화** — FDA 영양소 4종 기준값을 RDB 스키마로 표현
2. **SQL 기반 적합성 진단 엔진 구현** — JOIN, CASE, CTE, 윈도우 함수로 룰 엔진 구성
3. **룰 기반 진단 결과의 표준학적 해석** — 1차 프로젝트의 통계 모델 결과와 비교

---

## 기술 스택

- **DB**: PostgreSQL 18 (Docker 컨테이너)
- **ETL**: Python 3.x (pandas, psycopg2)
- **개발 환경**: VS Code + Claude Code

---

## 분석 대상 영양소 4종 (FDA 기준)

임계값은 모두 Daily Value의 **20% 기준** (100g당).

| 영양소 | Daily Value | 100g 임계값 | 단위 | FDA 주요 영양소 |
|---|---|---|---|:---:|
| 나트륨 (Sodium) | 2,300 | 460 | mg | O |
| 당류 (Sugars) | 50 | 10 | g | O |
| 포화지방 (Saturated Fat) | 20 | 4 | g | O |
| 에너지 (Energy) | 2,000 | 400 | kcal | X |

**선정 근거**

1. **1차 프로젝트 변수 중요도** — `sugars` 0.2086, `energy` 0.1971, `fat` 0.1918
2. **FDA 주요 영양소(Nutrient of Public Health Concern)** — sodium, sugars, saturated_fat 지정

---

## 데이터베이스 설계

### ERD

![ERD](docs/ERD.png)

### 시스템 아키텍처

![Architecture](docs/architecture.png)

---

## 빠른 시작

### 1. PostgreSQL 컨테이너 실행

> ⚠️ `<your-password>` 부분은 본인이 사용할 비밀번호로 변경해주세요.

```bash
docker run -d --name fda-postgres \
  -e POSTGRES_DB=fda_compliance \
  -e POSTGRES_USER=fda_admin \
  -e POSTGRES_PASSWORD=<your-password> \
  -p 5432:5432 \
  postgres:18
```

### 2. 스키마 생성 + 시드 데이터 입력

```powershell
# 스키마 (테이블 6개 + 인덱스 2개)
docker cp sql\01_schema.sql            fda-postgres:/tmp/
docker exec  fda-postgres psql -U fda_admin -d fda_compliance -f /tmp/01_schema.sql

# 카테고리 마스터 (6종)
docker cp sql\02_seed_categories.sql   fda-postgres:/tmp/
docker exec  fda-postgres psql -U fda_admin -d fda_compliance -f /tmp/02_seed_categories.sql

# 영양소 임계값 (4종)
docker cp sql\03_seed_nutrient_limits.sql fda-postgres:/tmp/
docker exec  fda-postgres psql -U fda_admin -d fda_compliance -f /tmp/03_seed_nutrient_limits.sql
```

### 3. 적재 결과 확인

```bash
docker exec fda-postgres psql -U fda_admin -d fda_compliance -c "\dt"
docker exec fda-postgres psql -U fda_admin -d fda_compliance -c "SELECT * FROM nutrient_limits ORDER BY nutrient_code;"
```

---

## 진행 일정 (6주, 2026.05.2주 ~ 2026.06.3주)

| 주차 | 기간 | 작업 내용 | 상태 |
|:---:|---|---|:---:|
| 1주차 | 2026.05.2주 | DB 스키마 설계 · 시드 데이터 입력 · 연구 제안서 | ✅ 완료 |
| 2주차 | 2026.05.3주 | ETL 파이프라인 · 4-tier 카테고리 매핑 · 핵심 발견 3건 | ✅ 완료 |
| 3주차 | 2026.05.4주 | SQL 룰 엔진 구현 (`v_compliance_results`, `v_risk_score`) | ⏳ 진행 예정 |
| 4주차 | 2026.06.1주 | 적합성 진단 결과 분석 (카테고리·영양소별 집계) | ⏳ 예정 |
| 5주차 | 2026.06.2주 | 결과 시각화 + 표준학적 해석 | ⏳ 예정 |
| 6주차 | 2026.06.3주 | 최종 보고서 작성 · 발표 준비 | ⏳ 예정 |

---

## 📅 진행 기록 (Development Journal)

각 주차별 작업 내용, 의사결정, 트러블슈팅을 정리한 진행 일지입니다.

- [Week 1: DB 설계 및 환경 구축](docs/journal/week1.md) ✅
- [Week 2: 데이터 ETL 및 핵심 발견](docs/journal/week2.md) ✅
- Week 3: SQL 쿼리 작성 (예정)
- Week 4: VIEW 구성 및 적합성 진단 (예정)
- Week 5: 분석 및 시각화 (예정)
- Week 6: 보고서 마무리 (예정)

---

## 프로젝트 문서

- [연구 제안서 (Proposal)](docs/proposal.pdf)
- [ERD](docs/ERD.png)
- [시스템 아키텍처](docs/architecture.png)

---

## 작성자

**홍지윤** (Jiyoon Hong)
고려대학교 빅데이터사이언스학부 석사과정
지도교수: 전수영

---

## 라이선스

이 프로젝트는 MIT License 하에 공개됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
