"""Figure 3 — Category × Nutrient violation-rate heatmap (Q1-B, US).

Q1-B 결과: 6 카테고리 × 4 영양소 = 24 셀 의 high 위반율 (%).
Snacks · Sweets 의 압도적 위반율 (Snacks sat_fat 82.4 %, Sweets sugars 67.4 %) 가 한눈에.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

import matplotlib.pyplot as plt
import seaborn as sns

from plot_style import save_figure, setup_plot_style


PROJECT_ROOT = Path(__file__).resolve().parents[2]


SQL = """
SELECT
    COALESCE(category, '(Other)')                  AS category,
    nutrient_code,
    ROUND(
        COUNT(*) FILTER (WHERE judgment = 'high')::numeric
        / NULLIF(COUNT(*), 0) * 100, 2)            AS high_pct
FROM v_compliance_us
GROUP BY category, nutrient_code
ORDER BY category, nutrient_code;
"""

NUTRIENT_DISPLAY = {
    "energy":        "Energy",
    "saturated_fat": "Saturated Fat",
    "sodium":        "Sodium",
    "sugars":        "Sugars",
}
# 행 순서 — diagnose 수 큰 → 작 (Snacks 가 위반율 최고지만 n 작음 — Other 가 가장 큼)
CATEGORY_ORDER = ["Snacks", "Sweets", "Other", "Dairy", "Beverages", "Meals"]


def load_data() -> pd.DataFrame:
    load_dotenv(PROJECT_ROOT / ".env")
    conn = psycopg2.connect(
        host=os.environ["PG_HOST"], port=os.environ["PG_PORT"],
        dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )
    df = pd.read_sql(SQL, conn)
    conn.close()
    return df


def main() -> None:
    setup_plot_style()
    df = load_data()

    # Pivot to wide: rows = category, cols = nutrient
    df["nutrient_label"] = df["nutrient_code"].map(NUTRIENT_DISPLAY)
    pivot = df.pivot(index="category", columns="nutrient_label",
                     values="high_pct")
    pivot = pivot.reindex(CATEGORY_ORDER)
    pivot = pivot[["Sodium", "Sugars", "Saturated Fat", "Energy"]]

    fig, ax = plt.subplots(figsize=(8.2, 5.0))

    sns.heatmap(
        pivot, annot=True, fmt=".1f",
        cmap="YlOrRd", vmin=0, vmax=85,
        cbar_kws={"label": "Violation rate (%)", "shrink": 0.85},
        linewidths=0.6, linecolor="white",
        annot_kws={"fontsize": 11, "fontweight": "bold"},
        ax=ax,
    )

    ax.set_xlabel("Nutrient", labelpad=8)
    ax.set_ylabel("Category", labelpad=8)
    ax.set_title(
        "Violation rate by category × nutrient (US, FDA DV ≥ 20 %)",
        pad=14,
    )
    fig.text(
        0.5, 0.93,
        "Snacks and Sweets dominate; Snacks sat-fat 82.4 % is the project maximum",
        ha="center", fontsize=10, style="italic", color="#555555",
    )

    # X-tick labels: 회전 없이 가로
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)

    plt.tight_layout(rect=(0, 0, 1, 0.93))
    out = save_figure(fig, "fig03_category_heatmap")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
