"""공통 시각화 스타일 — 표준학개론 2차 프로젝트 보고서용.

- 영문 라벨 전제 (한글 폰트 미사용)
- 정적 PNG 출력, 300 DPI
- 색약 친화 팔레트 (seaborn 'colorblind' 기반 + 의미 매핑)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


# ----------------------------------------------------------------------
# 출력 경로 — 본 모듈을 import 한 스크립트가 어디서 실행되어도 동일하게 작동
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"
RESULTS_DIR = PROJECT_ROOT / "docs" / "results"


# ----------------------------------------------------------------------
# 색약 친화 의미 색상 매핑 (seaborn colorblind 팔레트 기반)
#   Trusted (메타데이터 신뢰) — 청색
#   Other   (매핑 실패)       — 주황색
#   Inferred (이름 추론)      — 회색
#   Gap / Highlight           — 자홍색
#   Threshold line            — 짙은 회색
# ----------------------------------------------------------------------
COLORS = {
    "Trusted":   "#0173B2",   # blue
    "Other":     "#DE8F05",   # orange
    "Inferred":  "#949494",   # gray
    "Gap":       "#CC3311",   # red-ish for emphasis
    "Threshold": "#333333",   # near-black
    "Background":"#F5F5F5",   # light gray
    "Grid":      "#E0E0E0",
    "US":        "#0173B2",
    "EU":        "#029E73",   # teal-green
    "CODEX":     "#CC3311",   # red (strictest)
}


def setup_plot_style() -> None:
    """프로젝트 전역 matplotlib rcParams 설정. 각 스크립트 진입 시 1회 호출."""
    sns.set_theme(style="whitegrid", context="paper", palette="colorblind")

    mpl.rcParams.update({
        # Fonts (영문)
        "font.family":      "DejaVu Sans",
        "font.size":        11,
        "axes.titlesize":   13,
        "axes.titleweight": "bold",
        "axes.labelsize":   11,
        "axes.labelweight": "regular",
        "xtick.labelsize":  10,
        "ytick.labelsize":  10,
        "legend.fontsize":  10,
        "figure.titlesize": 14,
        "figure.titleweight":"bold",

        # 색상·그리드
        "axes.edgecolor":   "#333333",
        "axes.linewidth":   0.8,
        "grid.color":       COLORS["Grid"],
        "grid.linewidth":   0.6,
        "grid.alpha":       0.7,

        # 저장
        "savefig.dpi":      300,
        "savefig.bbox":     "tight",
        "savefig.facecolor":"white",

        # 화면 표시
        "figure.dpi":       100,
        "figure.facecolor": "white",
    })


def get_color_palette(kind: str = "group") -> dict[str, str]:
    """의미 그룹별 색상 사전 반환.

    kind:
        'group'   — Trusted / Inferred / Other
        'country' — US / EU / CODEX
    """
    if kind == "group":
        return {k: COLORS[k] for k in ("Trusted", "Inferred", "Other")}
    if kind == "country":
        return {k: COLORS[k] for k in ("US", "EU", "CODEX")}
    raise ValueError(f"unknown palette kind: {kind}")


def save_figure(fig, name: str) -> Path:
    """fig 를 docs/figures/{name}.png 로 저장. 경로 반환."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / f"{name}.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    return out
