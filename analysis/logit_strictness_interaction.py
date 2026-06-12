"""표준 강도 × 메타데이터 품질 교호작용 — 로지스틱 회귀 (Q8/Q10 보강).

목적:
    Q8(비례 z-검정)이 보인 "Other(메타데이터 부재) vs Trusted 의 sodium 위반율 격차"가
    "표준이 엄격해질수록 단조 확대"되는지를, 회귀 교호항으로 정식 검정한다.
    핵심은 meta_group × strictness 교호항 — 표준이 엄격해질 때 메타데이터 부재군의
    위반 확률이 추가로 더 오르는가.

데이터:
    v_compliance_results (다국가, 제품 × 영양소 × 국가). 분석 단위 = (제품, 국가).
    INNER JOIN 정책으로 결측 영양소 행은 자동 제외(0을 위반 아님으로 오집계하지 않음).

모델 (sodium, 이후 saturated_fat 비교):
    종속: is_violation = (judgment == 'high')  [DV ≥ 20%]
    설명: meta_group  — Trusted(tags|top, ref) / Inferred(name) / Other(other)
          strictness  — (a) 순서형 정수 EU=0,US=1,CODEX=2 (연속 취급)
                        (b) country 범주형 (ref=EU)
          교호항: meta_group × strictness
    통제: category — meta_group 과 완전 공선(category='Other' ⟺ meta='Other')이라 제외.
          (구조적 공선성으로 식별 불가 — 결과 노트에 명시)

통계:
    같은 제품이 3국에 반복 → 관측치 비독립.
    product_id 클러스터-로버스트 SE (cov_type='cluster').

주의:
    saturated_fat 은 3국 임계값이 모두 동일(4 g/100g)이라 strictness 가 국가 간
    변동이 없음 → 교호항이 구조적으로 정의되지 않음(degenerate). 비교용으로 그대로 보고.
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
import statsmodels.formula.api as smf
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

META_MAP = {"tags": "Trusted", "top": "Trusted", "name": "Inferred", "other": "Other"}
STRICT_ORD = {"EU": 0, "US": 1, "CODEX": 2}  # 엄격도 순서 (임계값 480→460→400)


def load(nutrient: str) -> pd.DataFrame:
    conn = psycopg2.connect(
        host=os.environ["PG_HOST"], port=os.environ["PG_PORT"],
        dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )
    df = pd.read_sql(
        "SELECT product_id, category, category_source, country_code, judgment "
        "FROM v_compliance_results WHERE nutrient_code = %(n)s",
        conn, params={"n": nutrient},
    )
    conn.close()
    df["meta_group"] = df["category_source"].map(META_MAP)
    df = df.dropna(subset=["meta_group"]).copy()  # 'free' 등 제외 (Q8 과 동일)
    df["is_violation"] = (df["judgment"] == "high").astype(int)
    df["strictness_ord"] = df["country_code"].map(STRICT_ORD)
    return df


def freq_table(df: pd.DataFrame, label: str) -> None:
    print(f"\n[{label}] 표본 행 {len(df)}  /  제품 {df.product_id.nunique()}")
    g = df.groupby(["meta_group", "country_code"]).agg(
        n=("is_violation", "size"), viol=("is_violation", "sum"))
    g["rate_pct"] = (g.viol / g.n * 100).round(1)
    print(g.to_string())


def tidy(res) -> pd.DataFrame:
    ci = res.conf_int()
    out = pd.DataFrame({
        "coef": res.params, "se": res.bse, "z": res.tvalues, "p": res.pvalues,
        "OR": np.exp(res.params),
        "OR_ci_lo": np.exp(ci[0]), "OR_ci_hi": np.exp(ci[1]),
    })
    return out.round(4)


def fit(df: pd.DataFrame, formula: str, label: str) -> pd.DataFrame:
    print("\n" + "=" * 78 + f"\n  {label}\n  {formula}\n" + "=" * 78)
    try:
        res = smf.logit(formula, data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["product_id"]}, disp=0)
    except Exception as e:  # 분리/특이행렬 등은 그대로 보고
        print(f"  [FIT FAILED] {type(e).__name__}: {e}")
        return pd.DataFrame()
    conv = getattr(res.mle_retvals, "get", lambda *_: None)("converged")
    print(f"  n = {int(res.nobs)}  clusters(product_id) = {df.product_id.nunique()}  "
          f"converged = {res.mle_retvals.get('converged')}  "
          f"pseudo-R2 = {res.prsquared:.4f}")
    t = tidy(res)
    print(t.to_string())
    t.insert(0, "model", label)
    t.insert(1, "term", t.index)
    return t


FORMULA_A = "is_violation ~ C(meta_group, Treatment('Trusted')) * strictness_ord"
FORMULA_B = ("is_violation ~ C(meta_group, Treatment('Trusted')) "
             "* C(country_code, Treatment('EU'))")


def main():
    all_tables = []
    for nutrient in ["sodium", "saturated_fat"]:
        print("\n" + "#" * 78 + f"\n#  {nutrient.upper()}\n" + "#" * 78)
        df = load(nutrient)
        freq_table(df, nutrient)
        # 임계값 국가 간 변동 확인 (saturated_fat 은 동일 → strictness 무변동)
        thr = (df.groupby("country_code")["strictness_ord"].first()
               if len(df) else None)
        all_tables.append(fit(df, FORMULA_A, f"{nutrient} (a) ordinal strictness"))
        all_tables.append(fit(df, FORMULA_B, f"{nutrient} (b) country categorical"))

    out = pd.concat([t for t in all_tables if not t.empty], ignore_index=True)
    out_csv = PROJECT_ROOT / "docs" / "results" / "logit_strictness_interaction.csv"
    out.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"\n[saved] {out_csv.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
