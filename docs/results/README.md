# SQL 룰 엔진 분석 결과 인덱스

## Week 3 — 단일국 (US) 진단

| Query | 주제 | 핵심 발견 (1줄) |
|---|---|---|
| [Q1](Q1.md) | 영양소별·카테고리별 high 분포 | 진단된 (제품, 영양소) 의 약 1/3 이 DV ≥ 20 %; 포화지방 위반율 최고 (36.2 %) |
| [Q2](Q2.md) | 카테고리별 위반율 | Snacks 69 % / Sweets 46 % 최상위; Other 제외 시 전체 비율은 거의 불변 (29.6 % → 30.6 %) |
| [Q3](Q3.md) | 3-step CTE 다단계 진단 | 진단된 2,127 건 중 medium 46.5 % / high 25.3 % / low 28.1 % |
| [Q4](Q4.md) | 카테고리 내 RANK top 5 | 트러플 200 %DV 포화지방, 간장 417 %DV 나트륨; product_name 매핑 오분류 사례 정성 확인 |
| [Q5](Q5.md) | VIEW 활용 종합 진단 | 전체 2,493 건 risk_level: high 21.6 % / medium 39.7 % / low 24.0 % / undiagnosed 14.7 % |
| [Q6](Q6.md) | 제품당 high 영양소 개수 | 다중 위험(2+) 23.6 %; 모두 위반(4개) 30 건 |
| [Q7](Q7.md) | NULL 탐지 | sodium 결측 47.5 %; undiagnosed 366 건 중 77.3 % 가 Other × other |
| [Q8](Q8.md) | ★ 가설 검증 (SQL+z-test) | **sodium 만 Other > Trusted (+10.98 pp, p=0.003) 유의**; saturated_fat 은 반대 방향 (Trusted +13.50 pp) |

## Week 4 — 다국가 (US / EU / CODEX) 확장

| Query | 주제 | 핵심 발견 (1줄) |
|---|---|---|
| [Q9](Q9.md) | Q8 다국가 확장 (36 셀) | sodium Other-Trusted gap: CODEX +13.80 > US +10.98 > EU +9.29 pp — **표준이 엄격할수록 메타데이터 부재 효과 강화** |
| [Q10](Q10.md) | 동일 제품의 국가별 판정 차이 | sodium **95 케이스** "FDA 적합 → CODEX 위반" (다수가 400 mg/100g 클러스터); sat_fat / energy 는 임계값 동일이라 차이 0 |

## Week 6 — 실용성 강화 (라벨 의무 전수 진단)

| Query | 주제 | 핵심 발견 (1줄) |
|---|---|---|
| [Q11](Q11.md) ★ | 한국 식품 2,493건 라벨 의무 전수 진단 (7,479행) | EU 60.41 % > US 54.19 % > CODEX 51.74 % (pass_pct); **"CODEX safe = 글로벌 수출 안전권" 924 건** — 보고서 4.4 절 + Streamlit MVP 토대 |

## 산출물

- **VIEW 4개 (Week 4 듀얼)**:
  - `v_compliance_results` (다국가, 19,767 행) / `v_compliance_us` (Week 3 호환, 6,589 행)
  - `v_risk_score` (다국가, 7,479 행 = 2,493 × 3) / `v_risk_score_us` (Week 3 호환, 2,493 행)
- **SQL 11 개**: [sql/queries/Q1.sql ~ Q11.sql](../../sql/queries/)
- **마이그레이션**: [sql/05_multi_country_migration.sql](../../sql/05_multi_country_migration.sql), [sql/06_dual_views.sql](../../sql/06_dual_views.sql)
- **Python 통계 검증**: [analysis/q8_statistical_test.py](../../analysis/q8_statistical_test.py)
- **결과 CSV**:
  - [q8_ztest_results.csv](q8_ztest_results.csv) — Q8 z-검정 raw 결과
  - [Q11_full_diagnosis.csv](Q11_full_diagnosis.csv) — 라벨 의무 전수 진단 7,479 행 / 493 KB

## Sugars surrogate 주의 사항 (Q9 · Q10 공통)

- OFF 원본의 `sugars-100g` 는 **total sugars** 기준 — EU (Regulation 1169/2011) 정의와만 정합.
- US (21 CFR 101.9) 는 added sugars, CODEX (WHO 2015) 는 free sugars 가 정식 정의.
- 본 분석의 sugars 비교 중 EU 결과만 정의 정합. US / CODEX 의 sugars 결과는 total 을 surrogate 로 사용한 상한 추정.
- 보고서·발표에서 sugars cross-country 인사이트를 언급할 때 반드시 명시할 것.
