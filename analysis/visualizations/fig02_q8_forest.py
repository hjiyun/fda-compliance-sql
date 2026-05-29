"""Figure 2 — Q8 Forest plot (Other vs Trusted, by nutrient).

Q8 의 비례 z-검정 결과를 forest plot 으로 시각화.
- Y축: 4 영양소
- X축: Other − Trusted 비율 차이 (pp)
- 점: diff_pp / 가로 막대: 95 % Wald CI
- p<0.05 AND |diff|>10pp 인 결과를 강조 (실용 유의 기준)

Data source: docs/results/q8_ztest_results.csv (rate_a = Trusted, rate_b = Other 기준)
                                            → 표시 시 부호 반전하여 Other − Trusted 로 통일.
"""
from __future__ import annotations

import pandas as pd

import matplotlib.pyplot as plt

from plot_style import COLORS, RESULTS_DIR, save_figure, setup_plot_style


NUTRIENT_DISPLAY = {
    "sodium":        "Sodium",
    "saturated_fat": "Saturated Fat",
    "sugars":        "Sugars",
    "energy":        "Energy",
}
# 위에서 아래로 표시 순서 — sodium 을 맨 위로 (가설 지지 영양소)
DISPLAY_ORDER = ["sodium", "saturated_fat", "sugars", "energy"]


def main() -> None:
    setup_plot_style()

    # ----- Load & filter Q8 CSV -----
    df = pd.read_csv(RESULTS_DIR / "q8_ztest_results.csv")
    df = df[df["comparison"] == "Trusted vs Other"].copy()

    # Sign flip: CSV is Trusted − Other; we want Other − Trusted
    df["diff_ot"]    = -df["diff_pp"]
    df["ci_low_ot"]  = -df["ci95_high_pp"]
    df["ci_high_ot"] = -df["ci95_low_pp"]

    # Apply display order
    df["order"] = df["nutrient"].map({n: i for i, n in enumerate(DISPLAY_ORDER)})
    df = df.sort_values("order").reset_index(drop=True)

    # ----- Plot — wide figure, label column reserved on right -----
    fig, ax = plt.subplots(figsize=(12.0, 5.6))
    plt.subplots_adjust(left=0.13, right=0.68, top=0.80, bottom=0.22)

    y_pos = list(range(len(df)))

    for y, (_, row) in zip(y_pos, df.iterrows()):
        is_sig = row["p_value"] < 0.05 and abs(row["diff_ot"]) > 10
        color  = COLORS["Gap"] if is_sig else COLORS["Inferred"]
        ms     = 13 if is_sig else 9
        lw     = 3.0 if is_sig else 2.0
        alpha  = 1.0 if is_sig else 0.65

        # CI bar
        ax.plot(
            [row["ci_low_ot"], row["ci_high_ot"]], [y, y],
            color=color, linewidth=lw, alpha=alpha, solid_capstyle="round",
            zorder=2,
        )
        # CI end caps
        for x_end in (row["ci_low_ot"], row["ci_high_ot"]):
            ax.plot([x_end, x_end], [y - 0.12, y + 0.12],
                    color=color, linewidth=lw, alpha=alpha, zorder=2)
        # Point
        ax.scatter([row["diff_ot"]], [y], s=ms ** 2, color=color,
                   edgecolor="white", linewidth=1.5, zorder=3,
                   marker="D" if is_sig else "o")

        # Labels — placed in the reserved right column via axes-fraction transform
        label = f"{row['diff_ot']:+.2f} pp,  p = {row['p_value']:.4f}"
        if is_sig:
            label += "  ★"
        ax.annotate(
            label,
            xy=(1.015, y), xycoords=("axes fraction", "data"),
            va="center", ha="left", fontsize=10.5,
            color=color, fontweight="bold" if is_sig else "normal",
            annotation_clip=False,
        )

    # Y-axis: nutrient names
    ax.set_yticks(y_pos)
    ax.set_yticklabels([NUTRIENT_DISPLAY[n] for n in df["nutrient"]],
                       fontsize=11)
    ax.invert_yaxis()  # first → top

    # Reference line at 0
    ax.axvline(0, color=COLORS["Threshold"], linestyle="--",
               linewidth=1.2, alpha=0.6, zorder=1)
    # Effect-size threshold lines at ±10 pp
    ax.axvline(-10, color=COLORS["Gap"], linestyle=":",
               linewidth=1.0, alpha=0.45, zorder=1)
    ax.axvline(+10, color=COLORS["Gap"], linestyle=":",
               linewidth=1.0, alpha=0.45, zorder=1)

    ax.set_xlim(-25, 25)
    ax.set_ylim(len(df) - 0.5, -0.5)  # invert with extra padding

    # X-axis: in-axis label for ±10 pp markers (just above x-axis tick line)
    ax.annotate("−10 pp", xy=(-10, len(df) - 0.55),
                xycoords="data", ha="center", va="bottom",
                fontsize=8, color=COLORS["Gap"], alpha=0.75)
    ax.annotate("+10 pp", xy=(+10, len(df) - 0.55),
                xycoords="data", ha="center", va="bottom",
                fontsize=8, color=COLORS["Gap"], alpha=0.75)

    ax.set_xlabel("Violation-rate difference: Other − Trusted (pp,  95 % CI)",
                  labelpad=14)

    # Direction labels — below x-axis label
    ax.annotate("← Trusted higher", xy=(0.02, -0.22),
                xycoords="axes fraction", fontsize=10,
                color=COLORS["Trusted"], style="italic")
    ax.annotate("Other higher →", xy=(0.65, -0.22),
                xycoords="axes fraction", fontsize=10,
                color=COLORS["Other"], style="italic")

    # Use suptitle + subtitle in figure-text, well above the axes
    fig.suptitle(
        "Category-metadata effect on nutrient violation rate "
        "(US, n = 2,493 products)",
        y=0.95, fontsize=13.5, fontweight="bold",
    )
    fig.text(
        0.5, 0.885,
        "★ = significant (p < 0.05 AND |diff| > 10 pp).  "
        "Dotted vertical lines mark the ±10 pp effect-size threshold.",
        ha="center", fontsize=9.5, style="italic", color="#555555",
    )

    ax.grid(True, axis="x", alpha=0.4)
    ax.set_axisbelow(True)

    out = save_figure(fig, "fig02_q8_forest")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
