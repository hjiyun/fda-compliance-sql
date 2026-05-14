"""
Q8 — category_source 신뢰도와 위반율의 차이에 대한 통계 검증.

Pipeline:
    1) PostgreSQL 의 v_compliance_results + products 조회 → group × nutrient 위반율
    2) 비교쌍별 비례 z-검정 (statsmodels.proportions_ztest)
    3) 위반율 차이의 95% Wald 신뢰구간
    4) 결론: p < 0.05 AND |차이| > 10 pp → 'significant'

비교쌍 (8개):
    Trusted vs Other     × 4 영양소
    Trusted vs Inferred  × 4 영양소
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportions_ztest,
)

# ------------------------------------------------------------------
# 1) DB 연결 + Q8 SQL 실행
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

SQL_PATH = PROJECT_ROOT / "sql" / "queries" / "Q8.sql"

conn = psycopg2.connect(
    host=os.environ["PG_HOST"],
    port=os.environ["PG_PORT"],
    dbname=os.environ["PG_DB"],
    user=os.environ["PG_USER"],
    password=os.environ["PG_PASSWORD"],
)

with SQL_PATH.open(encoding="utf-8") as f:
    sql = f.read()

df = pd.read_sql(sql, conn)
conn.close()

print("=" * 72)
print("Q8 SQL 결과 (group × nutrient × violation_rate)")
print("=" * 72)
print(df.to_string(index=False))

# ------------------------------------------------------------------
# 2) 비교쌍별 z-test + 95% CI
# ------------------------------------------------------------------
NUTRIENTS = ["energy", "sugars", "saturated_fat", "sodium"]
COMPARISONS = [("Trusted", "Other"), ("Trusted", "Inferred")]

SIG_P = 0.05
SIG_DIFF_PP = 10.0  # 10 percentage points

rows = []
for grp_a, grp_b in COMPARISONS:
    for nutrient in NUTRIENTS:
        row_a = df.query("group_name == @grp_a and nutrient_code == @nutrient").iloc[0]
        row_b = df.query("group_name == @grp_b and nutrient_code == @nutrient").iloc[0]

        counts = np.array([row_a.high_count, row_b.high_count])
        nobs = np.array([row_a.total_n, row_b.total_n])

        # z-test (2-sided)
        zstat, pval = proportions_ztest(counts, nobs, alternative="two-sided")

        # 95% Wald CI for (p_a - p_b)
        ci_low, ci_high = confint_proportions_2indep(
            count1=row_a.high_count,
            nobs1=row_a.total_n,
            count2=row_b.high_count,
            nobs2=row_b.total_n,
            method="wald",
            compare="diff",
        )

        rate_a = row_a.high_count / row_a.total_n * 100
        rate_b = row_b.high_count / row_b.total_n * 100
        diff_pp = rate_a - rate_b

        is_significant = (pval < SIG_P) and (abs(diff_pp) > SIG_DIFF_PP)

        rows.append(
            {
                "comparison": f"{grp_a} vs {grp_b}",
                "nutrient": nutrient,
                "rate_a_pct": round(rate_a, 2),
                "rate_b_pct": round(rate_b, 2),
                "diff_pp": round(diff_pp, 2),
                "z_stat": round(zstat, 3),
                "p_value": round(pval, 6),
                "ci95_low_pp": round(ci_low * 100, 2),
                "ci95_high_pp": round(ci_high * 100, 2),
                "n_a": int(row_a.total_n),
                "n_b": int(row_b.total_n),
                "significant": is_significant,
            }
        )

result = pd.DataFrame(rows)

print()
print("=" * 72)
print("비례 z-검정 결과 + 95% Wald 신뢰구간 (rate_a - rate_b, pp 단위)")
print(f"기준: p < {SIG_P} AND |diff| > {SIG_DIFF_PP} pp")
print("=" * 72)
print(result.to_string(index=False))

# ------------------------------------------------------------------
# 3) 결과 저장 (CSV)
# ------------------------------------------------------------------
OUT_CSV = PROJECT_ROOT / "docs" / "results" / "q8_ztest_results.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUT_CSV, index=False)
print(f"\n[saved] {OUT_CSV.relative_to(PROJECT_ROOT)}")

# ------------------------------------------------------------------
# 4) 결론 요약
# ------------------------------------------------------------------
print()
print("=" * 72)
print("결론 요약")
print("=" * 72)
for _, r in result.iterrows():
    flag = "[YES] significant" if r.significant else "[ no] not significant"
    direction = (
        "(A>B)"
        if r.diff_pp > 0
        else "(A<B)"
        if r.diff_pp < 0
        else "(A=B)"
    )
    print(
        f"  [{flag}] {r.comparison:<22} {r.nutrient:<14} "
        f"diff = {r.diff_pp:+6.2f} pp {direction}  "
        f"p = {r.p_value:.4g}  "
        f"CI95 = [{r.ci95_low_pp:+.2f}, {r.ci95_high_pp:+.2f}] pp"
    )
