"""Figure 4 — Sodium content distribution with 3-country thresholds.

Q10 의 핵심 발견 시각화: 한국 가공식품의 sodium 함량 분포 + US/EU/CODEX 임계값.
- 400 mg/100g 클러스터 (한국 식품 산업 표준점) 강조
- CODEX(400) 임계값에 정확히 도달하는 다수 제품 시각화
- "FDA 적합 → CODEX 위반" 95 케이스 영역 음영

Data: v_compliance_us (US country slice) 의 sodium 측정값 1,308 개.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

from plot_style import COLORS, save_figure, setup_plot_style


PROJECT_ROOT = Path(__file__).resolve().parents[2]


SQL = """
SELECT value_per_100g AS sodium_mg
FROM v_compliance_us
WHERE nutrient_code = 'sodium'
  AND value_per_100g IS NOT NULL
ORDER BY value_per_100g;
"""


def load_data() -> pd.Series:
    load_dotenv(PROJECT_ROOT / ".env")
    conn = psycopg2.connect(
        host=os.environ["PG_HOST"], port=os.environ["PG_PORT"],
        dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )
    df = pd.read_sql(SQL, conn)
    conn.close()
    return df["sodium_mg"].astype(float)


def main() -> None:
    setup_plot_style()
    s = load_data()

    n_total       = len(s)
    n_us_pass     = int((s < 460).sum())
    n_us_fail     = int((s >= 460).sum())
    n_codex_fail  = int((s >= 400).sum())
    n_us_ok_codex_fail = int(((s >= 400) & (s < 460)).sum())

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(11, 5.6))

    # Histogram (clip extreme outliers for readability — narrow band only)
    X_MAX = 1200  # mg/100g for axis (some products go higher, but uncommon)
    s_clip = s[s <= X_MAX]
    n_clipped = int((s > X_MAX).sum())

    bins = np.arange(0, X_MAX + 25, 25)
    counts, edges, patches = ax.hist(
        s_clip, bins=bins, color=COLORS["Trusted"], alpha=0.55,
        edgecolor="white", linewidth=0.6, zorder=2,
    )

    # Highlight the "US pass, CODEX fail" band (400 ≤ sodium < 460)
    ax.axvspan(400, 460, color=COLORS["Gap"], alpha=0.10, zorder=1,
               label=f"US pass / CODEX fail band  (n = {n_us_ok_codex_fail})")

    # Threshold vertical lines (CODEX 400 / US 460 / EU 480) — labelled via legend
    # (inline labels would overlap because thresholds are only 80 mg apart)
    thr = [("CODEX  400 mg", 400, COLORS["CODEX"]),
           ("US     460 mg", 460, COLORS["US"]),
           ("EU     480 mg", 480, COLORS["EU"])]
    y_top = counts.max() * 1.05
    for label, val, c in thr:
        ax.axvline(val, color=c, linestyle="--", linewidth=2.0,
                   alpha=0.85, zorder=4, label=label)

    # 400-cluster spike annotation — find the bin containing 400 exactly
    bin_idx_400 = int(400 // 25)  # bin starting at 400
    if bin_idx_400 < len(counts):
        spike_h = counts[bin_idx_400]
        arrow = FancyArrowPatch(
            (620, spike_h * 1.05), (412, spike_h * 1.02),
            arrowstyle="->", mutation_scale=18,
            color=COLORS["Gap"], linewidth=2.0, alpha=0.9, zorder=5,
        )
        ax.add_patch(arrow)
        ax.text(625, spike_h * 1.05,
                f"sodium = 400 mg / 100 g cluster\n"
                f"(industry standard point;\nCODEX threshold exactly met)",
                fontsize=9.5, color=COLORS["Gap"], fontweight="bold",
                va="center", ha="left")

    # Counts annotation (top-left)
    note = (
        f"n = {n_total:,} sodium measurements"
        f"{f' (truncated > {X_MAX} mg: {n_clipped})' if n_clipped else ''}\n"
        f"US pass: {n_us_pass:,}   ·   "
        f"US fail (≥ 460): {n_us_fail:,}\n"
        f"CODEX fail (≥ 400): {n_codex_fail:,}   ·   "
        f"of which US pass: {n_us_ok_codex_fail}"
    )
    # Place stats below the threshold legend on the right (Y axes fraction 0.62)
    # — avoids overlap with both the tall left bars and the top-right legend.
    ax.text(
        0.985, 0.62, note,
        transform=ax.transAxes, fontsize=9, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.5",
                  facecolor="white", edgecolor="#cccccc", alpha=0.95),
    )

    ax.set_xlabel("Sodium content (mg / 100 g)")
    ax.set_ylabel("Number of products")
    ax.set_xlim(0, X_MAX)
    ax.set_ylim(0, y_top * 1.18)
    ax.set_title(
        "Sodium content distribution in Korean processed foods "
        "with national thresholds",
        pad=12,
    )
    fig.text(
        0.5, 0.91,
        "The 400 mg / 100 g cluster aligns exactly with the CODEX threshold "
        "→ standard choice drives diagnosis outcomes",
        ha="center", fontsize=10, style="italic", color="#555555",
    )

    ax.legend(loc="upper right", bbox_to_anchor=(0.985, 0.97),
              frameon=True, fontsize=9, title="Thresholds",
              title_fontsize=9)
    ax.grid(True, axis="y", alpha=0.4)
    ax.set_axisbelow(True)

    plt.tight_layout(rect=(0, 0, 1, 0.93))
    out = save_figure(fig, "fig04_sodium_400_cluster")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
