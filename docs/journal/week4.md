# Week 4 — 다국가 표준 확장 (US + EU + CODEX)

> **기간**: 2026.05.21 ~ 2026.05.27
> **상태**: ✅ 완료

---

## 목표

- 단일국 (US, 21 CFR 101.9) 기반 진단을 EU (Regulation 1169/2011) 와 CODEX (CAC/GL 2-1985 + WHO) 로 확장
- 스키마 정규화: `nutrients` (정체성) + `nutrient_limits` (국가별 표준값) 분리
- VIEW 듀얼 구조 도입 (다국가 진단 + Week 3 호환 US 슬라이스)
- Q9 — Q8 가설을 3국으로 확장하여 표준 강도와 메타데이터 부재 효과의 상호작용 검증
- Q10 — 동일 제품의 국가별 판정 차이 (cross-country compliance gap) 정량화

---

## 결과 요약

| 항목 | 값 | 비고 |
|---|---:|---|
| `nutrients` (신설) | 4 행 | 영양소 정체성 (국가 무관) |
| `nutrient_limits` (재구조화) | 12 행 | US 4 + EU 4 + CODEX 4. PK = (country_code, nutrient_code) |
| `v_compliance_results` (다국가) | **19,767 행** | 6,589 × 3 |
| `v_compliance_us` (US 슬라이스) | 6,589 행 | Week 3 동일 (회귀 보장) |
| `v_risk_score` (다국가, 옵션 A) | **7,479 행** | (제품, 국가) 단위 — 2,493 × 3 |
| `v_risk_score_us` (US 슬라이스) | 2,493 행 | Week 3 동일 |
| 쿼리 파일 | 10 개 (Q1 ~ Q10) | 신규 Q9·Q10 |
| 결과 보고서 | 10 개 + 1 CSV | docs/results/ |
| Q8 회귀 검증 | 4 영양소 격차 (pp) 4/4 정확 일치 | sodium +10.98 / sat_fat −13.50 / energy −9.42 / sugars −6.77 |

---

## 핵심 발견 5가지

### 발견 1 ★ — sodium Other-Trusted gap 의 단조 확대 (Q9)

표준이 엄격해질수록 메타데이터 부재로 인한 sodium 진단 격차가 커진다:

| 국가 | sodium 임계값 (mg/100g) | Other 위반율 | Trusted 위반율 | gap (pp) |
|---|---:|---:|---:|---:|
| EU | 480 | 33.49 | 24.20 | +9.29 |
| US | 460 | 36.10 | 25.11 | +10.98 |
| CODEX | **400** | **45.31** | 31.51 | **+13.80** |

Week 3 Q8 의 "Other 그룹 sodium 위험 집중" 가설을 다국가로 확장한 결과, gap 의 크기가 임계값 엄격도와 단조 비례. **공중보건상 더 엄격한 표준일수록 메타데이터 표준화 우선순위가 더 중요**해진다는 함의.

### 발견 2 ★ — sodium 95 케이스 "FDA 적합 → CODEX 위반" (Q10)

한국 가공식품 1,308 sodium 측정 중 **95 건 (7.3 %)** 이 FDA(US) 기준 적합이지만 CODEX 기준 위반. 그중 상당수가 정확히 400 mg/100g 클러스터:

- Kimchi Buldak Dumpling / Chicken Tender / Special K 오리지널 / Crispy Chicken Breasts / 마포식 차돌된장찌개 / Pork Cutlet / Half And Half Hotdog / 버터 와규 주먹밥 …

→ **한국 가공식품 sodium 함량의 산업 표준점이 CODEX 임계값과 정확히 일치**. 임의의 영양 표준 선택이 진단 결과를 의미 있게 변화시키는 정량 사례.

비대칭: `us_high_codex_ok = 0` — CODEX 는 US 적합을 뒤집을 수 있지만 그 반대는 없음. 표준 엄격도 ranking CODEX > US > EU 가 한국 식품 분포에서도 일관 유지.

### 발견 3 — saturated_fat / energy 는 cross-country 차이 0 (Q10)

3국 임계값이 동일 (sat_fat 4 g, energy 400 kcal) 한 자연스러운 귀결. 보고서·발표에서 "cross-country 분석 가치가 있는 영양소는 sodium 과 sugars 두 가지" 로 framing 가능.

### 발견 4 — sugars 의 EU 외형 느슨 + surrogate 주의 (Q9·Q10)

EU sugars 임계값 18 g/100g (US/CODEX 의 10g 대비 80% 느슨) 때문에 EU 위반률이 다른 두 국가의 약 절반 수준:
- Trusted: US/CODEX 37.99 → EU 23.58
- Other: US/CODEX 31.22 → EU 17.61

판정 차이 510 케이스가 모두 "EU vs (US=CODEX)" 패턴이고 3국이 모두 다른 케이스는 0:
- 254 케이스: US/CODEX high, EU moderate (10–18g 구간)
- 256 케이스: US/CODEX moderate, EU low (2.5–4.5g 구간)

단 **OFF 의 sugars-100g 는 total sugars 기준** 이므로 EU (Regulation 1169/2011 — total) 만 정의 정합. US (added) / CODEX (free) 는 surrogate 비교. 보고서에서 sugars cross-country 결과 인용 시 반드시 명시.

### 발견 5 — 3국 all-different 케이스는 어느 영양소에서도 0 (Q10)

sodium 의 3국 임계값이 다 다르고 (400/460/480) 한국 식품의 sodium 분포가 넓음에도, 동일 측정값이 세 가지 다른 judgment 를 받는 케이스는 0. **임계값이 살짝 다르다고 해서 모든 단계가 갈리는 일은 발생하지 않음** — judgment 가 한 단계씩만 점프.

---

## Framing 업데이트

### Week 3 까지의 framing

> 한국 식품 카테고리 메타데이터 부재의 영향은 영양소별로 차별적이다. sodium 에서만 Trusted vs Other 위반율 격차가 통계적으로 유의(+10.98 pp, p=0.003)하며, 이는 메타데이터 표준화의 우선순위가 영양소별로 달라야 함을 시사한다.

### Week 4 의 정밀화

> 한국 식품 카테고리 메타데이터 부재가 sodium 진단 가시성을 떨어뜨리는 효과는, 적용하는 영양 표준이 엄격할수록 더 두드러진다 (EU 480 mg: +9.29 pp → US 460 mg: +10.98 pp → CODEX 400 mg: +13.80 pp). 즉 본 프로젝트의 발견은 단일 표준 의존이 아닌 **표준 강도 × 메타데이터 부재의 상호작용** 으로 일반화된다. 또한 한국 가공식품 1,308 sodium 측정 중 95 건이 FDA 기준 적합이지만 CODEX 기준 위반이며, 그중 다수가 정확히 400 mg/100g — **CODEX 임계값과 한국 식품 산업의 sodium 표준점이 일치**하는 정량 사례를 확인.

---

## 의사결정 로그

### 마이그레이션 옵션 B (정규화) 채택

- 옵션 A (인라인 country_code 추가, 정체성 컬럼 중복): 빠르지만 nutrient_name_kr 등 4개 컬럼이 3국에 중복 저장됨
- **옵션 B 채택**: `nutrients` 테이블 분리 + `nutrient_limits` 는 (country, nutrient) PK + 국가별 표준값만
- 이유: 정체성 정보(이름·단위·is_public_concern)는 국가 무관이므로 1 NF 위반 회피. 본 프로젝트 범위 작아 성능 차이는 무시 가능. 표준학개론 과목 맥락에서 "정규화가 표준 진단 시스템의 기본" 이라는 메시지도 산출 가치 있음.
- 비용: VIEW 와 Q-쿼리 일부가 nutrients JOIN 또는 driver 교체 필요 → Q7-A 한 곳만 영향

### v_risk_score 다국가 집계 — 옵션 A (제품 × 국가)

- 옵션 A: (제품, 국가) 단위 — 7,479 행. 같은 제품이 국가별로 다른 risk_level 가능
- 옵션 B: 제품 단위 (모든 국가 합산) — 2,493 행. 국가 분리 불가
- **옵션 A 채택**: Q10 (동일 제품의 국가별 판정 차이) 의 토대로 필수. v_risk_score_us = WHERE country_code='US' → 2,493 행 (Week 3 호환 보존)
- 부산물: CROSS JOIN (products × DISTINCT country_code) 로 undiagnosed 366 건이 국가별 3회 노출됨 — 다국가 의미 보존

### 듀얼 VIEW 구조 (`v_*` 다국가 + `v_*_us` 슬라이스)

- 단일 view 만 두기: Week 3 회귀 보장 어려움 (Q1~Q8 가 단일국 가정으로 작성됨)
- 두 view 모두 두기: Q1~Q8 은 `_us` 슬라이스 참조, 신규 Q9·Q10 만 다국가 view 직접 사용
- 결정: **단일국 호환을 view 레벨에서 보장**. Q-파일 수정은 view 이름 교체 한 줄. Q3 의 raw `nutrient_limits` 참조만 `country_code='US'` 필터 추가.
- 비용: 4 view 관리 부담. 다만 `_us` 는 `WHERE country_code='US'` 한 줄짜리 wrapper 라 실질 부담 없음.

### Q9 그룹 정의를 Q8 과 동일하게 유지

- 옵션: Trusted / Inferred / Other 3 그룹 그대로
- 대안: 다국가에서 그룹 정의를 변경 (예: 메타데이터 출처별로 더 세분화)
- **유지 채택**: Q8 회귀 검증을 위해 그룹 정의가 동일해야 함. Q9 의 US 슬라이스가 Q8 결과를 정확히 재현 ✓
- 산출: 4 영양소 × 3 국 × 3 그룹 = 36 셀

### Q10 출력 범위 — 옵션 B (판정 차이 있는 케이스만)

- 옵션 A: 모든 (제품, 영양소) 측정의 3국 판정 cross-tab 출력 — 1,500+ 행
- **옵션 B 채택**: `WHERE us_j != eu_j OR …` 필터. 차이 있는 케이스만 → 보고서 가독성 우선.
- 보완: 영양소별 차이 빈도 (10-A), "FDA → CODEX" 패턴 카운트 (10-B), 대표 케이스 (10-C) 의 3단 구성으로 정량 + 정성 동시 제공

### sugars 4 영양소 분석에 포함

- 제외 검토: OFF total vs US added/CODEX free 정의 차이 때문
- **포함 채택**: surrogate 명시 조건. EU 만 정의 정합, US/CODEX 는 total 을 상한 추정으로 사용
- 이유: sugars 의 EU 외형 느슨 효과는 임계값 설계가 진단에 미치는 영향을 잘 보여주는 정량 사례. 정의 차이를 명시하면 surrogate 비교 자체도 분석 가치 있음.

---

## 트러블슈팅

### 1. MSYS / Git Bash 의 docker exec 경로 자동 변환

- **증상**: `docker exec fda-postgres psql -f /tmp/05_multi_country_migration.sql` 가 `psql: error: C:/Users/julie/AppData/Local/Temp/...: No such file or directory` 로 실패
- **원인**: Git Bash (MSYS) 가 `/tmp/...` 패턴을 Windows 경로로 자동 변환하여 컨테이너 내부 경로가 호스트 경로로 바뀜
- **해결**: 환경 변수 `MSYS_NO_PATHCONV=1` 을 docker exec 앞에 붙임
- **배운 점**: Windows + Git Bash + Docker 조합에서 `/tmp` 같은 컨테이너 절대 경로를 그대로 보존하려면 이 변수 필수. PowerShell 에서는 발생하지 않음.

### 2. PowerShell + bash 변수 확장 차이

- **증상**: bash `for q in Q1 Q2 ...; do docker cp "${q}.sql" ...; done` 이 변수 미확장으로 실패 (`GetFileAttributesEx ...queries${q}.sql`)
- **원인**: 백슬래시 경로 안에서 bash 변수가 정상 확장 안 됨 (Git Bash 의 경로 해석 충돌)
- **해결**: PowerShell `foreach ($q in 'Q1','Q2',...) { docker cp "...\$q.sql" ... }` 로 교체
- **배운 점**: Windows 작업에서는 PowerShell 의 foreach 가 더 안전. bash 스크립트의 변수 확장은 경로 escape 와 충돌 가능.

### 3. `nutrient_name_kr` 이전으로 인한 Q7-A 깨짐

- **증상**: 마이그레이션 후 Q7-A 가 `column nl.nutrient_name_kr does not exist` 로 실패 가능 (실제 실행 전 코드 리뷰로 발견)
- **원인**: `nutrient_name_kr` 컬럼이 `nutrient_limits` → `nutrients` 로 이동. Q7-A 는 `nutrient_limits` 를 driver 로 쓰면서 `nl.nutrient_name_kr` 참조
- **해결**: Q7-A 의 driver 테이블을 `nutrient_limits` → `nutrients` 로 교체 (`nl` → `n` 별칭 변경 포함). `nutrient_limits` 자체는 결측 계산에 불필요하므로 JOIN 자체를 제거.
- **배운 점**: 스키마 정규화 시 컬럼 이전이 발생하는 모든 참조 위치를 사전 스캔 (Grep `nutrient_name_kr`) 으로 한 번에 파악하는 것이 안전. 회귀 검증 단계에서 결과 수치 동일성만 보면 컬럼 이전 누락은 못 잡음 (쿼리 자체가 실패).

### 4. VIEW CASCADE 의존성

- **증상**: 마이그레이션 Step D 에서 `ALTER TABLE nutrient_limits DROP COLUMN nutrient_name_kr` 실행 시 view 가 의존
- **원인**: `v_compliance_results` 가 `nl.nutrient_name_kr` 참조
- **해결**: 마이그레이션 Step A 에서 `DROP VIEW ... CASCADE` 로 의존 view 를 먼저 삭제 후 Step H 에서 임시 복원, Step 5 (06_dual_views.sql) 에서 최종 형태로 재생성
- **배운 점**: 정규화 마이그레이션은 view 의존성을 미리 명시적으로 해체해야 함. CASCADE 만 의존하면 사전 백업 (`pg_dump`) 이 필수 안전망.

---

## 정성적 관찰

### sodium 400 mg/100g 클러스터의 의미

Q10 의 "US 적합 → CODEX 위반" 95 케이스 중 상당수가 정확히 400.00 mg/100g 의 sodium 함량. 이는 측정 오차나 추정값이 아닌 **제조사가 의도적으로 표시한 함량** 으로 추정 (cross-product 일관성):

- Kimchi Buldak Dumpling, Chicken Tender, Special K 오리지널, Pork Cutlet, Half And Half Hotdog, Crispy Chicken Breasts, 마포식 차돌된장찌개 …

가설: 한국 식품 산업의 sodium 라벨링 관행이 "400 mg/100g 이하" 라는 산업 표준을 채택할 가능성. 보고서 한계 / 후속 연구 섹션에서 OFF 외부 데이터 (식약처 식품영양성분 DB 등) 와 cross-check 하면 가설 검증 가능.

### sugars 10g/100g 클러스터도 유사

같은 패턴이 sugars 10g/100g 케이스에서도 관찰됨. EU sugars 임계값 18g 의 외형 느슨 효과로 EU 에서만 적합 판정.

---

## 학습 노트

### 다국가 표준 정규화

- 표준 발행 기구 (FDA / EU Commission / Codex Alimentarius) 와 근거 규정 (`source`, `effective_date`) 을 nutrient_limits 에 보존해야 정량 분석의 재현성 보장
- sugars 의 정의 차이 (added / total / free) 처리 — 별도 `sugar_type` 컬럼으로 명시. surrogate 비교 시 해석에서 반드시 언급
- `nutrient_limits.threshold_ratio = 0.20` 은 3국 모두 동일 (DV 의 20%) — 임계 계산 로직은 국가 무관, 임계값만 다름

### 듀얼 VIEW 패턴

- 다국가 view + 단일국 슬라이스 view 의 조합은 backward-compat 와 forward-extension 을 동시에 달성하는 일반적 패턴
- 슬라이스 view 가 `WHERE country_code='US'` 한 줄짜리이므로 PostgreSQL 의 view inline 최적화로 성능 부담 없음 (실제 EXPLAIN 검증 시 동일 쿼리 플랜)

### CROSS JOIN 으로 모든 (entity, dimension) 조합 보존

- undiagnosed 제품도 다국가 view 에서 국가별 3회 노출되어야 의미가 살아남
- `SELECT DISTINCT country_code FROM nutrient_limits` CTE × `products` CROSS JOIN 으로 보장
- 대안 (LATERAL, GENERATE_SERIES) 대비 가독성·성능 모두 우수 — 차원 테이블이 작을 때 표준 패턴

### Q8 회귀 검증의 가치

- 다국가 인프라 도입 후 Q8 의 4 영양소 격차 (pp 단위 4자리) 가 정확히 일치 — view 정의 변경의 정확성을 한 번에 보장
- 회귀 기준이 명확할수록 마이그레이션 부담이 줄어듦. Week 3 산출물이 자연스러운 회귀 baseline 이 됨

---

## Week 4 의 가치

> Week 3 에서 발견한 "메타데이터 부재 → sodium 진단 가시성 격차" 가설을 다국가로 확장하면서, **표준 강도가 높아질수록 격차가 일관 확대**됨을 정량 발견 (Q9, CODEX +13.80 pp). 또한 동일 제품 1,308 sodium 측정 중 95 건이 FDA 적합 → CODEX 위반이며 그중 다수가 산업 표준점 400 mg/100g 에 위치 (Q10) — 표준 선택이 단순 임계값 차이가 아닌 식품 산업의 함량 분포 클러스터와 결합되어 진단 결과를 변화시키는 사례. 단일 표준 의존 분석을 넘어 **표준 × 데이터의 상호작용** 으로 framing 일반화 가능.

---

## Week 5 계획

### 시각화 (Week 3 미완 + Week 4 신규)

- 4 영양소 위반률 비교 차트 (Q1, US 단일국)
- 카테고리 × 영양소 위반률 히트맵 (Q1-B)
- **Q9 forest plot 스타일**: 그룹 간 위반율 차이 + 95% CI bar, 3국 동시 표시
- **Q10 cross-country gap 시각화**: sodium 함량 분포 + 3국 임계값 수직선 (밀집도 강조)
- risk_level 분포 도넛 차트 (Q5)

### 보고서 작성

- 4.5 (영양소별 위반률) — Q1 + 시각화
- 4.6 (룰 엔진 SQL 시연) — Q3 의 3-step CTE
- 4.7 (가설 검증) — Q8 + Q9 (다국가 확장)
- **4.8 신규 (Cross-country compliance gap)** — Q10 + sodium 400 mg/100g 클러스터 분석
- 한계점 (Q4 매핑 오류 + sugars surrogate + sodium 47% 결측) 정량 사례

### 도구

- matplotlib + seaborn. 한글 폰트 (맑은 고딕) + 영문 폰트 (Arial) 혼용
- forest plot: matplotlib `errorbar` + custom layout. statsmodels 의 `confint_proportions_2indep` 결과 활용
- PNG 300 dpi → `docs/figures/` (신규 폴더)

---

## 부산물 — Week 4 의 산출물

- `sql/05_multi_country_migration.sql` — 마이그레이션 (Step A~H)
- `sql/06_dual_views.sql` — 듀얼 VIEW 4종
- `sql/queries/Q9.sql`, `Q10.sql` — 다국가 분석 쿼리
- `sql/queries/Q1~Q8.sql` — view 참조 `_us` 슬라이스로 교체, Q3·Q7-A 직접 참조 보정
- `docs/results/Q9.md`, `Q10.md` — 결과 + 해석
- `docs/results/README.md` — Week 3/Week 4 섹션 분리 + sugars surrogate 주의 명시
- `docs/journal/week4.md` — 본 일지
- `backup_before_normalization.sql` — pg_dump 백업 (gitignore 처리, 로컬 보관)
