# 보강 분석 — 표준 강도 × 메타데이터 품질 교호작용 (로지스틱 회귀)

**목적**: Q8(비례 z-검정)이 보인 "Other(메타데이터 부재) vs Trusted 의 sodium 위반율 격차" 가 "표준이 엄격해질수록 단조 확대"(EU 9.3 → US 11.0 → CODEX 13.8 pp)되는 패턴을, 세 점을 눈으로 보는 기술(description) 수준을 넘어 **회귀 교호항(meta_group × strictness)으로 정식 검정**한다.

## 데이터 · 분석 단위

- 출처: `v_compliance_results` (다국가, 제품 × 영양소 × 국가). 분석 단위 = **(제품, 국가)**.
- `INNER JOIN` 정책으로 **결측 영양소 행은 자동 제외** — 미측정값을 "위반 아님(0)" 으로 오집계하지 않음.
- 영양소: 주분석 **sodium**, 비교용 **saturated_fat**.

## 변수

| 변수 | 정의 |
|---|---|
| `is_violation` (종속) | `judgment = 'high'` (DV ≥ 20%) → 1, else 0 |
| `meta_group` | Trusted(`tags`/`top`, **기준**) · Inferred(`name`) · Other(`other`). `free`(0건)는 제외 |
| `strictness` (a) | 순서형 정수 — **EU=0, US=1, CODEX=2** (sodium 임계값 480→460→400 mg/100g 순), 연속 취급 |
| `strictness` (b) | `country_code` 범주형, **기준=EU** |
| 교호항 | `meta_group × strictness` — **본 분석의 핵심** |

**통제변수 `category` 제외 (구조적 공선성)**: `category_source='other'` 인 제품은 정의상 카테고리 미분류(`category='Other'`) 이므로, `category='Other'` ⟺ `meta_group='Other'` 가 **651건 1:1로 완전 일치**한다. 두 변수가 동일 열이 되어 식별 불가하므로 category 를 통제변수로 넣지 않았다(넣으면 특이행렬). 즉 "메타데이터 부재군 = 미분류 카테고리군" 은 분리 불가능한 동일 집단이다.

## 통계 처리

- **클러스터-로버스트 표준오차** (`cov_type='cluster'`, groups=`product_id`). 같은 제품이 3국에 반복 등장 → 관측치 비독립이므로 필수.
- 모델: `statsmodels` 로지스틱 회귀 (Treatment coding, 기준 Trusted/EU).

## 표본 · 셀 빈도 (sodium)

제품 1,308 × 3국 = **3,924 행**. 모든 셀 n ≥ 219, 위반 53~295건 → 희소·분리 없음.

| meta_group | n / 국 | EU 위반율 | US | CODEX | Other−Trusted 격차 |
|---|---:|---:|---:|---:|---|
| Trusted | 219 | 24.2 % | 25.1 % | 31.5 % | — |
| Inferred | 438 | 24.7 % | 25.6 % | 30.4 % | — |
| Other | 651 | 33.5 % | 36.1 % | 45.3 % | 9.3 → 11.0 → **13.8** pp |

→ 격차는 기술적(descriptive)으로 단조 확대. 이것이 회귀 교호항에서도 유의한지가 검정 대상.

## 결과 — sodium 모델 (a) 순서형 strictness

n = 3,924 · clusters = 1,308 · converged · pseudo-R² = 0.017

| term | coef | OR | 95% CI (OR) | p |
|---|---:|---:|---|---:|
| Intercept | −1.189 | 0.30 | [0.22, 0.42] | <0.001 |
| meta[Inferred] | 0.039 | 1.04 | [0.70, 1.54] | 0.846 |
| meta[Other] | 0.456 | 1.58 | [1.10, 2.27] | **0.014** |
| strictness_ord | 0.186 | 1.20 | [1.10, 1.32] | **<0.001** |
| meta[Inferred] × strictness | −0.041 | 0.96 | [0.86, 1.07] | 0.454 |
| **meta[Other] × strictness** | **0.065** | **1.07** | **[0.96, 1.19]** | **0.223** |

## 결과 — sodium 모델 (b) country 범주형 (ref=EU)

n = 3,924 · clusters = 1,308 · converged · pseudo-R² = 0.018

| term | coef | OR | 95% CI (OR) | p |
|---|---:|---:|---|---:|
| Intercept | −1.142 | 0.32 | [0.23, 0.44] | <0.001 |
| meta[Inferred] | 0.025 | 1.03 | [0.70, 1.50] | 0.898 |
| meta[Other] | 0.456 | 1.58 | [1.11, 2.24] | **0.011** |
| country[US] | 0.049 | 1.05 | [0.98, 1.12] | 0.156 |
| country[CODEX] | 0.365 | 1.44 | [1.21, 1.71] | **<0.001** |
| meta[Inferred] × US | −0.001 | 1.00 | [0.92, 1.09] | 0.989 |
| **meta[Other] × US** | **0.066** | **1.07** | **[0.98, 1.17]** | **0.137** |
| meta[Inferred] × CODEX | −0.078 | 0.92 | [0.75, 1.14] | 0.456 |
| **meta[Other] × CODEX** | **0.133** | **1.14** | **[0.93, 1.40]** | **0.199** |

## 핵심 해석

> **교호항(Other × strictness)은 부호는 양(+)으로 "단조 확대" 서사와 방향이 일치하지만, product 클러스터-로버스트 SE 적용 후 통계적으로 유의하지 않다** (순서형 OR 1.07, p = 0.22 / Other×CODEX OR 1.14, p = 0.20). 즉 눈으로 보이던 격차 확대(9.3→11.0→13.8 pp)는 회귀 교호항으로는 α=0.05 에서 확증되지 않는다(**음성 결과**).

견고하게 유의한 것은 **주효과**다: ① 메타데이터 부재(Other)의 기저 위반 위험 상승(OR 1.58, p ≈ 0.01), ② 표준 엄격화 자체(순서형 OR 1.20/단계, p < 0.001; CODEX vs EU OR 1.44, p < 0.001). US vs EU 는 무차이(p = 0.16) — 두 임계값(460 vs 480)이 가까운 점과 일치.

## 비교 — saturated_fat

saturated_fat 은 **3국 임계값이 모두 동일**(4 g/100g) → 위반 여부가 국가 간 완전 동일(셀 위반율 Inferred 38.1 / Other 32.2 / Trusted 45.7 %, 3국 모두 같음). 따라서 **strictness 변동이 0 → 교호항이 구조적으로 정의되지 않음**(strictness·교호항 계수 = 0, Other×strictness 의 SE = NaN, degenerate).

| term | coef | OR | 95% CI (OR) | p |
|---|---:|---:|---|---:|
| meta[Inferred] | −0.315 | 0.73 | [0.53, 1.00] | 0.053 |
| meta[Other] | −0.572 | 0.56 | [0.42, 0.77] | **<0.001** |
| strictness_ord | 0.000 | 1.00 | — | 1.000 (degenerate) |
| meta[Other] × strictness | 0.000 | 1.00 | NaN | NaN (식별 불가) |

→ saturated_fat 의 메타데이터 주효과는 **음(Other OR 0.56)** 으로 sodium(양, OR 1.58)과 **반대 부호** — Q8 의 −13.50 pp 격차와 일관. 다만 교호항은 임계값 동일성 때문에 **검정 자체가 불가능**하다.

## 결론

1. **단조 확대의 통계적 확증 실패(음성).** 기술적 패턴(9.3→11.0→13.8 pp)은 존재하나, 교호항으로는 유의하지 않다(p ≈ 0.20~0.22). 보고서 5장의 "단조 확대" 서술은 *기술적 관찰*로는 유효하되 *정식 교호작용 검정으로는 미확증*임을 함께 명시하는 것이 정확하다.
2. **주효과는 견고.** 메타데이터 부재의 sodium 위반 위험 ↑, 표준 엄격화(특히 CODEX)의 위반 ↑ 는 모두 유의.
3. **영양소별 비대칭 재확인.** sodium 은 메타데이터 부재가 위험 ↑(양), saturated_fat 은 위험 ↓(음). saturated_fat 은 임계값 동일성으로 strictness 교호 검정 불가.

## 주의 (통계)

- 관측치 비독립(제품당 3국 반복) → product_id 클러스터-로버스트 SE 로 보정. 미보정 시 SE 과소·p 과대평가 위험.
- `category` 통제 불가(meta_group 과 완전 공선) — 위 변수 절 참조.
- 교호항 비유의는 **그대로 보고**한 결과이며, 유의화를 위한 표본 필터·변수 변경은 적용하지 않음.

## 산출물

- [logit_strictness_interaction.py](../../analysis/logit_strictness_interaction.py) — 회귀 스크립트
- [logit_strictness_interaction.csv](logit_strictness_interaction.csv) — 4개 모델 계수표 전체
- 토대 데이터: `v_compliance_results` (sql/06_dual_views.sql)
