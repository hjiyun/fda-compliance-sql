"""Q8 보완 — 효과크기 지표 (Odds Ratio · Cramér's V).

기존 Q8 비례 z-검정("유의한가")을 **대체하지 않고 보완**한다("얼마나 큰가").
p값은 그대로 두고 효과크기를 나란히 덧붙인다.

데이터: v_compliance_us (단일국 US, Q8 과 동일). 분석 단위 = (제품 × 영양소).
그룹: Trusted(tags|top) / Inferred(name) / Other(other). 위반 = high (DV ≥ 20%).
INNER JOIN 정책으로 결측 영양소 행 자동 제외.

(1) OR — 4영양소 각각 2×2 {Trusted, Other} × {viol, no_viol}. (Inferred 제외, z-검정과 동일 비교)
    OR = odds(viol | Other) / odds(viol | Trusted)  → OR>1 = Other 위반 odds 더 높음.
    0 셀이면 Haldane-Anscombe(+0.5) 보정 후 노트. 효과크기 magnitude 는 φ(2×2)로 등급화.
(2) Cramér's V — (a) 3그룹×위반 (영양소별), (b) category×위반 (sodium).
    bias-corrected V (Bergsma 2013) 동반. Cohen 기준(df*=min(r,c)-1=1): 0.10/0.30/0.50.
"""
from __future__ import annotations

import os
import warnings
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from scipy.stats import chi2_contingency
from statsmodels.stats.contingency_tables import Table2x2

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
RESULTS = PROJECT_ROOT / "docs" / "results"

META_MAP = {"tags": "Trusted", "top": "Trusted", "name": "Inferred", "other": "Other"}
NUTRIENTS = ["sodium", "saturated_fat", "sugars", "energy"]


def grade(v: float) -> str:
    """Cohen 기준 (φ / Cramér's V, df*=1): 0.10 small · 0.30 medium · 0.50 large."""
    if v < 0.10:
        return "negligible"
    if v < 0.30:
        return "small"
    if v < 0.50:
        return "medium"
    return "large"


def cramers_v(chi2: float, n: int, r: int, c: int) -> tuple[float, float]:
    phi2 = chi2 / n
    V = sqrt(phi2 / (min(r, c) - 1))
    phi2c = max(0.0, phi2 - (r - 1) * (c - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    cc = c - (c - 1) ** 2 / (n - 1)
    Vc = sqrt(phi2c / (min(rc, cc) - 1))
    return V, Vc


def load() -> pd.DataFrame:
    conn = psycopg2.connect(
        host=os.environ["PG_HOST"], port=os.environ["PG_PORT"],
        dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )
    df = pd.read_sql(
        "SELECT product_id, category, category_source, nutrient_code, judgment "
        "FROM v_compliance_us", conn)
    conn.close()
    df["meta_group"] = df["category_source"].map(META_MAP)
    df = df.dropna(subset=["meta_group"]).copy()
    df["viol"] = (df["judgment"] == "high").astype(int)
    return df


def main():
    df = load()
    print(f"총 (제품×영양소) 행: {len(df)}")

    # 기존 z-검정 결과 (Trusted vs Other) 병합용
    zt = pd.read_csv(RESULTS / "q8_ztest_results.csv")
    zt = zt[zt.comparison == "Trusted vs Other"].set_index("nutrient")

    # ---------- 셀 빈도 ----------
    print("\n" + "=" * 70 + "\n  셀 빈도 (group × {no_viol, viol})\n" + "=" * 70)
    for nut in NUTRIENTS:
        d = df[df.nutrient_code == nut]
        t = pd.crosstab(d.meta_group, d.viol).reindex(["Trusted", "Inferred", "Other"])
        t.columns = ["no_viol", "viol"]
        print(f"\n[{nut}]  (min cell = {int(t.values.min())})")
        print(t.to_string())

    # ---------- (1) Odds Ratio (Other vs Trusted) ----------
    print("\n" + "=" * 70 + "\n  (1) Odds Ratio — Other vs Trusted (2×2)\n" + "=" * 70)
    or_rows = []
    for nut in NUTRIENTS:
        d = df[df.nutrient_code == nut]
        t = pd.crosstab(d.meta_group, d.viol)
        o_v, o_n = int(t.loc["Other", 1]), int(t.loc["Other", 0])
        t_v, t_n = int(t.loc["Trusted", 1]), int(t.loc["Trusted", 0])
        tab = np.array([[o_v, o_n], [t_v, t_n]], dtype=float)
        haldane = (tab == 0).any()
        if haldane:
            tab = tab + 0.5
        t2 = Table2x2(tab)
        OR = t2.oddsratio
        lo, hi = t2.oddsratio_confint()
        chi2, _, _, _ = chi2_contingency(np.array([[o_v, o_n], [t_v, t_n]]),
                                         correction=False)
        n22 = o_v + o_n + t_v + t_n
        phi = sqrt(chi2 / n22)
        z_dpp = -float(zt.loc[nut, "diff_pp"])     # Other - Trusted (= -(Trusted-Other))
        z_p = float(zt.loc[nut, "p_value"])
        or_rows.append({
            "nutrient": nut,
            "Other_viol": o_v, "Other_noviol": o_n,
            "Trusted_viol": t_v, "Trusted_noviol": t_n,
            "dpp_Other_minus_Trusted": round(z_dpp, 2),
            "z_p_value": z_p,
            "OR_Other_vs_Trusted": round(OR, 3),
            "OR_ci_lo": round(lo, 3), "OR_ci_hi": round(hi, 3),
            "phi": round(phi, 3), "phi_grade": grade(phi),
            "haldane": bool(haldane),
        })
    or_df = pd.DataFrame(or_rows)
    print(or_df.to_string(index=False))
    or_df.to_csv(RESULTS / "q8_effect_size_or.csv", index=False, encoding="utf-8")

    # ---------- (2) Cramér's V ----------
    print("\n" + "=" * 70 + "\n  (2a) Cramér's V — 3그룹(Trusted/Inferred/Other) × 위반\n" + "=" * 70)
    v_rows = []
    for nut in NUTRIENTS:
        d = df[df.nutrient_code == nut]
        t = pd.crosstab(d.meta_group, d.viol)
        chi2, p, dof, exp = chi2_contingency(t.values, correction=False)
        r, c = t.shape
        n = int(t.values.sum())
        V, Vc = cramers_v(chi2, n, r, c)
        v_rows.append({
            "table": f"3그룹 × 위반 ({nut})", "n": n, "shape": f"{r}x{c}",
            "chi2": round(chi2, 3), "p": p, "min_expected": round(exp.min(), 1),
            "cramers_V": round(V, 3), "V_biascorr": round(Vc, 3),
            "grade": grade(Vc),
        })
    # (2b) category × 위반 (sodium)
    ds = df[df.nutrient_code == "sodium"]
    t = pd.crosstab(ds.category, ds.viol)
    chi2, p, dof, exp = chi2_contingency(t.values, correction=False)
    r, c = t.shape
    n = int(t.values.sum())
    V, Vc = cramers_v(chi2, n, r, c)
    v_rows.append({
        "table": "category × 위반 (sodium)", "n": n, "shape": f"{r}x{c}",
        "chi2": round(chi2, 3), "p": p, "min_expected": round(exp.min(), 1),
        "cramers_V": round(V, 3), "V_biascorr": round(Vc, 3), "grade": grade(Vc),
    })
    v_df = pd.DataFrame(v_rows)
    print(v_df.to_string(index=False))
    print("\n[2b] category × 위반 (sodium) 분할표:")
    print(t.rename(columns={0: "no_viol", 1: "viol"}).to_string())
    v_df.to_csv(RESULTS / "q8_effect_size_cramersv.csv", index=False, encoding="utf-8")

    print(f"\n[saved] {RESULTS/'q8_effect_size_or.csv'}")
    print(f"[saved] {RESULTS/'q8_effect_size_cramersv.csv'}")


if __name__ == "__main__":
    main()
