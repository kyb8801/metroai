"""숙련도시험(PT) 분석 페이지."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.modules.pt_analyzer import analyze_pt, analyze_pt_batch

st.set_page_config(
    page_title="MetroAI — PT 분석",
    page_icon="📊",
    layout="wide",
)

st.header("📊 숙련도시험(PT) 분석")
st.markdown("ISO 13528 / ISO 17043 기반 z-score, En number, ζ-score 자동 판정")

# ──────────────────────────────────────────
# 초보자 가이드 (NEW — v0.5.0)
# ──────────────────────────────────────────
with st.expander("💡 **숙련도시험(PT)이란? — 처음이신 분은 꼭 읽어보세요**", expanded=True):
    st.markdown(
        """
        **KOLAS 인정기관은 정기적으로 숙련도시험(PT)에 참가해야 합니다.**

        쉽게 말하면: 같은 시료를 여러 기관이 측정하고,
        **우리 기관의 결과가 다른 기관들과 얼마나 일치하는지** 확인하는 것입니다.

        ---

        **📌 판정 기준 요약:**

        | 지표 | 계산 방식 | 판정 |
        |------|-----------|------|
        | **z-score** | (우리 측정값 − 배정값) ÷ σ_pt | \\|z\\| < 2: 만족, 2~3: 주의, > 3: 불만족 |
        | **En number** | (우리 측정값 − 배정값) ÷ √(U_lab² + U_ref²) | \\|En\\| < 1: 적합 |
        | **ζ-score** | (우리 측정값 − 배정값) ÷ √(u_lab² + u_ref²) | \\|ζ\\| < 2: 적합 |

        ---

        **📋 어디서 입력값을 찾나요?**
        - PT 운영기관(KASTO 등)에서 보내주는 **PT 결과 보고서**에 모든 값이 있습니다
        - **우리 기관 측정값, 배정값**: 보고서 표지 또는 결과 요약표
        - **σ_pt**: "숙련도 평가용 표준편차"라는 이름으로 기재
        - **U_lab**: 우리 기관이 제출한 확장불확도
        - **U_ref**: 기준값의 확장불확도 (없으면 0으로 두세요)
        """
    )

    if st.button("📝 예시 데이터로 체험하기", key="pt_example"):
        st.session_state["pt_example_loaded"] = True

st.divider()

# 예시 데이터 로드 여부
_use_example = st.session_state.get("pt_example_loaded", False)

input_mode = st.radio("입력 방식", ["단건 입력", "CSV 업로드"], horizontal=True)

if input_mode == "단건 입력":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**필수 입력**")
        lab_value = st.number_input(
            "참가기관 측정값 (x)",
            value=50.012 if _use_example else 50.001,
            format="%.6g",
            help="PT 결과서에서 우리 기관이 보고한 측정값",
        )
        assigned_value = st.number_input(
            "배정값 (X)",
            value=50.000,
            format="%.6g",
            help="PT 운영기관이 결정한 기준값 (결과서에 'assigned value'로 표기)",
        )

    with col2:
        st.markdown("**선택 입력** _(PT 결과서에 있으면 입력)_")
        sigma_pt = st.number_input(
            "σ_pt (z-score용)",
            value=0.015 if _use_example else 0.0,
            format="%.6g",
            help="숙련도 평가용 표준편차. 결과서에 없으면 0으로 두세요.",
        )
        U_lab = st.number_input(
            "참가기관 확장불확도 U_lab",
            value=0.020 if _use_example else 0.0,
            format="%.6g",
            help="우리 기관이 보고한 확장불확도. 0이면 En/ζ 미계산.",
        )
        U_ref = st.number_input(
            "기준값 확장불확도 U_ref",
            value=0.005 if _use_example else 0.0,
            format="%.6g",
            help="기준값의 확장불확도 (없으면 0)",
        )
        k_val = st.number_input("포함인자 k", value=2.0)

    if st.button("📊 분석 실행", type="primary", use_container_width=True):
        result = analyze_pt(
            lab_value=lab_value,
            assigned_value=assigned_value,
            sigma_pt=sigma_pt if sigma_pt > 0 else None,
            U_lab=U_lab if U_lab > 0 else None,
            U_ref=U_ref if U_ref > 0 else None,
            k=k_val,
        )

        st.divider()
        st.subheader("분석 결과")

        cols = st.columns(3)

        def _indicator(judgment: str) -> str:
            if judgment == "만족":
                return "🟢"
            elif judgment == "주의":
                return "🟡"
            elif judgment == "불만족":
                return "🔴"
            return "⚪"

        with cols[0]:
            if result.z_score is not None:
                st.metric("z-score", f"{result.z_score:.3f}")
                st.markdown(f"{_indicator(result.z_judgment)} **{result.z_judgment}**")
            else:
                st.info("z-score: σ_pt 미입력")

        with cols[1]:
            if result.en_number is not None:
                st.metric("En number", f"{result.en_number:.3f}")
                st.markdown(f"{_indicator(result.en_judgment)} **{result.en_judgment}**")
            else:
                st.info("En number: U_lab/U_ref 미입력")

        with cols[2]:
            if result.zeta_score is not None:
                st.metric("ζ-score", f"{result.zeta_score:.3f}")
                st.markdown(f"{_indicator(result.zeta_judgment)} **{result.zeta_judgment}**")
            else:
                st.info("ζ-score: U_lab/U_ref 미입력")

        # ── 시각적 해석 섹션 ──
        st.divider()
        st.subheader("📝 결과 해석")

        if result.z_score is not None:
            abs_z = abs(result.z_score)
            if abs_z < 2:
                st.success(
                    f"✅ **z-score = {result.z_score:.3f}** → **만족**\n\n"
                    "우리 기관의 측정값이 다른 기관들과 잘 일치합니다. 시정조치 불필요."
                )
            elif abs_z < 3:
                st.warning(
                    f"⚠️ **z-score = {result.z_score:.3f}** → **주의**\n\n"
                    "경계선에 있습니다. 측정 프로세스를 점검하고 원인을 파악하세요. "
                    "다음 PT에서 개선 여부를 확인해야 합니다."
                )
            else:
                st.error(
                    f"🔴 **z-score = {result.z_score:.3f}** → **불만족**\n\n"
                    "우리 기관 측정값이 기준에서 크게 벗어났습니다.\n\n"
                    "**시정조치 필요:** 장비 재교정, 측정 절차 검토, 환경 조건 확인 등을 수행하고 "
                    "시정조치 보고서를 작성해야 합니다."
                )

        if result.en_number is not None:
            abs_en = abs(result.en_number)
            if abs_en < 1:
                st.success(
                    f"✅ **En = {result.en_number:.3f}** → **적합**\n\n"
                    "불확도를 고려했을 때 측정값이 적합합니다. 보고한 불확도도 적절합니다."
                )
            else:
                st.error(
                    f"🔴 **En = {result.en_number:.3f}** → **부적합**\n\n"
                    "불확도를 고려해도 측정값이 기준에서 벗어났습니다.\n\n"
                    "**가능한 원인:** 불확도를 과소 추정했거나, 실제 측정에 오류가 있을 수 있습니다."
                )

        # z-score 차트
        if result.z_score is not None:
            import plotly.graph_objects as go

            fig = go.Figure()
            # 배경 영역 (만족/주의/불만족)
            fig.add_vrect(x0=-2, x1=2, fillcolor="green", opacity=0.1, annotation_text="만족", annotation_position="top")
            fig.add_vrect(x0=-3, x1=-2, fillcolor="orange", opacity=0.1, annotation_text="주의")
            fig.add_vrect(x0=2, x1=3, fillcolor="orange", opacity=0.1)
            fig.add_trace(go.Bar(
                y=["z-score"],
                x=[result.z_score],
                orientation="h",
                marker_color="steelblue" if abs(result.z_score) <= 2.0 else ("orange" if abs(result.z_score) < 3.0 else "red"),
                width=0.5,
            ))
            fig.add_vline(x=-3, line_dash="dash", line_color="red", annotation_text="-3")
            fig.add_vline(x=-2, line_dash="dash", line_color="orange", annotation_text="-2")
            fig.add_vline(x=2, line_dash="dash", line_color="orange", annotation_text="+2")
            fig.add_vline(x=3, line_dash="dash", line_color="red", annotation_text="+3")
            fig.update_layout(title="z-score 판정 게이지", height=220, xaxis_title="z-score",
                             xaxis_range=[min(-4, result.z_score - 1), max(4, result.z_score + 1)])
            st.plotly_chart(fig, use_container_width=True)

else:
    st.markdown(
        "**CSV 파일 형식:** `cal_point, lab_value, assigned_value, sigma_pt, U_lab, U_ref`"
    )
    st.markdown("sigma_pt, U_lab, U_ref는 선택사항 (비어있으면 해당 지표 미계산)")

    uploaded = st.file_uploader("CSV 파일 업로드", type=["csv"])

    if uploaded is not None:
        import pandas as pd

        df = pd.read_csv(uploaded)
        st.dataframe(df, use_container_width=True)

        if st.button("📊 일괄 분석 실행", type="primary", use_container_width=True):
            data = []
            for _, row in df.iterrows():
                item = {
                    "cal_point": str(row.get("cal_point", "")),
                    "lab_value": float(row["lab_value"]),
                    "assigned_value": float(row["assigned_value"]),
                }
                if "sigma_pt" in row and pd.notna(row["sigma_pt"]):
                    item["sigma_pt"] = float(row["sigma_pt"])
                if "U_lab" in row and pd.notna(row["U_lab"]):
                    item["U_lab"] = float(row["U_lab"])
                if "U_ref" in row and pd.notna(row["U_ref"]):
                    item["U_ref"] = float(row["U_ref"])
                data.append(item)

            results = analyze_pt_batch(data)

            st.divider()
            st.subheader("분석 결과")

            result_data = []
            for r in results:
                row_data = {
                    "교정점": r.cal_point,
                    "측정값": f"{r.lab_value:.6g}",
                    "배정값": f"{r.assigned_value:.6g}",
                }
                if r.z_score is not None:
                    row_data["z-score"] = f"{r.z_score:.3f}"
                    row_data["z 판정"] = r.z_judgment
                if r.en_number is not None:
                    row_data["En"] = f"{r.en_number:.3f}"
                    row_data["En 판정"] = r.en_judgment
                if r.zeta_score is not None:
                    row_data["ζ"] = f"{r.zeta_score:.3f}"
                    row_data["ζ 판정"] = r.zeta_judgment
                result_data.append(row_data)

            st.dataframe(result_data, use_container_width=True)

            # z-score 차트
            z_scores = [r.z_score for r in results if r.z_score is not None]
            labels = [r.cal_point or f"#{i+1}" for i, r in enumerate(results) if r.z_score is not None]
            if z_scores:
                import plotly.graph_objects as go

                colors = []
                for z in z_scores:
                    if abs(z) <= 2.0:
                        colors.append("steelblue")
                    elif abs(z) < 3.0:
                        colors.append("orange")
                    else:
                        colors.append("red")

                fig = go.Figure()
                fig.add_trace(go.Bar(y=labels, x=z_scores, orientation="h", marker_color=colors))
                fig.add_vline(x=-3, line_dash="dash", line_color="red")
                fig.add_vline(x=-2, line_dash="dash", line_color="orange")
                fig.add_vline(x=2, line_dash="dash", line_color="orange")
                fig.add_vline(x=3, line_dash="dash", line_color="red")
                fig.update_layout(title="z-score 판정 차트", height=max(200, len(z_scores) * 40), xaxis_title="z-score")
                st.plotly_chart(fig, use_container_width=True)
