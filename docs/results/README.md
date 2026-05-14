# Week 3 — SQL 룰 엔진 분석 결과 인덱스

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

## 산출물

- VIEW 2 개: `v_compliance_results` (6,589 행) / `v_risk_score` (2,493 행)
- SQL 8 개 ([sql/queries/Q1.sql ~ Q8.sql](../../sql/queries/))
- Python 통계 검증 1 개 ([analysis/q8_statistical_test.py](../../analysis/q8_statistical_test.py))
- 결과 CSV: [q8_ztest_results.csv](q8_ztest_results.csv)
