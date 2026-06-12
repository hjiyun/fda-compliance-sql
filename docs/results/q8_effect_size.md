# Q8 보완 — 효과크기 (Odds Ratio · Cramér's V)

**목적**: 기존 Q8 비례 z-검정("차이가 유의한가")을 **대체하지 않고 보완**한다 — "차이가 얼마나 큰가"를 효과크기 한 수치로 덧붙인다. p값 결과는 그대로 두고 그 옆에 효과크기를 병기한다.

## 설정 (Q8 과 동일)

- 데이터: `v_compliance_us` (단일국 US). 분석 단위 = (제품 × 영양소). `INNER JOIN` 으로 결측 영양소 행 제외.
- 그룹: Trusted(`tags`/`top`) · Inferred(`name`) · Other(`other`). 위반 = `high` (DV ≥ 20%).
- OR 2×2 는 **Trusted vs Other** (Inferred 제외, z-검정과 동일 비교).

## 셀 빈도 (2×2: group × {no_viol, viol})

| nutrient | Trusted (no/viol) | Other (no/viol) | 최소 셀 |
|---|---|---|---:|
| sodium | 164 / 55 | 416 / 235 | 55 |
| saturated_fat | 120 / 101 | 518 / 246 | 101 |
| sugars | 142 / 87 | 586 / 266 | 87 |
| energy | 172 / 73 | 910 / 233 | 73 |

→ **0 셀 없음 → Haldane-Anscombe 보정 불필요, OR 안정적.** category×위반(sodium) 표만 관측 최소 셀이 10(Sweets 위반)이나 **기대빈도 최소 12.0 ≥ 5** 로 카이제곱·V 유효.

## 효과크기 등급 기준

- Cohen (φ / Cramér's V, 자유도 df\* = min(r,c)−1 = 1 인 표): **0.10 small · 0.30 medium · 0.50 large** (< 0.10 negligible).
- 본 분석의 모든 표는 위반 차원이 2범주 → df\* = 1 → 위 기준 적용.
- OR 은 비표준화 방향 지표로 보고하고, 표준화 magnitude 등급은 φ(2×2)로 매긴다. **등급은 기준에 기계적으로 대조만 하며 부풀리지 않는다.**

## 표 1 — 유의성(기존) + 효과크기(신규) 병기

OR = odds(viol \| Other) / odds(viol \| Trusted). **OR > 1 = Other 위반 odds 더 높음.** Δpp = (Other − Trusted) rate, p = 기존 z-검정(two-sided).

| nutrient | Δpp (Other−Trusted) | p (z-검정, 기존) | OR (Other vs Trusted) | 95% CI | φ | 등급 |
|---|---:|---:|---:|---|---:|---|
| **sodium** | **+10.98** | **0.0029** | **1.68** | [1.19, 2.38] | 0.101 | **small** |
| saturated_fat | −13.50 | 0.0002 | 0.56 | [0.42, 0.77] | 0.118 | small |
| energy | −9.41 | 0.0013 | 0.60 | [0.44, 0.82] | 0.087 | negligible |
| sugars | −6.77 | 0.0524 | 0.74 | [0.55, 1.00] | 0.059 | negligible |

- 방향: **sodium 만 OR > 1** (Other 위험 ↑). saturated_fat·energy·sugars 는 OR < 1 (Other 위험 ↓). 모든 OR 부호가 z-검정 Δpp 부호와 **일치**.
- sugars 는 OR CI 상한이 1.00 에 걸려(p = 0.052) 유의성 경계 — z-검정과 일관.
- energy 는 OR CI 가 1 을 제외(통계적으로 구분 가능)하나 φ 는 negligible — **"유의 ≠ 큰 효과"** 의 전형.

## 표 2 — Cramér's V (bias-corrected, Bergsma 2013)

| 분할표 | n | shape | χ² | p | min 기대빈도 | V | V(보정) | 등급 |
|---|---:|---|---:|---:|---:|---:|---:|---|
| 3그룹 × 위반 (sodium) | 1,308 | 3×2 | 17.53 | 1.6e−4 | 67.3 | 0.116 | 0.109 | small |
| 3그룹 × 위반 (saturated_fat) | 1,500 | 3×2 | 14.70 | 6.4e−4 | 80.0 | 0.099 | 0.092 | negligible |
| 3그룹 × 위반 (energy) | 2,120 | 3×2 | 11.02 | 4.1e−3 | 52.9 | 0.072 | 0.065 | negligible |
| 3그룹 × 위반 (sugars) | 1,661 | 3×2 | 4.03 | 0.133 | 75.8 | 0.049 | 0.035 | negligible |
| **category × 위반 (sodium)** | 1,308 | 6×2 | 51.27 | 7.6e−10 | 12.0 | 0.198 | **0.188** | **small** |

## 핵심 해석

1. **sodium 효과크기는 "small"** (OR 1.68; φ 0.101; 3그룹 V 0.109) — small 임계(0.10)를 갓 넘는 수준이다. z-검정 유의성(p = 0.003)과 효과크기가 **같은 방향으로 sodium 발견을 지지**하나, 표준화 크기는 **작다**(medium/large 아님).
2. sodium 은 4영양소 중 **유일하게 OR > 1** 이며 효과크기도 가장 크다(그래도 small). saturated_fat 은 반대 방향(OR 0.56, small) — Q8 의 −13.50 pp 와 일관.
3. category × 위반(sodium) 의 V = 0.188(small) 로 meta_group(0.109) 보다 다소 크다 — sodium 위반은 메타데이터 신뢰도보다 **카테고리 자체와의 연관이 약간 더 강하나**, 둘 다 여전히 small.

> 종합: 효과크기는 z-검정의 sodium 발견을 **방향·유의성 면에서 보강**하지만, 그 크기는 일관되게 **small~negligible** 이다. "통계적으로 유의 + 효과크기는 작음" 으로 보고하는 것이 정확하다.

## 산출물

- [q8_effect_size.py](../../analysis/q8_effect_size.py) — OR · Cramér's V 계산
- [q8_effect_size_or.csv](q8_effect_size_or.csv) — OR 표 (2×2 raw count 포함)
- [q8_effect_size_cramersv.csv](q8_effect_size_cramersv.csv) — Cramér's V 표
- 기존: [Q8.md](Q8.md) · [q8_ztest_results.csv](q8_ztest_results.csv) (z-검정, 변경 없음)
