# Week 3 — SQL 분석 및 가설 검증

> **기간**: 2026.05.14 ~ 2026.05.20
> **상태**: ✅ 완료

---

## 목표

- 적합성 진단 VIEW 2개 구축 (`v_compliance_results`, `v_risk_score`)
- 7개 핵심 SQL 쿼리 (Q1 ~ Q7) — 영양소·카테고리·CTE·윈도우 함수 활용
- Q8 신규 — Week 2 발견 3 ("Other 그룹 sodium 위험 집중") 의 통계적 검증
- SQL 단독으로 부족한 부분(z-검정, 신뢰구간)은 Python 하이브리드로 보강

---

## 결과 요약

| 항목 | 값 | 비고 |
|---|---:|---|
| `v_compliance_results` | **6,589 행** | (제품, 영양소) 쌍 단위, NULL 제외 |
| `v_risk_score` | **2,493 행** | 제품 단위, undiagnosed 366건 포함 |
| 쿼리 파일 | 8개 (Q1 ~ Q8) | `sql/queries/` |
| 결과 보고서 | 8개 Markdown + 1 CSV | `docs/results/` |
| 통계 검증 스크립트 | 1개 | `analysis/q8_statistical_test.py` |
| 진단된 제품 | **2,127 건** (전체의 85.3 %) | undiagnosed 366 제외 |
| 다중 위험 제품 (2+ high) | **539 건** (전체의 21.6 %) | risk_level = high |

---

## 핵심 발견 4가지

### 발견 1 — 한국 가공식품의 영양 위험 정량화 (Q1)

진단된 (제품, 영양소) 6,589 쌍 중 **약 1/3 이 FDA Daily Value 20 % 이상** (high 판정):

| 영양소 | high_n | diagnosed_n | high_pct |
|---|---:|---:|---:|
| 포화지방 | 543 | 1,500 | **36.20 %** |
| 당류 | 550 | 1,661 | 33.11 % |
| 나트륨 | 402 | 1,308 | 30.73 % |
| 에너지 | 458 | 2,120 | 21.60 % |

- 포화지방·당류·나트륨이 모두 30 %대 — 한국 가공식품에서 FDA 기준 "고함량(high in)" 표시 대상이 결코 적지 않음
- 에너지가 가장 낮음(21.6 %) — 부피·수분이 많은 식품들이 표본에 다수 포함된 결과로 추정
- 보고서 4.5절 핵심 표로 활용

### 발견 2 — 카테고리별 위험 분포의 비대칭 (Q2)

| category | diagnosed_n | high_n | high_pct |
|---|---:|---:|---:|
| Snacks | 204 | 141 | **69.12 %** |
| Sweets | 382 | 177 | 46.34 % |
| Other | 3,410 | 980 | 28.74 % |
| Dairy | 1,133 | 317 | 27.98 % |
| Beverages | 732 | 170 | 23.22 % |
| Meals | 728 | 168 | 23.08 % |

- Snacks · Sweets 가 압도적으로 위반율 높음 — 도메인 상식과 일치
- **Other 제외 시 전체 비율은 거의 불변** (29.6 % → 30.6 %). 4 영양소 합산 평균에서는 Other 가 별난 그룹이 아님
- 단 표본 크기 차이가 큼 (Snacks 204 vs Other 3,410) — 비율 변동성 주의

### 발견 3 ★ — Q8 가설 검증: 영양소별 차별적 영향

Week 2 발견 3("Other 그룹 sodium 위험 집중") 의 통계적 유의성 검증 (Trusted vs Other, 비례 z-검정 + 95% Wald CI):

| 영양소 | rate_T | rate_O | diff (pp) | p-value | CI 95 % | 판정 (p<0.05 ∧ ∣Δ∣>10pp) |
|---|---:|---:|---:|---:|---|---|
| **sodium** | 25.11 % | **36.10 %** | **−10.98** | **0.0029** | [−17.81, −4.16] | **✓ 가설 지지** |
| **saturated_fat** | **45.70 %** | 32.20 % | **+13.50** | **0.0002** | [+6.15, +20.86] | **✓ 반대 방향 유의** |
| energy | 29.80 % | 20.38 % | +9.41 | 0.0013 | [+3.23, +15.60] | not sig (∣Δ∣<10) |
| sugars | 37.99 % | 31.22 % | +6.77 | 0.0524 | [−0.24, +13.78] | not sig |

**Trusted vs Inferred** (8건 중 4개 영양소) — 4개 모두 not significant.

#### 해석

- **H1 ("Other > Trusted in all 4") 부분 기각**: sodium 만 유의하게 가설 지지. Week 2 의 mean / median 비교(360 vs 136 mg) 가 비율 z-검정으로도 확증됨 (p = 0.003)
- **saturated_fat 은 반대 방향**: Trusted 그룹이 13.5 pp 더 높음. Trusted = Snacks · Sweets · Dairy 편중이라는 그룹 구성의 자연스러운 귀결
- **H2 ("Inferred ≈ Trusted") 지지**: product_name 키워드 매핑(tier 4, +762 건) 이 메타데이터 매핑과 통계적으로 동등하다는 **사후 검증**. Week 2 의사결정 중 가장 비용 효율적이었던 결정의 정량 근거
- **다중 비교 보정 미적용**: 8 비교에 본페로니 보정 시 α = 0.00625. 판정이 바뀌는 케이스는 energy (Trusted vs Other, p = 0.0013) — 보정 시에도 유의. 효과 크기 임계(10 pp) 가 이미 보수적이라 실용적 결론은 불변

### 발견 4 — 메타데이터-영양정보 동시 결손 (Q7)

undiagnosed 366 건 (4 영양소 모두 NULL) 의 그룹 분포:

| category | category_source | product_n |
|---|---|---:|
| Other | other | **283** (77.3 %) |
| Beverages | tags | 28 |
| Beverages | name | 12 |
| Dairy | tags | 7 |
| 그 외 11 그룹 | | 36 |

- 카테고리 정보 미등록(`other`) 과 영양정보 미등록이 **시스템적으로 함께** 발생
- 두 결측이 독립이 아니라 동일한 OFF 등재 부실 패턴의 두 가지 발현임을 시사
- Trusted 그룹에도 undiagnosed 가 일부(예: Beverages tags 28건) 있어 두 문제가 부분 중첩이지 완전 일치는 아님

---

## Framing 업데이트

### Week 2 까지의 가설

> 한국 식품의 카테고리 메타데이터 부재는 영양 위험 정보 가시성의 구조적 격차로 이어진다 (sodium median 2.6배, mean 528 mg > FDA 임계 460).

### Week 3 의 정량 검증 후 정밀화

> 한국 식품 카테고리 메타데이터 부재의 영향은 **영양소별로 차별적**이다. **sodium 에서만 Trusted vs Other 위반율 격차가 통계적으로 유의**하며(+10.98 pp, p=0.003), 이는 메타데이터 표준화의 우선순위가 영양소별로 달라야 함을 시사한다. 다른 영양소(특히 포화지방) 에서는 카테고리 매핑이 잘 된 그룹이 오히려 위반율이 높다 — 이는 잘 분류되는 카테고리(Snacks/Sweets/Dairy) 의 본질적 영양 프로파일을 반영할 뿐, 메타데이터 부재 자체의 영향이 아니다.

### 보고서 활용 framing 후보

> Week 2 에서 "카테고리 미분류 식품군의 sodium 평균이 분류군의 2.6배" 라는 단순 비교를 통해 메타데이터 부재의 영향을 정량화하였다. Week 3 에서는 이 차이가 sodium 한정의 통계적으로 유의한 격차임을 비례 z-검정으로 확증하면서(95% CI: 4.16 ~ 17.81 pp), 동시에 포화지방에서는 정반대 방향의 유의 차이(95% CI: 6.15 ~ 20.86 pp)가 존재함을 발견하였다. 메타데이터 표준화의 우선순위 설계 시, sodium 과 같은 보편 위험 영양소를 별도로 다루어야 함을 시사한다.

---

## 의사결정 로그

### VIEW 임계값 3단계 (FDA 5 % / 20 %) 채택

- `low (<5%DV) / moderate (5-20%) / high (≥20%)`
- 20 % 는 FDA "high in" 표시 기준, 5 % 는 "low in" 기준 (21 CFR 101.13). 두 기준 모두 표준 문서에 명시되어 임의 선택이 아님
- 대안 검토: 이진 분류 (DV 20 % 이상/미만) — 거부. moderate 구간 자체가 보고서 분석 대상 (Q3 medium 등급 = high 1개 OR moderate 2개)
- 임계값을 VIEW DDL 에 직접 박은 것은 SQL 시연 가독성 우선. 본 프로젝트 범위 내 임계값 변경 가능성 낮음

### Q8 신규 — 옵션 C (가설 검증) 선택

- 옵션 A: `category_source` 별 단순 위반 비율 집계 — Week 2 에서 이미 mean / median 으로 비슷한 비교 수행. 추가 가치 낮음
- 옵션 B: KS 검정 또는 t-검정 (연속형 분포 비교) — Week 2 의 mean 비교 연장
- **옵션 C 채택**: 비례 z-검정 — 본 프로젝트의 분석 단위(high 판정 비율) 와 직접 정합. 95 % CI 로 효과 크기까지 함께 제시 가능
- 부산물: H2 ("Inferred ≈ Trusted") 검증을 통해 Week 2 tier 4 (product_name 매핑) 의 정당성을 정량 확인

### 결론 기준: p < 0.05 AND ∣diff∣ > 10 pp

- p-value 단독 기준은 표본이 클 때 실용적 의미 없는 차이도 유의로 판정. 큰 표본에서 효과 크기 기준 병용이 필수
- 10 pp 는 임의 선택이 아닌 도메인 기준: 본 프로젝트의 영양소별 전체 위반율(21~36 %) 의 약 1/3 — "그룹 간 차이가 전체 변동의 1/3 이상" 을 실용 유의 기준으로 설정
- 본페로니 보정 (α=0.00625) 도 별도 확인 — energy / sugars 의 판정만 바뀌고 결론은 불변

### 결과 폴더 구조 결정

- `docs/results/Q*.md` — 사람이 읽기 좋은 결과 + 해석
- `sql/queries/Q*.sql` — 재현 가능한 SQL (해석 없음)
- `analysis/q8_*.py` — SQL 로 표현 불가한 통계 계산
- 한 파일 안에 SQL + 결과 + 해석을 섞지 않은 이유: 향후 SQL 만 재실행하거나 해석만 보고서로 옮길 때 분리되어 있어야 편함

---

## 트러블슈팅

### 1. PostgreSQL ORDER BY 에서 CASE 별칭 참조 불가

- **증상**: Q6 의 `ORDER BY CASE WHEN bucket = '...' THEN 0 END` 에서 `ERROR: column "bucket" does not exist`
- **원인**: PostgreSQL 은 SELECT 의 컬럼 별칭을 ORDER BY 에서 직접 참조 가능하지만, **다른 CASE 식의 입력으로는 사용 불가**. 별칭은 SELECT 평가 후 생기는데 ORDER BY 의 CASE 는 같은 SELECT 평가 단계에 있기 때문
- **해결**: 정렬용 정수 키를 별도 컬럼으로 만들어 CTE 에 포함 (`bucket_order INT`)
- **배운 점**: ORDER BY 에서 SELECT 별칭을 단순 참조하는 것과, 별칭을 다른 식의 입력으로 사용하는 것은 다른 규칙. CTE 로 한 단계 분리하는 것이 가장 안전

### 2. Python 스크립트의 cp949 인코딩 에러

- **증상**: 검증 스크립트 실행 마지막 단계에서 `UnicodeEncodeError: 'cp949' codec can't encode character '✅'`
- **원인**: Windows 한글 cp949 콘솔에서 Python 의 `print()` 가 ✅ / ✓ 같은 유니코드 문자를 인코딩하지 못함. CSV 저장은 명시적 utf-8 로 성공, 콘솔 출력만 실패
- **해결**: 콘솔 출력에서 이모지·체크 문자를 ASCII 대체 (`[saved]`, `[YES]`)
- **배운 점**: Windows + Python 조합에서 비ASCII 콘솔 출력은 환경 변수 `PYTHONIOENCODING=utf-8` 또는 `sys.stdout.reconfigure(encoding='utf-8')` 로도 해결 가능. 다만 본 케이스는 ASCII 대체가 코드 의도(상태 표시) 에 충분히 부합

### 3. `pd.read_sql(psycopg2_conn)` SQLAlchemy 경고

- **증상**: `UserWarning: pandas only supports SQLAlchemy connectable ...`
- **원인**: pandas 2.x 부터 raw DBAPI2 객체 사용 시 경고
- **결정**: 무시. 본 스크립트는 단일 실행 분석용이고 결과 정상. 향후 ETL 코드처럼 반복 호출되는 곳은 SQLAlchemy 로 교체 검토

---

## 정성적 관찰

### Q4 카테고리 매핑 오류 사례

RANK top 5 결과에서 정성 확인된 매핑 오류:

- **Beverages × sodium** top 5 에 "Seasoned Deodeok Roots" (1위, 2497 mg/100g), "Gochujang Korean Hot Red Pepper Paste" (2위, 2440 mg), "AnSungTangMyun Noodle" (4위) — 모두 음료 아님
- **Beverages × energy** top 1: "Hazelnut cappucino" (1956 kcal/100g) 는 분말 형태로, 액상 음료 기준으로는 과대 표시
- **Beverages × saturated_fat** top 3: "Premium Sesame Oil" 16.7 g — 음료가 아님
- **Dairy × sodium** top 1: "Cheese pork cutlet" 3333 mg — 'cheese' 키워드로 Dairy 분류

원인: Week 2 tier 4 (product_name 키워드) 매핑이 단어 단위 매칭이라 "soup" → Beverages, "cheese" → Dairy 식의 오분류 발생. 단어 우선순위 트리(`구체 → 일반`) 가 일부에서 무력화됨.

→ 보고서 한계점(limitations) 섹션에 정량 사례로 활용 가능. 동시에 Q8 결과(Inferred ≈ Trusted, p = 0.28 ~ 0.90) 와 함께 보면, **개별 오분류가 그룹 단위 통계 결론을 흔들 정도는 아님** 을 알 수 있음.

### Q5 의 (no name) 제품

low 등급 대표 5개 중 2개가 "(no name)" — Week 2 의 product_name 추출 9 % 실패 잔여(220건) 의 일부. category_source 도 'other' 라 카테고리 'Other'. 향후 Open Food Facts 신규 덤프로 재적재 시 일부 복구 가능성 있으나 본 프로젝트 범위에서는 그대로 보존.

---

## 학습 노트

### SQL 설계

- **VIEW 재계산 vs 정합성**: VIEW 는 매 실행마다 underlying 테이블에서 재계산되므로 ETL 결과 변경이 즉시 반영됨. Materialized view 는 빠르지만 갱신 시점 관리 부담. 본 프로젝트는 데이터 크기 작아 (6,589 행) VIEW 로 충분
- **`FILTER (WHERE ...)` 절**: `COUNT(*) FILTER (WHERE judgment = 'high')` 는 `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` 와 동등하지만 가독성 우월. PostgreSQL 9.4+ 표준
- **`PARTITION BY` 윈도우 함수**: GROUP BY 와 달리 원본 행 보존하면서 그룹별 순위·집계 가능. Q4 의 RANK 가 전형적 활용
- **CTE 다단계**: Q3 의 3 단계 (violation_check → risk_summary → 최종 SELECT) 가 SQL 한 문장으로 룰 엔진 전체를 표현 — 보고서 시연 자료로 가장 유용
- **ORDER BY 에서의 CASE**: 별칭 참조는 가능하지만 별칭을 다른 식의 입력으로 쓰면 실패. CTE 분리가 안전

### SQL + Python 하이브리드

- SQL 은 집계까지, Python 은 통계 검정·구간 추정. 역할 분리가 명확하면 양쪽 모두 단순해짐
- `pd.read_sql(sql_string, conn)` 으로 SQL 결과 → DataFrame 직접 받기. SQL 파일을 그대로 읽어 실행 가능 → SQL 파일이 단일 진실 원천(single source of truth)
- 통계 검증 라이브러리: `statsmodels.stats.proportion` — `proportions_ztest` (z-검정), `confint_proportions_2indep` (두 비율 차이의 CI). scipy.stats 보다 비례 관련은 statsmodels 가 풍부

### 다중 비교 보정

- 본페로니: α / k. 가장 보수적. 본 프로젝트 8 비교 → α = 0.00625
- Benjamini-Hochberg (FDR): 발견율 통제, 보수성 완화. 탐색적 분석에 더 적합
- 본 프로젝트는 8 비교 중 2 개만 유의여서 보정 후에도 결론 동일. 향후 영양소·카테고리 조합이 늘어나면 BH 적용 검토

---

## Week 3 의 가치

> Week 2 의 발견("Other 그룹 sodium 위험 집중") 을 정량적으로 검증함과 동시에, **단순 일반화를 회피하고 영양소별 차별적 메커니즘을 발견**. sodium 가설 지지(p=0.003), saturated_fat 반대 방향 유의(p=0.0002), 두 영양소는 통계적 차이 없음 — 메타데이터 표준화의 우선순위 설계 근거 제공. 본 프로젝트가 단순 데이터 적재·집계를 넘어 **데이터 기반 발견(data-driven finding)** 을 도출할 수 있음을 입증.

---

## Week 4 계획

### 시각화

- 4 영양소 위반율 비교 차트 (Q1 → 보고서 그림 1)
- 카테고리 × 영양소 위반율 히트맵 (Q1-B → 보고서 그림 2)
- Q8 가설 검증 forest plot 스타일 (그룹 간 위반율 차이 + 95 % CI bar)
- risk_level 분포 도넛 차트 (Q5)

### 보고서 준비

- 4.5 절 (영양소별 위반율) — Q1 결과 표 + 시각화
- 4.6 절 (룰 엔진 SQL 시연) — Q3 의 3-step CTE 그대로
- 4.7 절 (가설 검증) — Q8 결과 + Week 2-3 framing 연결
- 한계점 (Q4 매핑 오류, sodium 47.5 % 결측 등) 도 정량 사례로 정리

### 도구

- `matplotlib`, `seaborn`. 한글 폰트(맑은 고딕) 설정 필요
- 그림 저장: PNG 300 dpi, `docs/figures/` (Week 4 신규 폴더)

---

## 부산물 — Week 3 의 산출물

- `sql/04_views.sql` — VIEW 2 개 정의
- `sql/queries/Q1.sql ~ Q8.sql` — 재현 가능한 SQL
- `analysis/q8_statistical_test.py` — z-검정 + 95 % CI
- `docs/results/Q1.md ~ Q8.md` — 결과 + 해석 보고서
- `docs/results/q8_ztest_results.csv` — 통계 검증 raw 결과
- `docs/results/README.md` — 결과 인덱스
