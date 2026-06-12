"""Figure 6 — 한국 식품 2,493건의 3국 라벨 부담 4대 패턴 (가로 막대).

Q11 결과 3 (Cross-country 라벨 부담 패턴, 제품 단위) 의 4개 주요 패턴을
건수 내림차순 가로 막대로. "924(3국 모두 safe)가 압도적" 을 한눈에.

값·라벨은 docs/results/Q11.md 결과 3 정의 기준 (Q11_full_diagnosis.csv 로 검증):
    924 = 3국 모두 safe                         (수출 친화)
    475 = 3국 모두 multiple_warning             (보편적 위반)
     64 = US·CODEX multiple, EU single 이하     (EU 단독 관대)  [61+3]
     19 = CODEX 만 multiple, US·EU safe/single  (CODEX 단독 엄격) [17+2]
    합 1,482 — 나머지는 중간 패턴 (전체 2,493건 중).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

from plot_style import save_figure, setup_plot_style

# 내림차순: 924 → 475 → 64 → 19
LABELS = [
    "3국 모두 safe\n(어느 시장에도 진출 가능)",
    "3국 모두 경고(multiple)\n(보편적 위반)",
    "EU 단독 관대\n(US·CODEX 경고, EU 이하)",
    "CODEX 단독 엄격\n(US·EU safe/single)",
]
COUNTS = [924, 475, 64, 19]

ACCENT = "#029E73"   # 강조색(초록) — 924
MUTED  = "#C9CDD2"   # 연한 회색 — 나머지


def _use_korean_font() -> None:
    path = Path(r"C:\Windows\Fonts\malgun.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        mpl.rcParams["font.family"] = "Malgun Gothic"
    mpl.rcParams["axes.unicode_minus"] = False


def main() -> None:
    setup_plot_style()
    _use_korean_font()

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    y = np.arange(len(COUNTS))
    colors = [ACCENT] + [MUTED] * (len(COUNTS) - 1)

    ax.barh(y, COUNTS, color=colors, edgecolor="white", linewidth=1.0, height=0.66)

    # 막대 끝 건수 라벨
    for yi, c in zip(y, COUNTS):
        ax.text(c + 14, yi, f"{c:,}건", va="center", ha="left",
                fontsize=11, fontweight="bold",
                color=ACCENT if yi == 0 else "#555555")

    ax.set_yticks(y)
    ax.set_yticklabels(LABELS, fontsize=10.5)
    ax.invert_yaxis()                       # 924 를 맨 위로
    ax.set_xlim(0, 1040)
    ax.set_xlabel("제품 수 (건)")
    ax.set_title("한국 식품 3국 라벨 부담 — 4대 패턴", fontsize=13, pad=10)
    ax.grid(True, axis="x", alpha=0.5)
    ax.grid(False, axis="y")

    # 단서: 합이 2,493 이 아님
    fig.text(0.985, 0.015,
             "4개 주요 패턴만 표시 · 전체 2,493건 중 (합 1,482건, 나머지는 중간 패턴)",
             ha="right", va="bottom", fontsize=8.5, style="italic", color="#888888")

    plt.tight_layout(rect=(0, 0.04, 1, 1))
    out = save_figure(fig, "fig06_burden_patterns")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
