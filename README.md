# 다국가 적합성 비교 진단 시스템 (FDA · EU · CODEX)

> 표준학개론 2차 프로젝트 — 관계형 데이터베이스를 활용한 SQL 기반 룰 엔진 + 국제 표준 비교

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/status-in%20progress-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 프로젝트 개요

- **3개 국제 표준** (FDA · EU · CODEX) 영양 표시 규정을 PostgreSQL 관계형 데이터베이스로 정형화
- SQL 쿼리 (JOIN / CASE / CTE / 윈도우 함수)로 한국 식품 **2,493건**의 국가별 적합성을 비교 진단
- 1차 프로젝트(`synthetic-data-tbt-detection`)의 후속 연구 — 데이터 기반 학습 모델 → **표준 기반 룰 엔진**
- 단일국(FDA) 분석으로 시작해 Week 4부터 EU·CODEX 비교 확장

> 📄 자세한 연구 배경·방법론·일정은 [연구 제안서](docs/proposal.pdf) 참조.

---

## 🔍 핵심 발견 (Week 3 시점, 단일국 예비 결과)

본 프로젝트의 ETL · SQL 분석 · 통계 검증을 통해 다음 4가지를 정량적으로 확인하였습니다 ([Week 2](docs/journal/week2.md) · [Week 3](docs/journal/week3.md) 일지 참조).

1. **Phantom 0 위험 (셀 기준 23.9 %)** — 1차 프로젝트의 0-대치 영양소 컬럼을 그대로 룰 엔진에 사용했을 경우, 결측이 자동으로 "적합" 판정되어 위양성 적합 분류가 발생할 수 있다. 본 프로젝트는 NULL 보존 정책으로 회피.
2. **한국 식품의 카테고리 메타데이터 부재 (~85 % 결측)** — `categories_tags`, `category_top`, `categories` 자유텍스트 모두 결측 비율이 비슷하게 높음. 4-tier fallback 매핑으로 분류율을 10.4 % → **42.6 %** 까지 확장.
3. **한국 가공식품의 영양 위험 정량화** — 진단된 (제품, 영양소) 6,589 쌍 중 약 1/3 이 FDA DV 20 % 이상. 포화지방 36.2 % / 당류 33.1 % / 나트륨 30.7 % / 에너지 21.6 %.
4. **메타데이터 부재의 영양소별 차별적 영향 ★** — Week 2에서 발견한 *"Other 그룹의 sodium 평균이 FDA 임계값 초과(528 vs 460 mg/100g)"* 패턴을 통계적으로 검증. **sodium에서만** Trusted vs Other 위반율 격차 유의 (+10.98pp, p=0.003). 반면 포화지방은 정반대 방향으로 유의 (Trusted 그룹 +13.50pp 더 높음, p=0.0002) — 카테고리 분류 자체가 *Snacks/Sweets/Dairy 등 고지방 식품군에 편향*되어 있음을 시사. 메타데이터 표준화의 우선순위가 영양소별로 달라야 함을 보여줌.

→ Week 4 부터 EU · CODEX 임계값과의 **국가별 적합성 비교**(Q9 · Q10)로 확장.

---

## 연구 목적

1. **다국가 표준 문서의 데이터베이스 정형화** — FDA · EU · CODEX 영양소 4종 기준값을 단일 스키마로 표현
2. **SQL 기반 적합성 진단 엔진 구현** — JOIN, CASE, CTE, 윈도우 함수, Nutri-Score 산식
3. **국가별 진단 결과 비교** — 한국 식품의 같은 데이터에 3개국 기준 적용 시 적합성 차이 정량화
4. **표준학적 해석** — 1차 프로젝트의 통계 모델과 비교 + 국가별 표준 격차의 무역·소비자 정보 함의

---

## 기술 스택

- **DB**: PostgreSQL 18 (Docker 컨테이너)
- **ETL**: Python 3.x (pandas, psycopg2)
- **통계 검증**: statsmodels (proportions z-test, Wald CI)
- **개발 환경**: VS Code + Claude Code

---

## 분석 대상 영양소 4종 — 국가별 임계값 (100g 기준 high 분류)

| 영양소 | FDA (DV 20 %) | EU / UK Traffic Light 'red' | CODEX (Nutrition Claim) | 단위 |
|---|---:|---:|---:|---|
| 나트륨 (Sodium) | **460** | 600 (salt 1.5 g 환산) | 600 | mg/100g |
| 당류 (Sugars) | **10** | 22.5 (총당류) | 15 (시드값) | g/100g |
| 포화지방 (Saturated Fat) | **4** | 5 | 5 | g/100g |
| 에너지 (Energy) | **400** | — (직접 임계 없음) | — | kcal/100g |

> ⚠️ EU·CODEX 수치는 일반 인용 기준값. **확정 시드값은 새 proposal 과 대조 후 `sql/03_seed_nutrient_limits.sql` 갱신 예정** (Week 4).

### nutrient_limits 다국가 구조 (Week 4 마이그레이션 예정)

기존 단일 PK `(nutrient_code)` → 복합 PK `(country_code, nutrient_code)` 로 확장.

```sql
CREATE TABLE nutrient_limits (
    country_code         VARCHAR(10)  NOT NULL,     -- 'FDA' / 'EU' / 'CODEX'
    nutrient_code        VARCHAR(30)  NOT NULL,
    nutrient_name_kr     VARCHAR(50)  NOT NULL,
    unit                 VARCHAR(10)  NOT NULL,
    daily_value          NUMERIC(10,2),             -- 국가별 RI/DV (있을 때만)
    high_threshold_100g  NUMERIC(10,2) NOT NULL,
    source_document      VARCHAR(100),              -- e.g. 'FDA 21 CFR 101.13'
    PRIMARY KEY (country_code, nutrient_code)
);
```

`v_compliance_results` VIEW 는 `country_code` 별 별도 VIEW (`v_compliance_fda`, `v_compliance_eu`, `v_compliance_codex`) 로 분리 또는 파라미터 함수화 검토.

**선정 근거**

1. **1차 프로젝트 변수 중요도** — `sugars` 0.2086, `energy` 0.1971, `fat` 0.1918
2. **FDA 주요 영양소(Nutrient of Public Health Concern)** — sodium, sugars, saturated_fat 지정
3. **국제 표준 비교 가능성** — 4 영양소 모두 EU(Reg. 1169/2011) · CODEX(CXG 23-1997) 에 대응 기준 존재

---

## 데이터베이스 설계

### ERD

![ERD](docs/ERD.png)

> ERD 는 Week 1 단일국 버전. Week 4 마이그레이션 후 다국가 버전 추가 예정.

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

## 진행 일정 (8주, 2026.05.2주 ~ 2026.07.1주)

| 주차 | 기간 | 작업 내용 | 상태 |
|:---:|---|---|:---:|
| 1주차 | 2026.05.2주 | DB 스키마 설계 · 시드 데이터 입력 · 연구 제안서 | ✅ 완료 |
| 2주차 | 2026.05.3주 | ETL 파이프라인 · 4-tier 카테고리 매핑 · 핵심 발견 3건 | ✅ 완료 |
| 3주차 | 2026.05.4주 | SQL 룰 엔진 + 8개 쿼리 + Q8 가설 검증 (z-test) | ✅ 완료 |
| 4주차 | 2026.06.1주 | **`nutrient_limits` 다국가 확장 + Nutri-Score 산식 SQL + Q9·Q10** | ⏳ 예정 |
| 5주차 | 2026.06.2주 | 국가별 적합성 비교 분석 + 시각화 | ⏳ 예정 |
| 6주차 | 2026.06.3주 | 표준학적 해석 + 보고서 4.7 절 (단일국 예비) 마무리 | ⏳ 예정 |
| 7주차 | 2026.06.4주 | 다국가 비교 결과 정리 + 발표자료 1차 | ⏳ 예정 |
| 8주차 | 2026.07.1주 | 최종 보고서 작성 · 발표 준비 | ⏳ 예정 |

---

## 📅 진행 기록 (Development Journal)

각 주차별 작업 내용, 의사결정, 트러블슈팅을 정리한 진행 일지입니다.

- [Week 1: DB 설계 및 환경 구축](docs/journal/week1.md) ✅
- [Week 2: 데이터 ETL 및 핵심 발견](docs/journal/week2.md) ✅
- [Week 3: SQL 분석 및 가설 검증](docs/journal/week3.md) ✅
- Week 4: 다국가 확장 + Nutri-Score (예정)
- Week 5: 국가별 비교 분석 (예정)
- Week 6: 표준학적 해석 (예정)
- Week 7: 다국가 비교 정리 (예정)
- Week 8: 최종 보고서 (예정)

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
