"""MetroAI — KOLAS 측정불확도 예산 자동화 도구.

Streamlit MVP 메인 앱.
실행: streamlit run metroai/ui/app.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import streamlit as st

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.core.distributions import DistributionType, UncertaintySource
from metroai.core.gum import GUMCalculator
from metroai.core.mcm import MCMCalculator
from metroai.core.model import MeasurementModel
from metroai.export.kolas_excel import export_budget_excel
from metroai.templates.length import create_gauge_block_template

# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="MetroAI — KOLAS 불확도 예산 자동화",
    page_icon="📐",
    layout="wide",
)

# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.title("📐 MetroAI")
    st.caption("KOLAS 불확도 예산서, 5분 만에.")
    st.divider()

    mode = st.radio(
        "모드 선택",
        ["🔧 템플릿 사용", "✏️ 직접 입력"],
        index=0,
    )

    if mode == "🔧 템플릿 사용":
        template = st.selectbox(
            "교정 분야",
            ["길이 — 블록게이지 비교 교정"],
        )

    st.divider()
    st.markdown(
        "**MetroAI v0.1.0**\n\n"
        "GUM (ISO/IEC Guide 98-3) 준거\n\n"
        "KOLAS-G-002 양식 지원\n\n"
        "[GitHub](https://github.com/kyb8801/metroai)"
    )


# ──────────────────────────────────────────
# 메인 영역
# ──────────────────────────────────────────
st.header("측정불확도 예산표 작성")

if mode == "🔧 템플릿 사용":
    # ─── 블록게이지 템플릿 ───
    st.subheader("📏 블록게이지 비교 교정")
    st.markdown(
        "**측정 모델:** `L = dL + d_std + (α_s - α_x) × L_s × ΔT`"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**기본 파라미터**")
        nominal_length = st.number_input(
            "공칭 길이 (mm)", value=50.0, step=1.0, format="%.1f"
        )
        std_cert_u = st.number_input(
            "표준기 교정 확장불확도 U (μm)", value=0.05, step=0.01, format="%.4f"
        )
        std_cert_k = st.number_input(
            "표준기 교정 포함인자 k", value=2.0, step=0.1, format="%.1f"
        )

    with col2:
        st.markdown("**환경 조건**")
        temp_unc = st.number_input(
            "온도 불확도 반폭 (°C)", value=0.5, step=0.1, format="%.1f"
        )
        alpha_unc = st.number_input(
            "열팽창계수 불확도 (/°C)", value=1.0e-6, step=1.0e-7, format="%.1e"
        )
        temp_dev = st.number_input(
            "온도 편차 ΔT (°C)", value=0.0, step=0.1, format="%.1f"
        )

    st.markdown("**비교기 반복 측정값 (μm)**")
    readings_str = st.text_input(
        "쉼표로 구분 입력",
        value="0.10, 0.12, 0.08, 0.11, 0.09",
        help="비교기에서 측정한 차이값 (시험편 - 표준기, μm 단위)",
    )

    try:
        readings = [float(x.strip()) for x in readings_str.split(",") if x.strip()]
    except ValueError:
        st.error("숫자를 쉼표로 구분하여 입력하세요.")
        readings = None

    if readings and len(readings) >= 2:
        # 계산 실행
        if st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True):
            with st.spinner("GUM 불확도 전파 계산 중..."):
                model, sources, config = create_gauge_block_template(
                    nominal_length_mm=nominal_length,
                    comparator_readings=readings,
                    std_cert_uncertainty_um=std_cert_u,
                    std_cert_k=std_cert_k,
                    alpha_uncertainty=alpha_unc,
                    temp_deviation_C=temp_dev,
                    temp_uncertainty_C=temp_unc,
                )

                calc = GUMCalculator(
                    model, sources,
                    measurand_name=config["measurand_name"],
                    measurand_unit=config["measurand_unit"],
                )
                result = calc.calculate()

            # ── 결과 표시 ──
            st.divider()
            st.subheader("📊 계산 결과")

            # 핵심 지표
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("합성불확도 uc", f"{result.combined_uncertainty:.4e} μm")
            with m2:
                dof_str = "∞" if math.isinf(result.effective_dof) else f"{result.effective_dof:.0f}"
                st.metric("유효자유도 νeff", dof_str)
            with m3:
                st.metric("포함인자 k", f"{result.coverage_factor:.3f}")
            with m4:
                st.metric("확장불확도 U", f"{result.expanded_uncertainty:.4e} μm")

            # 불확도 표현 문구
            st.info(f"**{result.uncertainty_statement()}**")

            # 불확도 예산표
            st.subheader("📋 불확도 예산표")
            budget_data = []
            for comp in result.components:
                dof_str = "∞" if math.isinf(comp.dof) else f"{comp.dof:.0f}"
                dist_name = comp.source.distribution.value if comp.source.eval_type == "B" else "-"
                budget_data.append({
                    "불확도 성분": comp.source.name,
                    "기호": comp.source.symbol,
                    "평가 유형": f"{comp.source.eval_type}형",
                    "자유도 ν": dof_str,
                    "분포": dist_name,
                    "u(xi)": f"{comp.std_uncertainty:.4e}",
                    "ci": f"{comp.sensitivity_coeff:.4e}",
                    "|ci|·u(xi)": f"{comp.contribution:.4e}",
                    "기여율 (%)": f"{comp.percent_contribution:.1f}",
                })

            st.dataframe(budget_data, use_container_width=True)

            # ── MCM 검증 ──
            st.subheader("🎲 몬테카를로 검증 (MCM)")

            mcm_samples = st.slider("시뮬레이션 횟수", 10_000, 500_000, 100_000, step=10_000)

            if st.button("MCM 검증 실행"):
                with st.spinner(f"몬테카를로 시뮬레이션 {mcm_samples:,}회 실행 중..."):
                    mcm_calc = MCMCalculator(
                        model, sources,
                        n_samples=mcm_samples, seed=42,
                    )
                    mcm_result = mcm_calc.simulate(gum_uc=result.combined_uncertainty)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("MCM 표준불확도", f"{mcm_result.std:.4e}")
                with c2:
                    st.metric(
                        "95% 포함구간",
                        f"[{mcm_result.coverage_low:.4e}, {mcm_result.coverage_high:.4e}]",
                    )
                with c3:
                    agree_text = "✅ 일치" if mcm_result.gum_agreement else "⚠️ 불일치"
                    st.metric("GUM vs MCM", agree_text)

                # 히스토그램
                if mcm_result.samples is not None:
                    import plotly.graph_objects as go

                    fig = go.Figure()
                    fig.add_trace(go.Histogram(
                        x=mcm_result.samples, nbinsx=100,
                        name="MCM 분포", marker_color="steelblue",
                    ))
                    fig.add_vline(
                        x=mcm_result.coverage_low, line_dash="dash",
                        line_color="red", annotation_text="95% 하한",
                    )
                    fig.add_vline(
                        x=mcm_result.coverage_high, line_dash="dash",
                        line_color="red", annotation_text="95% 상한",
                    )
                    fig.update_layout(
                        title="MCM 출력 분포",
                        xaxis_title=f"측정값 ({config['measurand_unit']})",
                        yaxis_title="빈도",
                        height=400,
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # ── 다운로드 ──
            st.divider()
            st.subheader("📥 내보내기")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                excel_buf = export_budget_excel(result)
                st.download_button(
                    "📊 엑셀 다운로드 (.xlsx)",
                    data=excel_buf,
                    file_name="불확도_예산표.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

else:
    # ─── 직접 입력 모드 ───
    st.subheader("✏️ 사용자 정의 측정 모델")

    model_expr = st.text_input(
        "측정 모델 수학식",
        value="a + b + c",
        help="Python/sympy 문법. 예: a + b, a * b, a**2 + b/c",
    )
    symbols_str = st.text_input(
        "입력량 기호 (쉼표 구분)",
        value="a, b, c",
    )
    symbol_names = [s.strip() for s in symbols_str.split(",") if s.strip()]

    st.divider()
    st.markdown("**불확도 성분 입력**")

    sources_input = []
    for i, sym in enumerate(symbol_names):
        with st.expander(f"📌 입력량: {sym}", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input(f"성분 이름", value=f"성분 {sym}", key=f"name_{sym}")
                value = st.number_input(f"추정값", value=0.0, key=f"val_{sym}", format="%.6g")
            with c2:
                eval_type = st.selectbox(f"평가 유형", ["B", "A"], key=f"type_{sym}")
                if eval_type == "B":
                    dist = st.selectbox(
                        f"분포",
                        ["정규분포", "균일분포(사각)", "삼각분포", "U자형분포"],
                        key=f"dist_{sym}",
                    )
                    dist_map = {
                        "정규분포": DistributionType.NORMAL,
                        "균일분포(사각)": DistributionType.RECTANGULAR,
                        "삼각분포": DistributionType.TRIANGULAR,
                        "U자형분포": DistributionType.USHAPE,
                    }
                    distribution = dist_map[dist]
                else:
                    distribution = DistributionType.NORMAL

            with c3:
                if eval_type == "B":
                    input_method = st.radio(
                        "입력 방법", ["표준불확도 직접", "반폭 a", "확장불확도 U+k"],
                        key=f"method_{sym}",
                    )
                    if input_method == "표준불확도 직접":
                        u_val = st.number_input(
                            "표준불확도 u", value=0.01, key=f"u_{sym}", format="%.4e"
                        )
                        sources_input.append(UncertaintySource(
                            name=name, symbol=sym, eval_type="B",
                            value=value, std_uncertainty=u_val,
                            distribution=distribution,
                        ))
                    elif input_method == "반폭 a":
                        a_val = st.number_input(
                            "반폭 a (±)", value=0.01, key=f"a_{sym}", format="%.4e"
                        )
                        sources_input.append(UncertaintySource(
                            name=name, symbol=sym, eval_type="B",
                            value=value, distribution=distribution,
                            half_width=a_val,
                        ))
                    else:
                        U_val = st.number_input(
                            "확장불확도 U", value=0.02, key=f"U_{sym}", format="%.4e"
                        )
                        k_val = st.number_input(
                            "포함인자 k", value=2.0, key=f"k_{sym}"
                        )
                        sources_input.append(UncertaintySource(
                            name=name, symbol=sym, eval_type="B",
                            value=value, distribution=distribution,
                            expanded_uncertainty_input=U_val,
                            coverage_factor_input=k_val,
                        ))
                else:
                    data_str = st.text_input(
                        "반복 측정 데이터 (쉼표 구분)",
                        value="1.00, 1.01, 0.99, 1.00, 1.02",
                        key=f"data_{sym}",
                    )
                    try:
                        data_vals = [float(x.strip()) for x in data_str.split(",") if x.strip()]
                    except ValueError:
                        data_vals = []
                    sources_input.append(UncertaintySource(
                        name=name, symbol=sym, eval_type="A",
                        repeat_data=data_vals if len(data_vals) >= 2 else None,
                    ))

    if sources_input and st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True):
        try:
            model = MeasurementModel(model_expr, symbol_names)
            calc = GUMCalculator(model, sources_input, measurand_name="Y")
            result = calc.calculate()

            st.divider()
            st.subheader("📊 계산 결과")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("측정값 Y", f"{result.measurand_value:.6g}")
            with m2:
                st.metric("합성불확도 uc", f"{result.combined_uncertainty:.4e}")
            with m3:
                dof_str = "∞" if math.isinf(result.effective_dof) else f"{result.effective_dof:.0f}"
                st.metric("유효자유도 νeff", dof_str)
            with m4:
                st.metric("확장불확도 U", f"{result.expanded_uncertainty:.4e}")

            st.info(f"**{result.uncertainty_statement()}**")

            # 예산표
            budget_data = []
            for comp in result.components:
                dof_str = "∞" if math.isinf(comp.dof) else f"{comp.dof:.0f}"
                dist_name = comp.source.distribution.value if comp.source.eval_type == "B" else "-"
                budget_data.append({
                    "불확도 성분": comp.source.name,
                    "기호": comp.source.symbol,
                    "평가 유형": f"{comp.source.eval_type}형",
                    "분포": dist_name,
                    "u(xi)": f"{comp.std_uncertainty:.4e}",
                    "ci": f"{comp.sensitivity_coeff:.4e}",
                    "|ci|·u(xi)": f"{comp.contribution:.4e}",
                    "기여율 (%)": f"{comp.percent_contribution:.1f}",
                })
            st.dataframe(budget_data, use_container_width=True)

            # 엑셀 다운로드
            excel_buf = export_budget_excel(result)
            st.download_button(
                "📊 엑셀 다운로드 (.xlsx)",
                data=excel_buf,
                file_name="불확도_예산표.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"계산 오류: {e}")
