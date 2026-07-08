"""감사 위험 상세 — kolas-audit-predictor explainability (v0.7.0).

v2 design 블록 3 구현. waterfall + scenario what-if + LLM reasoning + AI 권장 조치.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.agents import KolasAuditPredictorAgent, KolasMonitorAgent

st.set_page_config(
    page_title="감사 위험 상세 — MetroAI",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    """
    <style>
    .v2-brand-h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: #1E40AF;
        margin-bottom: 0.25rem;
        letter-spacing: -0.01em;
    }
    .v2-subtle {
        color: #475569;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .v2-risk-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.75rem;
        text-align: center;
    }
    .v2-risk-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 4rem;
        font-weight: 700;
        line-height: 1;
        margin: 0.5rem 0;
    }
    .v2-risk-label {
        font-size: 0.85rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .v2-confidence-bar {
        background: #E2E8F0;
        border-radius: 999px;
        height: 8px;
        margin: 0.75rem auto;
        overflow: hidden;
        max-width: 280px;
    }
    .v2-confidence-fill {
        background: linear-gradient(90deg, #1E40AF 0%, #06B6D4 100%);
        height: 100%;
        border-radius: 999px;
    }
    .v2-section-h {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E293B;
        margin: 1.5rem 0 0.75rem 0;
    }
    .v2-ai-card {
        background: rgba(6, 182, 212, 0.05);
        border-left: 3px solid #06B6D4;
        padding: 1rem 1.25rem;
        border-radius: 6px;
        font-size: 0.93rem;
        color: #0F172A;
        line-height: 1.6;
    }
    .v2-ai-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        background: #06B6D4;
        color: white;
        padding: 0.1rem 0.4rem;
        border-radius: 3px;
        margin-right: 0.4rem;
        vertical-align: middle;
    }
    .v2-rec-row {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #1E40AF;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .v2-rec-row.p0 { border-left-color: #EF4444; }
    .v2-rec-row.p1 { border-left-color: #F59E0B; }
    .v2-rec-row.p2 { border-left-color: #06B6D4; }
    .v2-rec-prio {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.1rem 0.4rem;
        border-radius: 3px;
        margin-right: 0.5rem;
    }
    .v2-rec-impact {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #10B981;
        font-weight: 600;
        float: right;
    }
    .v2-disclaimer {
        background: #FEF3C7;
        border-left: 3px solid #F59E0B;
        padding: 0.85rem 1rem;
        border-radius: 6px;
        font-size: 0.83rem;
        color: #1E293B;
        margin-top: 1.5rem;
    }
    .v2-model-meta {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        font-size: 0.85rem;
        color: #475569;
        font-family: 'JetBrains Mono', monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Header
# ──────────────────────────────────────────
st.markdown(
    "<div class='v2-brand-h1'>감사 위험 상세 · Explainability</div>"
    "<div class='v2-subtle'>kolas-audit-predictor 출력의 explainability. "
    "Scenario what-if · waterfall · AI reasoning · 권장 조치 우선순위.</div>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# 3-column layout
# ──────────────────────────────────────────
left, center, right = st.columns([1.4, 2, 1.4])

# ─── LEFT: Scenario inputs (What if?) ───
with left:
    st.markdown("<div class='v2-section-h'>시나리오 입력</div>", unsafe_allow_html=True)
    st.markdown("<div class='v2-subtle' style='font-size:0.85rem;'>입력 변경 시 우측 예측 즉시 갱신.</div>", unsafe_allow_html=True)

    sop = st.slider("SOP 완성도 (%)", 0, 100, 87, help="현재 SOP 23종 중 검토·승인 완료 비율")
    months = st.slider("마지막 감사 후 경과 (개월)", 0, 36, 9)
    turnover = st.slider("인력 회전율 (0–1, 추정)", 0.0, 1.0, 0.18, 0.05,
                         help="job-scout 에이전트 신호 + 본 기관 인력 변동")
    nc = st.number_input("최근 1년 부적합 수", 0, 20, 1)
    scope = st.number_input("인정범위 수", 1, 10, 2)
    methods = st.number_input("측정방법 수", 1, 100, 8)

    save_btn = st.button("이 시나리오 저장", use_container_width=True)
    if save_btn:
        if "saved_scenarios" not in st.session_state:
            st.session_state.saved_scenarios = []
        st.session_state.saved_scenarios.append({
            "sop": sop, "months": months, "turnover": turnover,
            "nc": nc, "scope": scope, "methods": methods,
        })
        st.success(f"저장됨 (총 {len(st.session_state.saved_scenarios)}건)")

# ─── Run agent with scenario ───
@st.cache_data(ttl=60, show_spinner=False)
def _predict(sop_completeness, months_since, turnover_sig, nonconf, scope_n, method_n):
    return KolasAuditPredictorAgent().run({
        "sop_completeness": sop_completeness / 100.0,
        "months_since_last_audit": months_since,
        "personnel_turnover_signal": turnover_sig,
        "recent_nonconformities": nonconf,
        "accreditation_scope_count": scope_n,
        "measurement_method_count": method_n,
    })


prediction = _predict(sop, months, turnover, nc, scope, methods)
risk = prediction.payload["risk_score"] * 100
confidence = prediction.payload["confidence"] * 100
contributors = prediction.payload["contributors"]
recommendations = prediction.payload["recommendations"]
reasoning = prediction.payload["reasoning"]
model_meta = prediction.payload["model_metadata"]
disclaimer = prediction.payload["disclaimer"]

# Risk color
if risk < 25:
    risk_color = "#10B981"  # green
elif risk < 50:
    risk_color = "#F59E0B"  # amber
else:
    risk_color = "#EF4444"  # red

# ─── CENTER: Prediction + waterfall ───
with center:
    st.markdown(
        f"""
        <div class='v2-risk-box'>
          <div class='v2-risk-label'>예측 감사 위험</div>
          <div class='v2-risk-value' style='color:{risk_color};'>{risk:.1f}%</div>
          <div class='v2-confidence-bar'>
            <div class='v2-confidence-fill' style='width:{confidence}%;'></div>
          </div>
          <div style='font-size:0.85rem;color:#475569;'>신뢰도 {confidence:.0f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Waterfall chart
    st.markdown("<div class='v2-section-h'>기여 요인 (waterfall)</div>", unsafe_allow_html=True)
    try:
        import altair as alt
        import pandas as pd

        df = pd.DataFrame(contributors)
        df["color"] = df["direction"].map({"up": "#EF4444", "down": "#10B981"})
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                y=alt.Y("factor:N", title=None, sort="-x"),
                x=alt.X("contribution_pct:Q", title="기여도 (pp)"),
                color=alt.Color(
                    "direction:N",
                    scale=alt.Scale(
                        domain=["up", "down"],
                        range=["#EF4444", "#10B981"],
                    ),
                    legend=None,
                ),
                tooltip=["factor", "contribution_pct", "direction"],
            )
            .properties(height=160)
            .configure_view(stroke=None)
        )
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        # Altair 미설치 시 fallback
        for c in contributors:
            arrow = "↑" if c["direction"] == "up" else "↓"
            color = "#EF4444" if c["direction"] == "up" else "#10B981"
            st.markdown(
                f"<div style='margin-bottom:0.4rem;'>"
                f"<span style='font-family:JetBrains Mono,monospace;color:{color};'>{arrow} {c['contribution_pct']:+.1f}pp</span> "
                f"<span style='color:#1E293B;'>{c['factor']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # AI reasoning
    st.markdown("<div class='v2-section-h'>AI Reasoning</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='v2-ai-card'>"
        f"<span class='v2-ai-badge'>AI</span>{reasoning}"
        f"</div>",
        unsafe_allow_html=True,
    )

# ─── RIGHT: Recommended actions ───
with right:
    st.markdown("<div class='v2-section-h'>AI 권장 조치</div>", unsafe_allow_html=True)
    st.markdown("<div class='v2-subtle' style='font-size:0.85rem;'>우선순위 + 예상 risk 감소율.</div>", unsafe_allow_html=True)
    for rec in recommendations:
        prio = rec["priority"]
        prio_cls = prio.lower()
        prio_bg = {"P0": "#FEE2E2", "P1": "#FEF3C7", "P2": "#E0F2FE"}.get(prio, "#E2E8F0")
        prio_fg = {"P0": "#EF4444", "P1": "#F59E0B", "P2": "#06B6D4"}.get(prio, "#475569")
        impact = rec.get("expected_risk_reduction_pct", 0)
        st.markdown(
            f"""
            <div class='v2-rec-row {prio_cls}'>
              <span class='v2-rec-prio' style='background:{prio_bg};color:{prio_fg};'>{prio}</span>
              <span class='v2-rec-impact'>-{impact:.1f}pp</span>
              <span style='font-size:0.92rem;color:#1E293B;'>{rec['action']}</span><br>
              <small style='color:#475569;font-family:JetBrains Mono,monospace;'>{rec['source_agent']}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("권장 조치를 작업으로 추가", use_container_width=True, type="primary"):
        st.success(f"{len(recommendations)}개 작업 등록됨 (orchestrator agent → 오늘의 작업).")

# ──────────────────────────────────────────
# Model metadata + disclaimer
# ──────────────────────────────────────────
st.markdown("---")
mc1, mc2 = st.columns([1.5, 1])
with mc1:
    st.markdown("<div class='v2-section-h'>Model metadata</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='v2-model-meta'>
        <strong>model_type:</strong> {model_meta.get('model_type', '?')}<br>
        <strong>model_version:</strong> {model_meta.get('model_version', '?')}<br>
        <strong>data_origin:</strong> {model_meta.get('data_origin', '?')}<br>
        <strong>honest_metric:</strong><br>
        <span style='display:block;padding-left:1rem;margin-top:0.3rem;'>{model_meta.get('honest_metric', '?')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mc2:
    st.markdown("<div class='v2-section-h'>Disclaimer</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='v2-disclaimer'>⚠️ {disclaimer}</div>",
        unsafe_allow_html=True,
    )

# Saved scenarios
if st.session_state.get("saved_scenarios"):
    st.markdown("<div class='v2-section-h'>저장된 시나리오</div>", unsafe_allow_html=True)
    import pandas as pd
    df_saved = pd.DataFrame(st.session_state.saved_scenarios)
    df_saved.index = [f"#{i+1}" for i in range(len(df_saved))]
    st.dataframe(df_saved, use_container_width=True)

st.caption(
    "본 페이지는 kolas-audit-predictor (baseline rule 또는 GBT) 의 explainability 출력입니다. "
    "AI 출력은 cyan 라벨. 최종 판단은 품질책임자가 수행해야 합니다."
)
