"""Figure 1 — Sodium Other-Trusted gap by standard strictness.

Q9 (Week 4) 의 핵심 발견 시각화: sodium 임계값이 엄격해질수록 (480 → 460 → 400 mg/100g)
메타데이터 부재(Other) 그룹과 메타데이터 보유(Trusted) 그룹의 위반율 격차가 단조 증가.

Layout: 2 panels
    Left  — Slope chart (Trusted vs Other 두 라인 + 격차 영역 음영)
    Right — Gap bar chart (+9.29 → +10.98 → +13.80 pp, 단조 증가 강조)
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from plot_style import COLORS, save_figure, setup_plot_style


# ---------------------------------------------------------------------
# Data — Q9 결과 (sodium 만, 국가별 정렬은 임계값 큰→작 = 느슨→엄격)
# ---------------------------------------------------------------------
COUNTRIES   = ["EU", "US", "CODEX"]
THRESHOLDS  = [480, 460, 400]                 # mg / 100 g
TRUSTED_PCT = [24.20, 25.11, 31.51]
OTHER_PCT   = [33.49, 36.10, 45.31]
GAP_PP      = [9.29, 10.98, 13.80]


# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------
def main() -> None:
    setup_plot_style()

    fig, (ax_l, ax_r) = plt.subplots(
        1, 2, figsize=(11, 5), gridspec_kw={"width_ratios": [1.4, 1.0]}
    )

    # ---- Left panel: slope chart with shaded gap ----
    x = np.arange(len(COUNTRIES))
    ax_l.fill_between(
        x, TRUSTED_PCT, OTHER_PCT,
        color=COLORS["Gap"], alpha=0.12, label="Gap (Other − Trusted)",
        zorder=1,
    )
    ax_l.plot(
        x, TRUSTED_PCT, marker="o", markersize=9, linewidth=2.4,
        color=COLORS["Trusted"], label="Trusted (metadata)",
        zorder=3,
    )
    ax_l.plot(
        x, OTHER_PCT, marker="s", markersize=9, linewidth=2.4,
        color=COLORS["Other"], label="Other (mapping failed)",
        zorder=3,
    )

    # Point labels
    for xi, yi in zip(x, TRUSTED_PCT):
        ax_l.annotate(
            f"{yi:.2f}", (xi, yi), textcoords="offset points",
            xytext=(0, -16), ha="center", fontsize=9,
            color=COLORS["Trusted"], fontweight="bold",
        )
    for xi, yi in zip(x, OTHER_PCT):
        ax_l.annotate(
            f"{yi:.2f}", (xi, yi), textcoords="offset points",
            xytext=(0, 10), ha="center", fontsize=9,
            color=COLORS["Other"], fontweight="bold",
        )

    # X-tick labels: country + threshold
    ax_l.set_xticks(x)
    ax_l.set_xticklabels(
        [f"{c}\n({t} mg / 100 g)" for c, t in zip(COUNTRIES, THRESHOLDS)],
        fontsize=10,
    )
    ax_l.set_ylim(18, 50)
    ax_l.set_ylabel("Sodium violation rate (%)")
    ax_l.set_xlabel("Standard (threshold, less strict → stricter)")
    ax_l.set_title("Trusted vs Other groups across 3 standards",
                   fontsize=12, pad=10)
    ax_l.legend(loc="upper left", frameon=True, fontsize=9)
    ax_l.grid(True, axis="y", alpha=0.5)

    # ---- Right panel: gap bars ----
    bars = ax_r.bar(
        x, GAP_PP, width=0.55,
        color=[COLORS["EU"], COLORS["US"], COLORS["CODEX"]],
        edgecolor="white", linewidth=1.5,
    )

    # Gap value labels
    for xi, gi in zip(x, GAP_PP):
        ax_r.annotate(
            f"+{gi:.2f} pp", (xi, gi), textcoords="offset points",
            xytext=(0, 6), ha="center", fontsize=11, fontweight="bold",
            color=COLORS["Threshold"],
        )

    # Monotonic-trend arrow overlay
    ax_r.annotate(
        "", xy=(2, 15.5), xytext=(0, 10.0),
        arrowprops=dict(arrowstyle="->", color=COLORS["Gap"],
                        lw=2.2, alpha=0.7),
    )
    ax_r.text(
        1.0, 16.0, "monotonic ↑",
        ha="center", fontsize=10, color=COLORS["Gap"],
        fontweight="bold", style="italic",
    )

    ax_r.set_xticks(x)
    ax_r.set_xticklabels(COUNTRIES)
    ax_r.set_ylim(0, 17.5)
    ax_r.set_ylabel("Other − Trusted gap (pp)")
    ax_r.set_xlabel("Standard")
    ax_r.set_title("Gap widens as threshold tightens",
                   fontsize=12, pad=10)
    ax_r.grid(True, axis="y", alpha=0.5)

    # ---- Figure title ----
    fig.suptitle(
        "Sodium violation rate gap by standard strictness",
        y=1.02, fontsize=14, fontweight="bold",
    )
    fig.text(
        0.5, 0.965,
        "Metadata absence (Other) widens the gap with stricter sodium thresholds  "
        "(EU 480 → US 460 → CODEX 400 mg / 100 g)",
        ha="center", fontsize=10, style="italic", color="#555555",
    )

    plt.tight_layout(rect=(0, 0, 1, 0.94))
    out = save_figure(fig, "fig01_sodium_monotonic")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
