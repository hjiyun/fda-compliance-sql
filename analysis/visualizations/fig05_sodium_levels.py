"""Figure 5 — Sodium: Other consistently above Trusted across 3 standards.

fig01(격차 강조) 의 대체 버전. "격차 확대(gap widens)" 메시지를 제거하고
"세 표준 모두에서 Other 가 일관되게 위쪽" 이라는 사실만 남긴다.

fig01 과의 차이:
    - 두 선 사이 음영(Gap 영역) 제거
    - 'monotonic' / 'gap widens' / 화살표 / 격차 수치(+9.3/+11.0/+13.8) 전부 제거
    - 점 라벨은 절대 위반율(%) 만 (격차 아님)
    - Other 강조(진한 초록·굵은 선), Trusted 연한 회색·가는 선
    - 단일 패널 (우측 막대 없음)

값은 회귀 보고서 셀 표 기준(소수 1자리): Trusted 24.2/25.1/31.5, Other 33.5/36.1/45.3.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

from plot_style import COLORS, save_figure, setup_plot_style

# ---------------------------------------------------------------------
# Data — sodium, 임계값 느슨(EU 480) → 엄격(CODEX 400)
# ---------------------------------------------------------------------
COUNTRIES   = ["EU", "US", "CODEX"]
THRESHOLDS  = [480, 460, 400]            # mg / 100 g
TRUSTED_PCT = [24.2, 25.1, 31.5]         # 메타데이터 보유
OTHER_PCT   = [33.5, 36.1, 45.3]         # 메타데이터 부재

OTHER_COLOR   = COLORS["Other"]           # 주황 (#DE8F05, 원래 fig01 팔레트) — 강조
TRUSTED_COLOR = COLORS["Trusted"]         # 파랑 (#0173B2, 원래 fig01 팔레트)


def _use_korean_font() -> None:
    """범례·축 한글용 Malgun Gothic 등록 (Windows)."""
    path = Path(r"C:\Windows\Fonts\malgun.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        mpl.rcParams["font.family"] = "Malgun Gothic"
    mpl.rcParams["axes.unicode_minus"] = False


def main() -> None:
    setup_plot_style()
    _use_korean_font()

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    x = np.arange(len(COUNTRIES))

    # 두 선 (음영 없음)
    ax.plot(x, TRUSTED_PCT, marker="o", markersize=7, linewidth=1.8,
            color=TRUSTED_COLOR, label="Trusted (메타데이터 보유)", zorder=3)
    ax.plot(x, OTHER_PCT, marker="o", markersize=9.5, linewidth=3.2,
            color=OTHER_COLOR, label="Other (메타데이터 부재)", zorder=4)

    # 점 라벨 — 절대 위반율(%) 만
    for xi, yi in zip(x, OTHER_PCT):
        ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=10.5,
                    color=OTHER_COLOR, fontweight="bold")
    for xi, yi in zip(x, TRUSTED_PCT):
        ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points",
                    xytext=(0, -17), ha="center", fontsize=10.5,
                    color=TRUSTED_COLOR, fontweight="bold")

    # 축
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n{t}" for c, t in zip(COUNTRIES, THRESHOLDS)],
                       fontsize=11)
    ax.set_xlim(-0.32, 2.32)
    ax.set_ylim(0, 50)
    ax.set_xlabel("표준 임계값 (mg / 100 g, 느슨 → 엄격)", labelpad=8)
    ax.set_ylabel("Sodium 위반율 (%)")
    ax.set_title("Other > Trusted across all three standards (sodium)",
                 fontsize=13, pad=12)
    ax.legend(loc="upper left", frameon=True, fontsize=10.5)
    ax.grid(True, axis="y", alpha=0.5)
    ax.grid(False, axis="x")

    plt.tight_layout()
    out = save_figure(fig, "fig05_sodium_levels")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
