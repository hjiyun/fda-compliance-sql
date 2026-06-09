"""한국 식품 다국가 라벨링 사전 점검 도구 (Streamlit MVP).

표준학개론 2차 프로젝트 — 본 연구 보고서 5.2.3 절 (a) 및 5.4.3 셋째 항목의
실무 활용 사례 구현.

영양 성분 4 종(나트륨 · 당류 · 포화지방 · 에너지) 을 100 g 기준으로 입력받아
미국 FDA · 유럽 EU · 국제 CODEX 의 3 국 라벨 표시 의무를 실시간 판정한다.

실행:
    streamlit run app/app.py

참조:
    - 보고서 4.4 절: 라벨 표시 의무 전수 진단 (Q11)
    - 보고서 5.2.3 절: 룰 기반 접근의 적합성평가 실무 함의
    - 데이터 출처: nutrient_limits 테이블 (3 국 × 4 영양소 = 12 행),
      docs/results/Q11_full_diagnosis.csv (7,479 행, 본 도구 외부 참조용)
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# 상수 — sql/nutrient_limits 테이블의 12 행을 dict 로 임베드.
#         PostgreSQL 의존성 회피 (Streamlit Cloud 호스팅 시 비용 0).
# ============================================================
NUTRIENT_LIMITS: dict[tuple[str, str], dict] = {
    # (country_code, nutrient_code) → daily_value · high_threshold_100g · unit · source
    ('US', 'sodium'):        {'dv': 2300, 'th100g': 460, 'unit': 'mg',   'source': '21 CFR 101.9'},
    ('US', 'sugars'):        {'dv':   50, 'th100g':  10, 'unit': 'g',    'source': '21 CFR 101.9 (added)'},
    ('US', 'saturated_fat'): {'dv':   20, 'th100g':   4, 'unit': 'g',    'source': '21 CFR 101.9'},
    ('US', 'energy'):        {'dv': 2000, 'th100g': 400, 'unit': 'kcal', 'source': '21 CFR 101.9'},

    ('EU', 'sodium'):        {'dv': 2400, 'th100g': 480, 'unit': 'mg',   'source': 'Reg. (EU) 1169/2011'},
    ('EU', 'sugars'):        {'dv':   90, 'th100g':  18, 'unit': 'g',    'source': 'Reg. (EU) 1169/2011 (total)'},
    ('EU', 'saturated_fat'): {'dv':   20, 'th100g':   4, 'unit': 'g',    'source': 'Reg. (EU) 1169/2011'},
    ('EU', 'energy'):        {'dv': 2000, 'th100g': 400, 'unit': 'kcal', 'source': 'Reg. (EU) 1169/2011'},

    ('CODEX', 'sodium'):        {'dv': 2000, 'th100g': 400, 'unit': 'mg',   'source': 'CAC/GL 2-1985 (NRV-NCD)'},
    ('CODEX', 'sugars'):        {'dv':   50, 'th100g':  10, 'unit': 'g',    'source': 'WHO Sugars Guideline 2015 (free)'},
    ('CODEX', 'saturated_fat'): {'dv':   20, 'th100g':   4, 'unit': 'g',    'source': 'CAC/GL 2-1985 (NRV-NCD)'},
    ('CODEX', 'energy'):        {'dv': 2000, 'th100g': 400, 'unit': 'kcal', 'source': 'WHO Recommendation'},
}

COUNTRIES = ['US', 'EU', 'CODEX']
NUTRIENTS = ['sodium', 'sugars', 'saturated_fat', 'energy']


# ============================================================
# 한국어 매핑 (UI 표시용 — 데이터 키 자체는 영문 유지)
# ============================================================
NUTRIENT_KR = {
    'sodium':        '나트륨',
    'sugars':        '당류',
    'saturated_fat': '포화지방',
    'energy':        '에너지',
}

NUTRIENT_UNIT = {
    'sodium': 'mg', 'sugars': 'g', 'saturated_fat': 'g', 'energy': 'kcal',
}

JUDGMENT_KR = {
    'low':      '적합 (DV 5 % 미만)',
    'moderate': '주의 (DV 5–20 %)',
    'high':     '위반 (DV 20 % 이상)',
}

COUNTRY_KR = {
    'US':    '🇺🇸 미국 (FDA)',
    'EU':    '🇪🇺 유럽 (EU)',
    'CODEX': '🌍 국제 (CODEX/WHO)',
}

BURDEN_KR = {
    'safe':              '✅ 라벨 의무 없음',
    'single_warning':    '⚠️ 1 영양소 경고',
    'multiple_warning':  '🚨 2+ 영양소 경고',
}

BURDEN_SHORT_EN = {  # 보고서와 동일 키 — 코드/CSV 호환용
    'safe':              'safe',
    'single_warning':    'single_warning',
    'multiple_warning':  'multiple_warning',
}


# ============================================================
# 예시 시나리오 (3 종, 사이드바 버튼)
# 보고서 핵심 발견과 1:1 매핑.
# ============================================================
SCENARIOS = {
    '🍜 Shin Ramyun (보편적 위반)':
        {'sodium': 1790.0, 'sugars': 6.0, 'saturated_fat': 9.0, 'energy': 503.0,
         'desc': '3 국 모두 multiple_warning. 보고서 4.2.1 절 영양소별 위반률.'},
    '🥡 400 mg 클러스터 (비대칭)':
        {'sodium':  400.0, 'sugars': 5.0, 'saturated_fat': 3.0, 'energy': 250.0,
         'desc': 'US · EU safe / CODEX 만 multi. 보고서 4.3.2 절 + 5.2.3 (b).'},
    '✅ 글로벌 안전권 (3 국 safe)':
        {'sodium':  100.0, 'sugars': 5.0, 'saturated_fat': 2.0, 'energy': 200.0,
         'desc': '3 국 모두 safe (924 건 안전권). 보고서 4.4.3 절 + 5.2.3 (a).'},
}


# ============================================================
# 진단 로직
# ============================================================
def judge(value: float, country: str, nutrient: str) -> tuple[str, float]:
    """(judgment, percent_dv) 반환.

    판정 기준은 21 CFR 101.13 의 5 % / 20 % DV 기준 — 모든 국가 공통.
    임계값(daily_value) 만 국가별로 다름.
    """
    dv = NUTRIENT_LIMITS[(country, nutrient)]['dv']
    pct = value / dv * 100.0
    if pct >= 20:
        return 'high', pct
    if pct >= 5:
        return 'moderate', pct
    return 'low', pct


def burden_level(high_count: int) -> str:
    """제품의 4 영양소 중 high 판정 개수 → label_burden_level (보고서 4.4 절 정의)."""
    if high_count == 0:
        return 'safe'
    if high_count == 1:
        return 'single_warning'
    return 'multiple_warning'


# ============================================================
# Streamlit UI
# ============================================================
def init_session_state() -> None:
    defaults = {
        'input_sodium':        0.0,
        'input_sugars':        0.0,
        'input_saturated_fat': 0.0,
        'input_energy':        0.0,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def render_sidebar() -> None:
    with st.sidebar:
        st.header("📋 예시 시나리오")
        st.caption("발표 시연용 — 한 번의 클릭으로 입력값 자동 채움.")

        for name, payload in SCENARIOS.items():
            if st.button(name, use_container_width=True):
                for k in NUTRIENTS:
                    st.session_state[f'input_{k}'] = float(payload[k])
            st.caption(payload['desc'])

        st.divider()
        st.header("ℹ️ 본 도구 정보")
        st.markdown(
            """
**출처**: 표준학개론 2차 프로젝트 (홍지윤, 빅데이터사이언스학과 석사과정)

**분석 데이터**: Open Food Facts 한국 식품 2,493 건의 다국가 적합성 진단 결과
[(Q11.md)](https://github.com/hjiyun/fda-compliance-sql/blob/main/docs/results/Q11.md)

**임계값 근거**:
- US — 21 CFR 101.9 (DV ≥ 20 % = "high in ...")
- EU — Regulation (EU) No 1169/2011
- CODEX — CAC/GL 2-1985 + WHO 권고

⚠️ **한계** — 본 판정은 100 g 기준 통일한 surrogate 지표이며,
FDA 의 공식 RACC 기반 표시 자격과 정확히 일치하지 않습니다.
상세는 보고서 5.3.3 절 참조.
            """
        )


def render_inputs() -> dict[str, float]:
    st.subheader("1️⃣ 영양 성분 입력 (100 g 기준)")
    c1, c2, c3, c4 = st.columns(4)
    return {
        'sodium':        c1.number_input("🧂 나트륨 (mg)",
                            min_value=0.0, max_value=10000.0, step=10.0,
                            key='input_sodium'),
        'sugars':        c2.number_input("🍬 당류 (g)",
                            min_value=0.0, max_value=100.0,   step=1.0,
                            key='input_sugars'),
        'saturated_fat': c3.number_input("🧈 포화지방 (g)",
                            min_value=0.0, max_value=100.0,   step=0.5,
                            key='input_saturated_fat'),
        'energy':        c4.number_input("⚡ 에너지 (kcal)",
                            min_value=0.0, max_value=4000.0,  step=10.0,
                            key='input_energy'),
    }


def diagnose(inputs: dict[str, float]) -> tuple[dict, dict[str, int]]:
    """results[country][nutrient] = (judgment, pct_dv, th100g) + high_counts[country]."""
    results: dict[str, dict[str, tuple[str, float, float]]] = {}
    high_counts: dict[str, int] = {}
    for country in COUNTRIES:
        results[country] = {}
        high_n = 0
        for nutrient in NUTRIENTS:
            judgment, pct = judge(inputs[nutrient], country, nutrient)
            th = NUTRIENT_LIMITS[(country, nutrient)]['th100g']
            results[country][nutrient] = (judgment, pct, th)
            if judgment == 'high':
                high_n += 1
        high_counts[country] = high_n
    return results, high_counts


def render_burden_cards(high_counts: dict[str, int]) -> None:
    st.subheader("2️⃣ 3 국 라벨 부담 판정")
    cols = st.columns(3)
    for col, country in zip(cols, COUNTRIES):
        level = burden_level(high_counts[country])
        with col:
            st.metric(
                label=COUNTRY_KR[country],
                value=BURDEN_KR[level],
                delta=f"high {high_counts[country]} / 4 영양소",
                delta_color="off",
            )


def render_diagnosis_table(inputs: dict[str, float], results: dict) -> None:
    st.subheader("3️⃣ 영양소 × 국가 진단 표")
    rows = []
    for nutrient in NUTRIENTS:
        unit = NUTRIENT_UNIT[nutrient]
        row = {'영양소': NUTRIENT_KR[nutrient],
               '입력값 (per 100g)': f"{inputs[nutrient]:.1f} {unit}"}
        for country in COUNTRIES:
            judgment, pct, th = results[country][nutrient]
            row[COUNTRY_KR[country]] = (
                f"{JUDGMENT_KR[judgment]}  ·  {pct:.1f} % DV  ·  임계 {th} {unit}"
            )
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_chart(results: dict) -> None:
    st.subheader("4️⃣ 국가별 % Daily Value")
    fig = go.Figure()
    palette = {'US': '#0173B2', 'EU': '#029E73', 'CODEX': '#CC3311'}
    for country in COUNTRIES:
        pcts = [results[country][n][1] for n in NUTRIENTS]
        fig.add_trace(go.Bar(
            name=COUNTRY_KR[country],
            x=[NUTRIENT_KR[n] for n in NUTRIENTS],
            y=pcts,
            text=[f"{p:.1f}%" for p in pcts],
            textposition='outside',
            marker_color=palette[country],
        ))
    fig.add_hline(y=20, line_dash="dash", line_color="#CC3311",
                  annotation_text="20 % DV (high 임계)",
                  annotation_position="top right")
    fig.add_hline(y=5,  line_dash="dot",  line_color="gray",
                  annotation_text="5 % DV (low/moderate 경계)",
                  annotation_position="top right")
    fig.update_layout(
        barmode='group',
        yaxis_title="% Daily Value",
        xaxis_title="영양소",
        height=420,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_recommendation(inputs: dict[str, float], results: dict,
                           high_counts: dict[str, int]) -> None:
    st.subheader("5️⃣ 권장 조치")
    any_high = any(high_counts[c] > 0 for c in COUNTRIES)
    if not any_high:
        st.success(
            "✅ **3 국 모두 라벨 표시 의무 없음** — 입력된 영양 성분 기준으로 "
            "가장 엄격한 CODEX 표준에서도 라벨 표시 의무가 발생하지 않습니다. "
            "본 제품은 *글로벌 수출 안전권* 에 해당합니다 (보고서 4.4.3 절)."
        )
        return

    recs = []
    for country in COUNTRIES:
        for nutrient in NUTRIENTS:
            judgment, pct, th = results[country][nutrient]
            if judgment == 'high':
                unit = NUTRIENT_UNIT[nutrient]
                delta = inputs[nutrient] - th
                recs.append({
                    '국가': COUNTRY_KR[country],
                    '영양소': NUTRIENT_KR[nutrient],
                    '현재값': f"{inputs[nutrient]:.1f} {unit}",
                    '임계값 (high 진입)': f"{th} {unit}",
                    '감축 권장 (high → moderate)': f"{delta:.1f} {unit} 초과",
                })
    st.warning(
        "⚠️ **다음 영양소가 라벨 표시 의무를 유발합니다.** "
        "각 국가 임계값 아래로 감축 시 high 판정에서 벗어납니다 "
        "(권장량은 *현재값 − 임계값* 의 단순 차이 — 보고서 5.4.1 절의 "
        "Level 2 점수 시스템은 향후 과제)."
    )
    st.dataframe(pd.DataFrame(recs), use_container_width=True, hide_index=True)


def render_footer() -> None:
    st.divider()
    st.caption(
        "🔬 본 도구는 본 연구의 SQL 룰 엔진을 Streamlit MVP 로 포팅한 "
        "*실무 활용 사례* 입니다. 전체 데이터·코드: "
        "[GitHub 레포지토리](https://github.com/hjiyun/fda-compliance-sql)"
    )


def main() -> None:
    st.set_page_config(
        page_title="한국 식품 다국가 라벨링 사전 점검",
        page_icon="🥢",
        layout="wide",
    )

    init_session_state()

    st.title("🥢 한국 식품 다국가 라벨링 사전 점검 도구")
    st.caption(
        "100 g 기준 영양 성분 4 종을 입력하면 "
        "**미국 FDA · 유럽 EU · 국제 CODEX** 3 국의 "
        "라벨 표시 의무를 실시간 판정합니다."
    )

    render_sidebar()
    inputs = render_inputs()
    results, high_counts = diagnose(inputs)
    render_burden_cards(high_counts)
    render_diagnosis_table(inputs, results)
    render_chart(results)
    render_recommendation(inputs, results, high_counts)
    render_footer()


if __name__ == "__main__":
    main()
