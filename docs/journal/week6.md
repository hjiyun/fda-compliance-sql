# Week 6 — 보고서 작성 + 실용성 강화 (Q11 · Streamlit MVP)

> **기간**: 2026.06.02 ~ 2026.06.09
> **상태**: ✅ 완료 (Streamlit MVP UI 피드백은 Week 7 로 위임)

---

## 목표

- 보고서 1~5 장 학술 톤으로 작성 (단정 회피 · cross-reference 일관)
- 시각화 4 종 확정
- 실용성 강화 — 본 연구의 SQL 룰 엔진을 *수출 시장별 라벨 부담 점검 도구* 로 환산
- Streamlit MVP 골격 완성 (DB 의존성 없는 dict 임베드 방식)

---

## 결과 요약

| 항목 | 값 | 비고 |
|---|---:|---|
| 보고서 통합본 | **65,381 자 / 약 42 페이지** | `docs/report/full_report.md` |
| 본문 5 개 장 | 5 파일 / 약 800 줄 | 01~05, single source of truth |
| 초록 본문 | 670 자 | 권장 400~600 자 약간 초과 |
| 그림 | 4 종 (300 DPI PNG) | Week 5 산출물 재활용 |
| 표 | 9 종 (4.1 ~ 4.9) | Week 6 신규: 4.5~4.8 (Q11 결과) |
| Q11 분석 | 7,479 행 평탄화 CSV (493 KB) | 한국 식품 × 3 국 라벨 의무 전수 |
| Streamlit MVP | `app/app.py` 349 줄 | DB 의존성 0, 3 시연 시나리오 내장 |
| 통합 스크립트 | `_assemble_full_report.py` | 본문 6 파일 → full_report.md 자동 생성 |

---

## 핵심 작업

### 보고서 1~5 장 작성

- 1 장 서론 — RQ1~3 명시, 1.3 절 3 가지 연구 기여 정립
- 2 장 이론적 배경 — FDA · EU · CODEX 표준 위계 + ISO/IEC 17000 / 25012 인용 + MNAR 가설 framing
- 3 장 연구 방법론 — DB 설계 4 원칙 + ETL 4-tier 매핑 + SQL 분석 기법 (코드 인용 3 개: `v_compliance_results`, Q3 CTE, Q10 cross-tab)
- 4 장 분석 결과 — Q1~Q11 통합, 시각화 4 종 본문 인용, 절 구조 변경 (4.4 Q11 신규 + 4.5 1차 비교 이동)
- 5 장 표준학적 해석 — 3 핵심 발견 종합 + RQ 답변 + 한계 5 종(인과 3 + 데이터 5) + 향후 연구 3 종

### 시각화 4 종 (Week 5 산출물의 본문 인용)

- 그림 4.1 카테고리 × 영양소 히트맵
- 그림 4.2 Q8 forest plot
- 그림 4.3 sodium 단조 패턴 (학술적 정점)
- 그림 4.4 sodium 400 mg 클러스터

### 실용성 강화 — Q11 + 보고서 통합

- `sql/queries/Q11.sql` — 4 부분 쿼리 (집계 + 영양소 빈도 + 시장 비교 + 평탄화)
- `docs/results/Q11.md` — 결과 + 실무 활용 시사
- `docs/results/Q11_full_diagnosis.csv` — 7,479 행 (제품 × 국가) 전수
- 보고서 4.4 절 신규 추가 (5 부절: 분포 / 영양소별 / cross-country / 대표사례 / 실무 시사)
- 보고서 5.2.3 실무 함의 보강 — (a) 수출 기업 도구 / (b) 식약처 정합성 / (c) 다국가 재사용
- 보고서 5.4.3 셋째 항목 신규 — Streamlit MVP 위치 명시

### Streamlit MVP 골격

- `app/app.py` — 5 개 render 함수 분리 (sidebar · inputs · burden cards · diagnosis table · chart · recommendation)
- `NUTRIENT_LIMITS` dict 12 행 임베드 — PostgreSQL 의존성 0 (Streamlit Cloud 호스팅 비용 0)
- 3 시연 시나리오 사이드바 버튼 (Shin Ramyun / 400 mg 클러스터 / 글로벌 안전권)
- Plotly group bar (4 영양소 × 3 국 % DV + 5/20 % DV 기준선)
- 단순 권장 조치 (현재값 − 임계값 차이)

---

## 핵심 의사결정

### 보고서 분량 35~40 → 42 페이지 허용

- 4.4 절 신규 추가로 약 2 페이지 증가
- 학사 보고서 상한 (45 페이지) 내 유지
- *학술 + 실무 통합 framing* 의 자연스러운 산물로 정당화. 분량 축소를 위해 4.4 를 빼는 것은 본 연구의 핵심 가치(룰 엔진의 실무 환원) 를 약화시킴

### Cross-reference 일관성을 *의도적 설계 작업* 으로 처리

- 2.4 ↔ 5.1 · 5.5 "상호작용" 메시지 일관 인용 (단 5.5 만 변주: "표준 위계의 엄격도 와 메타데이터 품질")
- 3 장 한계 박스 4 종 ↔ 5.3.3 데이터 한계 명시 cross-ref (절 번호 포함)
- 5.2.3 (a) ↔ 5.4.3 셋째 항목 (Streamlit) 양방향 호응
- 절 구조 변경 (4.4 신규) 시 stale 참조 자체 점검 → 2 곳 발견·수정 (5.2.3 마지막, 5.4.3 둘째)

### 시나리오 B 수학적 검증 (Streamlit MVP)

- 사용자 spec *"400 mg 클러스터 → US/EU safe, CODEX 만 multi"* 가 본 4 영양소 임계 구조에서 *수학적으로 불가능* 임을 unit 검증으로 발견
- 이유: CODEX 단독 high 가능 영양소가 sodium 한 종류뿐 (sat_fat · energy 는 3 국 동일, sugars 는 US/CODEX 동일)
- **옵션 1 채택** — expected 만 "single_warning" 으로 정정 + 보고서 메시지 "FDA 적합 → CODEX 위반" 패턴은 유지
- AI 가 사용자 spec 을 그대로 수용하지 않고 수학적 검증으로 반박한 사례 — 본 프로젝트 협업의 *동의 전 검토* 원칙의 직접 적용

### 표 캡션 [표 4.X] 부여 + 표 목록 (List of Tables) 신설

- 그림 캡션 일관성과 동등 처리 (학술 보고서 표준)
- 4.4 절 신규 추가로 표 5 → 9 종 확장
- 표 목록은 마감 직전 보류였으나 캡션 부여 직후 동일 작업 흐름에서 처리 (효율)

### 통합본 자동 생성 스크립트 (`_assemble_full_report.py`)

- 본문 6 파일 (`00_abstract` + `01~05`) 을 single source of truth 로 유지
- 통합본은 파생 산출물 — 본문 수정 시 한 줄 명령으로 재생성
- TOC · 그림 목록 · 표 목록은 스크립트 내 수동 작성 (3-level TOC 의 한국어 헤더 anchor 깨짐 위험 회피)

---

## 트러블슈팅

### 1. `wc -m` 결과의 단위 혼동

- **증상**: 보고서 분량 보고에서 `wc -m` 결과 (98,425 등) 를 글자 수로 해석. Python `len()` 기준 실제 글자 수는 57,206
- **원인**: `wc -m` 은 로케일에 따라 *UTF-8 바이트 수* 반환. 한글 1 자 = 3 바이트이므로 글자 수의 약 1.8 배
- **해결**: Python `len()` 으로 재측정. 단 분량 추정은 글자/페이지 비율(약 1,700 자 / A4) 기준으로 통일
- **배운 점**: 텍스트 분량 측정 시 *글자 수* 와 *바이트 수* 를 명확히 구분. 학술 보고서 분량 평가는 항상 글자 수 기준

### 2. PostgreSQL `ORDER BY` CASE 별칭 입력 제약 재발

- **증상**: Q11-A 의 `ORDER BY CASE label_burden_level WHEN ...` 가 *별칭 ↔ 다른 CASE 입력 사용 불가* 제약으로 실패. Week 3 학습 노트의 동일 패턴
- **해결**: CTE 분리로 별칭을 먼저 부여, 외부 SELECT 에서 GROUP BY · ORDER BY
- **배운 점**: 같은 트러블슈팅 패턴이 재발할 때 *학습 노트의 가치* 확인. 새 쿼리 작성 시 학습 노트 prefer-check 습관화 검토

### 3. Streamlit 시나리오 B 의 수학적 불가능성

- **증상**: 사용자 spec "CODEX 만 multi" 의 입력값 (sodium 400, sugars 5, sat_fat 3, energy 250) 으로 unit test 시 CODEX = single_warning (sodium 단독 high) 만 나옴
- **원인**: CODEX 단독 high 가능 영양소가 sodium 한 종류 뿐이라 *둘 이상 high* (multi) 가 수학적으로 불가능
- **해결**: 옵션 1 — expected 정정 (single_warning), 입력값 유지. *비대칭 패턴* 자체는 메시지로 살림
- **배운 점**: 시나리오 설계 시 표준의 임계값 구조를 직접 시뮬레이션해야 함. 직관에만 의존하면 spec 과 실제가 어긋남

---

## 정성적 관찰

### 보고서 분량 균형의 의식적 설계

장별 분량을 의도적으로 비대칭 배분:
- 3 장 (방법론) 약 9 페이지 — 가장 두꺼움 (학술 보고서 표준 7~10 페이지)
- 5 장 (해석·결론) 약 8 페이지 — 한계 절 풍부히 (5.3.3 만 5 항목)
- 4 장 (결과) 약 7~8 페이지 — Q11 절 추가로 분량 증가
- 1·2 장 약 6 페이지씩 — 도입·이론

방법론·해석을 두껍게, 도입은 정제. 학사 보고서 평가 기준의 *방법·해석 깊이* 가중치 반영.

### Cross-reference 자체 점검의 가치

절 구조 변경 (4.4 신규 추가 + 4.5 이동) 시 *grep 으로 stale 참조 자체 점검* 을 수행. 2 곳의 stale 참조 (5.2.3, 5.4.3) 발견·수정. 사용자가 명시적으로 요청하지 않았으나 cross-reference 무결성 차원에서 필수적 작업.

→ 학술 보고서의 *문서 무결성* 은 자동화된 자체 점검 (grep `4\.4|4\.5` 같은) 의 가치를 보여줌. Week 7 마감 직전에도 동일 절차 1 회 더 반복 권장.

### AI 협업 시 수학적 자율 검증의 가치

사용자 spec 의 "CODEX 만 multi" 가 *불가능* 임을 AI 가 자율적으로 검증. *사용자 spec → AI 그대로 구현* 의 단순 패턴이 아니라, AI 가 검증 단계에서 반박 + 옵션 제시. 사용자 선호 *"AI 제안 그대로 OK 금지"* 원칙의 양방향 적용 사례.

### MVP 원칙의 실천

Streamlit MVP 범위 결정 시 "하나를 제대로 vs 둘을 어설프게" 의 명시적 선택. 옵션 A (신규 제품 진단) 단독으로 결정, 옵션 B (기존 식품 검색) 는 Week 7 시간 여유 시 추가. MVP 가 흔히 "minimum lovable" 보다 "minimum viable" 에 그치는 함정을 회피.

---

## 학습 노트

### 학술 보고서 작성

- **본문 6 파일 + 통합본 1 파일** 의 single source of truth + derived artifact 패턴 — 보고서 마감 직전까지 본문만 수정하면 통합본은 한 줄 명령으로 갱신
- **분량 측정** 은 *글자 수* (Python `len()`) 기준 통일. `wc -m` 은 UTF-8 바이트 수로 한국어 분량 과대 추정
- **단정 회피** 의 통일된 표현 — "시사한다", "본 데이터에서 관측된 패턴", "가능성을 제시한다" 등. 1~5 장 톤 일관성의 핵심
- **Cross-reference 절 번호 명시** — "5 장에서 다룬다" 보다 "5 장 5.3.3 절에서 다룬다" 가 정직성 ↑

### Streamlit MVP 설계

- **DB 의존성 0** — `nutrient_limits` 12 행을 Python dict 로 임베드. Streamlit Cloud 호스팅 비용 0 + 단일 파일 실행 가능
- **시나리오 사이드바 버튼** — 발표 시연용. session_state 패턴으로 입력값 자동 채움
- **render 함수 분리** — `init_session_state` · `render_sidebar` · `render_inputs` · `diagnose` · `render_burden_cards` · `render_diagnosis_table` · `render_chart` · `render_recommendation` · `render_footer` — 단일 책임 원칙
- **수학적 검증** — 사용자 spec 의 시나리오를 unit test 로 사전 검증. UI 작성 후 문제 발견하면 비용 큼

### Cross-reference 일관성

- *grep 자체 점검* 을 Week 마감 작업 표준 절차로 채택 권장
- 절 번호 변경 시 `\d+\.\d+` 패턴으로 전수 점검
- 그림 · 표 캡션은 본문 인용과 캡션 정의 모두 grep 으로 양방향 점검

---

## 부산물

### 보고서

- `docs/report/00_abstract.md` — 초록 670 자 + 주제어 7 종
- `docs/report/01_introduction.md` — 1 장 서론
- `docs/report/02_theoretical_background.md` — 2 장 이론적 배경
- `docs/report/03_methodology.md` — 3 장 연구 방법론 (SQL 코드 3 인용)
- `docs/report/04_results.md` — 4 장 분석 결과 (Q1~Q11 + 그림 4 + 표 9)
- `docs/report/05_discussion.md` — 5 장 표준학적 해석 · 한계 · 향후 · 결론
- `docs/report/full_report.md` — 통합본 65,381 자 / 약 42 페이지
- `docs/report/_assemble_full_report.py` — 통합 자동 생성 스크립트
- `docs/report/_TODO.md` — 인용 보강 추적 (gitignore 처리)

### 실용성 산출

- `sql/queries/Q11.sql` — 라벨 의무 전수 진단 4 부분 쿼리
- `docs/results/Q11.md` — 결과 + 실무 활용 시사
- `docs/results/Q11_full_diagnosis.csv` — 7,479 행 평탄화
- `app/app.py` — Streamlit MVP (349 줄, 5 render 함수)

### 갱신

- `README.md` — Week 6 완료 반영 (배지, 5 발견, 임계값표 실제값 정정, 일정표, 일지 링크, 보고서 섹션 신설, Week 7 미리보기)
- `.gitignore` — `docs/report/_TODO.md` 등재

---

## 다음 주 (Week 7) 계획

### 핵심

- Streamlit MVP 로컬 실행 + UI 디자인 피드백 · 미세 조정
- (시간 여유 시) 옵션 B 추가 — 기존 한국 식품 2,493 건 검색 기능
- (시간 여유 시) Streamlit Cloud 호스팅 시도

### 보고서 마무리

- 표지 정보 보강 (지도교수 · 제출일) — 현재 학번까지만 명시
- PDF 변환 (pandoc 또는 markdown-pdf) + 페이지 번호 수동 보강 후 목차·그림 목록·표 목록 페이지 번호 채움
- 발표 자료 PPT 1차 (보고서 핵심 발견 5 종 + 시각화 4 종 + Streamlit 데모 영상)

### 선택

- 인용 보강 — `docs/report/_TODO.md` 의 KISS/RISS 검색 키워드로 한국어 학술 논문 2~3 편 인용 추가 (2.3.2, 2.3.3 절)
- `docs/results/README.md` Q11 인덱스 추가 (Week 6 미완 항목)

### 도구

- `streamlit` (이미 설치) · `pandas` · `plotly` (Streamlit 추가 의존성)
- `pandoc` (PDF 변환용, 신규 설치 검토)
- `Markdown All in One` VS Code 확장 (목차 자동 생성 보조)

---

## Week 6 의 가치

> Week 1~5 의 *데이터 → 분석 → 발견* 흐름을 *학술 보고서* 라는 단일 산출물로 응축. 동시에 본 연구의 SQL 룰 엔진을 *수출 시장별 라벨 부담 점검 도구* 로 환산하여 학술-실무 통합 framing 완성. 보고서 단일 파일 35~40 페이지 목표를 약간 초과(42 페이지) 하였으나, 4.4 절(Q11 실무) + 5.2.3 (a)(b)(c) + 5.4.3 셋째 항목(Streamlit) 의 일관된 학술→실무 사슬을 위한 자연스러운 분량 증가. *"표준 위계의 엄격도와 메타데이터 품질이 상호작용한다"* 의 학술 명제와 *"CODEX safe = 글로벌 수출 안전권"* 의 실무 메시지가 동일 데이터(한국 식품 2,493 건) 위에서 한 보고서로 통합된 형태로 도달.
