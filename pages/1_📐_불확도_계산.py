"""불확도 계산 페이지 — 템플릿, 직접입력, 위자드 모드."""

from __future__ import annotations

import math
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import streamlit as st

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.core.distributions import DistributionType, UncertaintySource
from metroai.core.gum import GUMCalculator, GUMResult
from metroai.core.mcm import MCMCalculator
from metroai.core.model import MeasurementModel
from metroai.export.kolas_excel import export_budget_excel
from metroai.export.kolas_pdf import export_calibration_certificate_pdf
from metroai.templates.length import create_gauge_block_template
from metroai.templates.mass import create_mass_template
from metroai.templates.temperature import create_temperature_template
from metroai.templates.pressure import create_pressure_template

st.set_page_config(
    page_title="MetroAI — 불확도 계산",
    page_icon="📐",
    layout="wide",
)


# ──────────────────────────────────────────
# 공통: 결과 표시 함수
# ──────────────────────────────────────────
def show_results(result: GUMResult, model, sources, config: dict):
    """GUM 결과를 화면에 표시."""
    st.divider()
    st.subheader("📊 계산 결과")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("합성불확도 uc", f"{result.combined_uncertainty:.4e} {config.get('measurand_unit', '')}")
    with m2:
        dof_str = "∞" if math.isinf(result.effective_dof) else f"{result.effective_dof:.0f}"
        st.metric("유효자유도 νeff", dof_str)
    with m3:
        st.metric("포함인자 k", f"{result.coverage_factor:.3f}")
    with m4:
        st.metric("확장불확도 U", f"{result.expanded_uncertainty:.4e} {config.get('measurand_unit', '')}")

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

    # MCM 검증
    st.subheader("🎲 몬테카를로 검증 (MCM)")
    mcm_samples = st.slider("시뮬레이션 횟수", 10_000, 500_000, 100_000, step=10_000, key="mcm_slider")

    if st.button("MCM 검증 실행", key="mcm_btn"):
        with st.spinner(f"몬테카를로 시뮬레이션 {mcm_samples:,}회 실행 중..."):
            mcm_calc = MCMCalculator(model, sources, n_samples=mcm_samples, seed=42)
            mcm_result = mcm_calc.simulate(gum_uc=result.combined_uncertainty)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("MCM 표준불확도", f"{mcm_result.std:.4e}")
        with c2:
            st.metric("95% 포함구간", f"[{mcm_result.coverage_low:.4e}, {mcm_result.coverage_high:.4e}]")
        with c3:
            agree_text = "✅ 일치" if mcm_result.gum_agreement else "⚠️ 불일치"
            st.metric("GUM vs MCM", agree_text)

        if mcm_result.samples is not None:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=mcm_result.samples, nbinsx=100, name="MCM 분포", marker_color="steelblue"))
            fig.add_vline(x=mcm_result.coverage_low, line_dash="dash", line_color="red", annotation_text="95% 하한")
            fig.add_vline(x=mcm_result.coverage_high, line_dash="dash", line_color="red", annotation_text="95% 상한")
            fig.update_layout(title="MCM 출력 분포", xaxis_title=f"측정값 ({config.get('measurand_unit', '')})", yaxis_title="빈도", height=400)
            st.plotly_chart(fig, use_container_width=True)

    # 내보내기
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

    with col_dl2:
        with st.expander("📄 교정성적서 PDF 다운로드"):
            cert_number = st.text_input("성적서 번호", value="CAL-2026-001", key="cert_num")
            cert_org = st.text_input("교정기관명", value="", key="cert_org")
            cert_kolas = st.text_input("KOLAS 인정번호", value="KOLAS-", key="cert_kolas")
            cert_client = st.text_input("의뢰기관명", value="", key="cert_client")
            cert_equip = st.text_input("교정 대상 기기", value="", key="cert_equip")

            cert_info = {
                "cert_number": cert_number,
                "cal_org": cert_org,
                "cal_org_kolas_id": cert_kolas,
                "cal_org_address": "",
                "client_org": cert_client,
                "client_address": "",
                "equipment_name": cert_equip,
                "manufacturer": "",
                "model": "",
                "serial_number": "",
                "cal_date": "2026-04-04",
                "cal_location": "",
                "temperature": "20.0 +/- 0.5",
                "humidity": "50 +/- 10",
                "calibrator_name": "",
                "reviewer_name": "",
                "approver_name": "",
            }

            pdf_buf = export_calibration_certificate_pdf(result, cert_info)
            st.download_button(
                "📄 PDF 다운로드",
                data=pdf_buf,
                file_name=f"교정성적서_{cert_number}.pdf",
                mime="application/pdf",
                use_container_width=True,
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
        ["🔧 템플릿 사용", "✏️ 직접 입력", "🧙 위자드 모드"],
        index=0,
    )

    if mode == "🔧 템플릿 사용":
        template = st.selectbox(
            "교정 분야",
            [
                "길이 — 블록게이지 비교 교정",
                "질량 — 분동 교정",
                "온도 — 온도계 교정",
                "압력 — 압력계 교정",
            ],
        )

    st.divider()
    st.markdown(
        "**MetroAI v0.1.0**\n\n"
        "GUM (ISO/IEC Guide 98-3) 준거\n\n"
        "KOLAS-G-002 양식 지원"
    )


# ──────────────────────────────────────────
# 메인 영역
# ──────────────────────────────────────────
st.header("측정불확도 예산표 작성")


# ──────────────────────────────────────────
# 템플릿 모드
# ──────────────────────────────────────────
if mode == "🔧 템플릿 사용":

    if template == "길이 — 블록게이지 비교 교정":
        st.subheader("📏 블록게이지 비교 교정")
        st.markdown("**측정 모델:** `L = dL + d_std + (α_s - α_x) × L_s × ΔT`")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**기본 파라미터**")
            nominal_length = st.number_input("공칭 길이 (mm)", value=50.0, step=1.0, format="%.1f")
            std_cert_u = st.number_input("표준기 교정 확장불확도 U (μm)", value=0.05, step=0.01, format="%.4f")
            std_cert_k = st.number_input("표준기 교정 포함인자 k", value=2.0, step=0.1, format="%.1f")
        with col2:
            st.markdown("**환경 조건**")
            temp_unc = st.number_input("온도 불확도 반폭 (°C)", value=0.5, step=0.1, format="%.1f")
            alpha_unc = st.number_input("열팽창계수 불확도 (/°C)", value=1.0e-6, step=1.0e-7, format="%.1e")
            temp_dev = st.number_input("온도 편차 ΔT (°C)", value=0.0, step=0.1, format="%.1f")

        st.markdown("**비교기 반복 측정값 (μm)**")
        readings_str = st.text_input("쉼표로 구분 입력", value="0.10, 0.12, 0.08, 0.11, 0.09", key="gb_readings")

        try:
            readings = [float(x.strip()) for x in readings_str.split(",") if x.strip()]
        except ValueError:
            st.error("숫자를 쉼표로 구분하여 입력하세요.")
            readings = None

        if readings and len(readings) >= 2:
            if st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True, key="gb_calc"):
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
                    calc = GUMCalculator(model, sources, measurand_name=config["measurand_name"], measurand_unit=config["measurand_unit"])
                    result = calc.calculate()
                show_results(result, model, sources, config)

    elif template == "질량 — 분동 교정":
        st.subheader("⚖️ 분동 교정")
        st.markdown("**측정 모델:** `m = dm_d + d_std + dm_b + dm_a`")

        col1, col2 = st.columns(2)
        with col1:
            nominal_mass = st.number_input("공칭 질량 (g)", value=100.0, step=10.0)
            std_cert_U = st.number_input("표준분동 교정 확장불확도 U (mg)", value=0.05, step=0.01, format="%.4f", key="mass_U")
            std_cert_k_m = st.number_input("표준분동 교정 포함인자 k", value=2.0, step=0.1, key="mass_k")
        with col2:
            resolution = st.number_input("저울 분해능 (mg)", value=0.001, step=0.001, format="%.4f", key="mass_res")
            buoyancy = st.number_input("부력 보정 불확도 (mg)", value=0.001, step=0.001, format="%.4f", key="mass_buoy")

        readings_str = st.text_input("반복 측정값 (mg, 쉼표 구분)", value="0.010, 0.012, 0.008, 0.011, 0.009", key="mass_readings")
        try:
            readings = [float(x.strip()) for x in readings_str.split(",") if x.strip()]
        except ValueError:
            readings = None

        if readings and len(readings) >= 2:
            if st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True, key="mass_calc"):
                with st.spinner("계산 중..."):
                    model, sources, config = create_mass_template(
                        nominal_mass_g=nominal_mass,
                        std_cert_U=std_cert_U,
                        std_cert_k=std_cert_k_m,
                        readings_mg=readings,
                        resolution_mg=resolution,
                        buoyancy_unc_mg=buoyancy,
                    )
                    calc = GUMCalculator(model, sources, measurand_name=config["measurand_name"], measurand_unit=config["measurand_unit"])
                    result = calc.calculate()
                show_results(result, model, sources, config)

    elif template == "온도 — 온도계 교정":
        st.subheader("🌡️ 온도계 교정")
        st.markdown("**측정 모델:** `T = dT_ind + d_std + dT_stab + dT_uni + dT_res`")

        col1, col2 = st.columns(2)
        with col1:
            cal_point = st.number_input("교정점 (°C)", value=100.0, step=10.0, key="temp_point")
            std_cert_U_t = st.number_input("표준 온도계 교정 U (°C)", value=0.02, step=0.01, format="%.4f", key="temp_U")
            std_cert_k_t = st.number_input("표준 온도계 교정 k", value=2.0, step=0.1, key="temp_k")
        with col2:
            stability = st.number_input("항온조 안정도 (°C)", value=0.02, step=0.01, format="%.3f", key="temp_stab")
            uniformity = st.number_input("항온조 균일도 (°C)", value=0.05, step=0.01, format="%.3f", key="temp_uni")
            resolution_t = st.number_input("시험편 분해능 (°C)", value=0.01, step=0.01, format="%.3f", key="temp_res")

        readings_str = st.text_input("반복 측정값 (°C, 쉼표 구분)", value="0.01, 0.02, -0.01, 0.00, 0.01", key="temp_readings")
        try:
            readings = [float(x.strip()) for x in readings_str.split(",") if x.strip()]
        except ValueError:
            readings = None

        if readings and len(readings) >= 2:
            if st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True, key="temp_calc"):
                with st.spinner("계산 중..."):
                    model, sources, config = create_temperature_template(
                        cal_point_C=cal_point,
                        std_cert_U_C=std_cert_U_t,
                        std_cert_k=std_cert_k_t,
                        readings_C=readings,
                        stability_C=stability,
                        uniformity_C=uniformity,
                        resolution_C=resolution_t,
                    )
                    calc = GUMCalculator(model, sources, measurand_name=config["measurand_name"], measurand_unit=config["measurand_unit"])
                    result = calc.calculate()
                show_results(result, model, sources, config)

    elif template == "압력 — 압력계 교정":
        st.subheader("🔧 압력계 교정")
        st.markdown("**측정 모델:** `P = dP_ind + d_std + dP_res + dP_hyst + dP_zero`")

        col1, col2 = st.columns(2)
        with col1:
            cal_point_p = st.number_input("교정점 (MPa)", value=10.0, step=1.0, key="pres_point")
            std_cert_U_p = st.number_input("표준기 교정 U (MPa)", value=0.002, step=0.001, format="%.4f", key="pres_U")
            std_cert_k_p = st.number_input("표준기 교정 k", value=2.0, step=0.1, key="pres_k")
        with col2:
            resolution_p = st.number_input("시험편 분해능 (MPa)", value=0.001, step=0.001, format="%.4f", key="pres_res")
            hysteresis = st.number_input("이력차 (MPa)", value=0.002, step=0.001, format="%.4f", key="pres_hyst")
            zero_drift = st.number_input("영점 드리프트 (MPa)", value=0.001, step=0.001, format="%.4f", key="pres_zero")

        readings_str = st.text_input("반복 측정값 (MPa, 쉼표 구분)", value="0.001, 0.002, -0.001, 0.000, 0.001", key="pres_readings")
        try:
            readings = [float(x.strip()) for x in readings_str.split(",") if x.strip()]
        except ValueError:
            readings = None

        if readings and len(readings) >= 2:
            if st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True, key="pres_calc"):
                with st.spinner("계산 중..."):
                    model, sources, config = create_pressure_template(
                        cal_point_MPa=cal_point_p,
                        std_cert_U_MPa=std_cert_U_p,
                        std_cert_k=std_cert_k_p,
                        readings_MPa=readings,
                        resolution_MPa=resolution_p,
                        hysteresis_MPa=hysteresis,
                        zero_drift_MPa=zero_drift,
                    )
                    calc = GUMCalculator(model, sources, measurand_name=config["measurand_name"], measurand_unit=config["measurand_unit"])
                    result = calc.calculate()
                show_results(result, model, sources, config)


# ──────────────────────────────────────────
# 직접 입력 모드
# ──────────────────────────────────────────
elif mode == "✏️ 직접 입력":
    st.subheader("✏️ 사용자 정의 측정 모델")

    model_expr = st.text_input("측정 모델 수학식", value="a + b + c", help="Python/sympy 문법. 예: a + b, a * b, a**2 + b/c")
    symbols_str = st.text_input("입력량 기호 (쉼표 구분)", value="a, b, c")
    symbol_names = [s.strip() for s in symbols_str.split(",") if s.strip()]

    st.divider()
    st.markdown("**불확도 성분 입력**")

    sources_input = []
    for i, sym in enumerate(symbol_names):
        with st.expander(f"📌 입력량: {sym}", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("성분 이름", value=f"성분 {sym}", key=f"name_{sym}")
                value = st.number_input("추정값", value=0.0, key=f"val_{sym}", format="%.6g")
            with c2:
                eval_type = st.selectbox("평가 유형", ["B", "A"], key=f"type_{sym}")
                if eval_type == "B":
                    dist = st.selectbox(
                        "분포",
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
                        u_val = st.number_input("표준불확도 u", value=0.01, key=f"u_{sym}", format="%.4e")
                        sources_input.append(UncertaintySource(
                            name=name, symbol=sym, eval_type="B",
                            value=value, std_uncertainty=u_val, distribution=distribution,
                        ))
                    elif input_method == "반폭 a":
                        a_val = st.number_input("반폭 a (±)", value=0.01, key=f"a_{sym}", format="%.4e")
                        sources_input.append(UncertaintySource(
                            name=name, symbol=sym, eval_type="B",
                            value=value, distribution=distribution, half_width=a_val,
                        ))
                    else:
                        U_val = st.number_input("확장불확도 U", value=0.02, key=f"U_{sym}", format="%.4e")
                        k_val = st.number_input("포함인자 k", value=2.0, key=f"k_{sym}")
                        sources_input.append(UncertaintySource(
                            name=name, symbol=sym, eval_type="B",
                            value=value, distribution=distribution,
                            expanded_uncertainty_input=U_val, coverage_factor_input=k_val,
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

    if sources_input and st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True, key="manual_calc"):
        try:
            model = MeasurementModel(model_expr, symbol_names)
            calc = GUMCalculator(model, sources_input, measurand_name="Y")
            result = calc.calculate()
            config = {"measurand_name": "Y", "measurand_unit": ""}
            show_results(result, model, sources_input, config)
        except Exception as e:
            st.error(f"계산 오류: {e}")


# ──────────────────────────────────────────
# 위자드 모드
# ──────────────────────────────────────────
elif mode == "🧙 위자드 모드":
    st.subheader("🧙 위자드 모드 — 단계별 불확도 입력")
    st.markdown("GUM을 몰라도 괜찮아요! 질문에 답하면 불확도 예산표가 자동으로 만들어집니다.")

    # 세션 상태 초기화
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "wizard_sources" not in st.session_state:
        st.session_state.wizard_sources = []
    if "wizard_model_expr" not in st.session_state:
        st.session_state.wizard_model_expr = ""
    if "wizard_symbol_names" not in st.session_state:
        st.session_state.wizard_symbol_names = []
    if "wizard_measurand" not in st.session_state:
        st.session_state.wizard_measurand = {"name": "Y", "unit": ""}

    # ─── Step 1: 측정 대상 선택 ───
    st.markdown("### Step 1: 측정 대상 선택")
    target = st.selectbox(
        "무엇을 교정/시험하나요?",
        ["길이 (블록게이지)", "질량 (분동)", "온도 (온도계)", "압력 (압력계)", "직접 입력"],
        key="wizard_target",
    )

    if target == "직접 입력":
        st.session_state.wizard_model_expr = st.text_input(
            "측정 모델 수식", value="a + b", key="wizard_custom_expr",
        )
        st.session_state.wizard_measurand = {
            "name": st.text_input("측정량 기호", value="Y", key="wizard_meas_name"),
            "unit": st.text_input("단위", value="", key="wizard_meas_unit"),
        }
    else:
        target_configs = {
            "길이 (블록게이지)": ("dL + d_std + alpha_diff * Ls_mm * 1000 * dT", "L", "μm"),
            "질량 (분동)": ("dm_d + d_std + dm_b + dm_a", "m", "mg"),
            "온도 (온도계)": ("dT_ind + d_std + dT_stab + dT_uni + dT_res", "T", "°C"),
            "압력 (압력계)": ("dP_ind + d_std + dP_res + dP_hyst + dP_zero", "P", "MPa"),
        }
        expr, meas_name, meas_unit = target_configs[target]
        st.session_state.wizard_model_expr = expr
        st.session_state.wizard_measurand = {"name": meas_name, "unit": meas_unit}
        st.info(f"측정 모델: `{expr}`")

    st.divider()

    # ─── Step 2: 불확도 성분 수집 ───
    st.markdown("### Step 2: 불확도 성분 추가")

    with st.form("wizard_add_source", clear_on_submit=True):
        st.markdown("**새 불확도 성분 추가**")

        src_name = st.text_input("성분 이름 (예: 비교기 반복 측정)", key="wiz_src_name")
        src_symbol = st.text_input("수식에서 사용할 기호 (예: dL)", key="wiz_src_sym")

        how_known = st.selectbox(
            "이 값의 불확도를 어떻게 알았나요?",
            [
                "같은 측정을 여러번 반복했어요 (A형)",
                "교정성적서에 적혀 있어요 (B형-정규분포)",
                "사양서/규격서에 ±값이 있어요 (B형-균일분포)",
                "경험적으로 범위를 알아요 (B형-삼각분포)",
            ],
            key="wiz_how_known",
        )

        if "반복" in how_known:
            data_str = st.text_input(
                "측정값을 쉼표로 입력해주세요",
                value="", key="wiz_data",
                help="예: 0.10, 0.12, 0.08, 0.11, 0.09",
            )
        elif "교정성적서" in how_known:
            wiz_U = st.number_input("교정성적서의 확장불확도(U) 값은?", value=0.05, format="%.4e", key="wiz_U")
            wiz_k = st.number_input("포함인자(k) 값은? (보통 2입니다)", value=2.0, key="wiz_k")
        elif "사양서" in how_known:
            wiz_a = st.number_input("±값(반폭)은 얼마인가요?", value=0.01, format="%.4e", key="wiz_a")
        else:
            wiz_a_tri = st.number_input("범위(반폭)는 얼마인가요?", value=0.01, format="%.4e", key="wiz_a_tri")

        submitted = st.form_submit_button("성분 추가", type="primary")

        if submitted and src_name and src_symbol:
            if "반복" in how_known:
                try:
                    data_vals = [float(x.strip()) for x in data_str.split(",") if x.strip()]
                except ValueError:
                    data_vals = []
                if len(data_vals) >= 2:
                    src = UncertaintySource(
                        name=src_name, symbol=src_symbol, eval_type="A",
                        repeat_data=data_vals,
                    )
                    st.session_state.wizard_sources.append(src)
                    st.session_state.wizard_symbol_names.append(src_symbol)
                    st.success(f"✅ '{src_name}' 추가 완료 (A형 평가, 평균의 표준불확도 자동 계산)")
                else:
                    st.error("최소 2개 이상의 데이터가 필요합니다.")
            elif "교정성적서" in how_known:
                src = UncertaintySource(
                    name=src_name, symbol=src_symbol, eval_type="B",
                    value=0.0, distribution=DistributionType.NORMAL,
                    expanded_uncertainty_input=wiz_U, coverage_factor_input=wiz_k,
                )
                st.session_state.wizard_sources.append(src)
                st.session_state.wizard_symbol_names.append(src_symbol)
                st.success(f"✅ '{src_name}' 추가 완료 (B형 평가, 정규분포, u = {wiz_U}/{wiz_k} = {wiz_U/wiz_k:.4e})")
            elif "사양서" in how_known:
                src = UncertaintySource(
                    name=src_name, symbol=src_symbol, eval_type="B",
                    value=0.0, distribution=DistributionType.RECTANGULAR,
                    half_width=wiz_a,
                )
                st.session_state.wizard_sources.append(src)
                st.session_state.wizard_symbol_names.append(src_symbol)
                st.success(f"✅ '{src_name}' 추가 완료 (B형 평가, 균일분포, u = {wiz_a}/√3 = {wiz_a / 1.732:.4e})")
            else:
                src = UncertaintySource(
                    name=src_name, symbol=src_symbol, eval_type="B",
                    value=0.0, distribution=DistributionType.TRIANGULAR,
                    half_width=wiz_a_tri,
                )
                st.session_state.wizard_sources.append(src)
                st.session_state.wizard_symbol_names.append(src_symbol)
                st.success(f"✅ '{src_name}' 추가 완료 (B형 평가, 삼각분포, u = {wiz_a_tri}/√6 = {wiz_a_tri / 2.449:.4e})")

    # 현재 추가된 성분 목록
    if st.session_state.wizard_sources:
        st.markdown("**추가된 성분 목록:**")
        for i, src in enumerate(st.session_state.wizard_sources):
            u_val, _ = src.compute()
            eval_desc = "A형" if src.eval_type == "A" else f"B형-{src.distribution.value}"
            st.markdown(f"  {i+1}. **{src.name}** ({src.symbol}) — {eval_desc}, u = {u_val:.4e}")

        if st.button("🗑️ 전체 초기화"):
            st.session_state.wizard_sources = []
            st.session_state.wizard_symbol_names = []
            st.rerun()

    st.divider()

    # ─── Step 3+4: 계산 ───
    st.markdown("### Step 3: 계산")

    if len(st.session_state.wizard_sources) < 2:
        st.warning("최소 2개 이상의 불확도 성분이 필요합니다.")
    else:
        # 모델 수식 구성 (직접입력이 아닌 경우 심볼 합산)
        if target == "직접 입력":
            expr = st.session_state.wizard_model_expr
            syms = st.session_state.wizard_symbol_names
        else:
            syms = st.session_state.wizard_symbol_names
            expr = " + ".join(syms)

        st.info(f"측정 모델: `{st.session_state.wizard_measurand['name']} = {expr}`")

        if st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True, key="wizard_calc"):
            try:
                model = MeasurementModel(expr, syms)
                calc = GUMCalculator(
                    model, st.session_state.wizard_sources,
                    measurand_name=st.session_state.wizard_measurand["name"],
                    measurand_unit=st.session_state.wizard_measurand["unit"],
                )
                result = calc.calculate()

                # 성분별 해설
                st.markdown("### 성분별 해설")
                for comp in result.components:
                    src = comp.source
                    if src.eval_type == "A":
                        desc = f"**{src.name}**: A형 평가 (반복 측정 통계), 정규분포를 사용했습니다."
                    else:
                        desc = f"**{src.name}**: B형 평가, {src.distribution.value}를 사용했습니다."
                    st.markdown(f"- {desc} (u = {comp.std_uncertainty:.4e})")

                config = {
                    "measurand_name": st.session_state.wizard_measurand["name"],
                    "measurand_unit": st.session_state.wizard_measurand["unit"],
                }
                show_results(result, model, st.session_state.wizard_sources, config)

            except Exception as e:
                st.error(f"계산 오류: {e}")
