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

from metroai.auth import (
    init_auth_state,
    render_auth_sidebar,
    show_usage_info,
    show_guest_notice,
    get_usage_manager,
)
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
# 인증 및 사용량 관리
# ──────────────────────────────────────────
def check_and_track_calculation(username=None):
    """계산 실행 전 사용량 확인 및 추적.

    Args:
        username: 로그인한 사용자명. None이면 게스트 모드.

    Returns:
        (can_proceed, message) 튜플
        - can_proceed: True면 계산 진행 가능
        - message: 안내 메시지 (제한시 표시)
    """
    if username is None:
        # 게스트: 1회 제한
        if "guest_calculation_done" not in st.session_state:
            st.session_state.guest_calculation_done = False

        if st.session_state.guest_calculation_done:
            return False, "게스트는 1번의 계산만 가능합니다. 로그인 후 더 많은 계산을 이용하세요!"

        return True, "게스트: 1회 계산 가능"

    # 로그인 사용자: 월 3회 제한
    usage_manager = get_usage_manager()
    if not usage_manager.check_limit(username, limit=3):
        return False, "이번 달 계산 한도(3회)를 초과했습니다. 내년 같은 기간에 이용할 수 있습니다."

    return True, None


def increment_calculation_usage(username=None):
    """계산 실행 후 사용량 증가.

    Args:
        username: 로그인한 사용자명. None이면 게스트 모드.
    """
    if username is None:
        # 게스트 계산 표시
        st.session_state.guest_calculation_done = True
    else:
        # 사용자 사용량 증가
        usage_manager = get_usage_manager()
        usage_manager.increment_usage(username)


# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
# 인증 초기화
init_auth_state()

# 사이드바 인증 위젯
username, name = render_auth_sidebar()

# 인증 상태 세션 저장
if username:
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.name = name
else:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.name = None

# 사용량 정보 표시 및 모드 선택
with st.sidebar:
    if st.session_state.authenticated and st.session_state.username:
        show_usage_info(st.session_state.username)
    else:
        show_guest_notice()

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
                can_proceed, msg = check_and_track_calculation(st.session_state.username)
                if not can_proceed:
                    st.error(msg)
                else:
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
                    increment_calculation_usage(st.session_state.username)
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
                can_proceed, msg = check_and_track_calculation(st.session_state.username)
                if not can_proceed:
                    st.error(msg)
                else:
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
                    increment_calculation_usage(st.session_state.username)
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
                can_proceed, msg = check_and_track_calculation(st.session_state.username)
                if not can_proceed:
                    st.error(msg)
                else:
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
                    increment_calculation_usage(st.session_state.username)
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
                can_proceed, msg = check_and_track_calculation(st.session_state.username)
                if not can_proceed:
                    st.error(msg)
                else:
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
                    increment_calculation_usage(st.session_state.username)
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
        can_proceed, msg = check_and_track_calculation(st.session_state.username)
        if not can_proceed:
            st.error(msg)
        else:
            try:
                model = MeasurementModel(model_expr, symbol_names)
                calc = GUMCalculator(model, sources_input, measurand_name="Y")
                result = calc.calculate()
                config = {"measurand_name": "Y", "measurand_unit": ""}
                increment_calculation_usage(st.session_state.username)
                show_results(result, model, sources_input, config)
            except Exception as e:
                st.error(f"계산 오류: {e}")


# ──────────────────────────────────────────
# 위자드 모드
# ──────────────────────────────────────────
elif mode == "🧙 위자드 모드":
    st.subheader("🧙 위자드 모드 — 스마트 위자드로 불확도 예산표 만들기")
    st.markdown("측정 분야를 선택하면 표준 불확도 성분들이 자동으로 제시됩니다. 필요한 항목을 선택하고 값을 입력하기만 하면 됩니다!")

    # 세션 상태 초기화
    if "wizard_target" not in st.session_state:
        st.session_state.wizard_target = "길이 (블록게이지)"
    if "wizard_sources" not in st.session_state:
        st.session_state.wizard_sources = []
    if "wizard_symbol_names" not in st.session_state:
        st.session_state.wizard_symbol_names = []
    if "wizard_enabled_components" not in st.session_state:
        st.session_state.wizard_enabled_components = {}

    # ─── Step 1: 측정 분야 선택 ───
    with st.expander("📏 Step 1: 측정 분야 선택", expanded=True):
        target = st.selectbox(
            "측정 분야 선택",
            ["길이 (블록게이지)", "질량 (분동)", "온도 (온도계)", "압력 (압력계)", "직접 입력"],
            key="wizard_target_select",
        )
        st.session_state.wizard_target = target

    # ─── 표준 템플릿 정의 ───
    # 각 템플릿은 (측정량_이름, 단위, [(컴포넌트_순서, 이름, 기호, 평가유형, 분포, 설명, 기본값)])
    templates = {
        "길이 (블록게이지)": {
            "measurand_name": "L",
            "measurand_unit": "μm",
            "measurement_model_expr": "dL + d_std + alpha_diff * Ls_mm * 1000 * dT",
            "components": [
                {
                    "order": 1,
                    "name": "비교기 반복 측정",
                    "symbol": "dL",
                    "eval_type": "A",
                    "description": "비교기로 여러 번 측정한 편차",
                    "input_type": "repeat_data",
                    "default_repeat": "0.10, 0.12, 0.08, 0.11, 0.09",
                },
                {
                    "order": 2,
                    "name": "표준기 교정 불확도",
                    "symbol": "d_std",
                    "eval_type": "B",
                    "distribution": DistributionType.NORMAL,
                    "description": "표준 블록게이지 교정성적서에서",
                    "input_type": "cert_uncertainty",
                    "default_U": 0.05,
                    "default_k": 2.0,
                },
                {
                    "order": 3,
                    "name": "열팽창계수 차이",
                    "symbol": "alpha_diff",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "표준기와 시험편의 열팽창계수 차이",
                    "input_type": "half_width",
                    "default_a": 1.0e-6,
                },
                {
                    "order": 4,
                    "name": "온도 불확도",
                    "symbol": "dT",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "환경 온도 불확도 반폭",
                    "input_type": "half_width",
                    "default_a": 0.5,
                },
                {
                    "order": 5,
                    "name": "비교기 분해능",
                    "symbol": "d_res",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "비교기의 측정 분해능",
                    "input_type": "resolution",
                    "default_res": 0.01,
                },
            ],
        },
        "질량 (분동)": {
            "measurand_name": "m",
            "measurand_unit": "mg",
            "measurement_model_expr": "dm_d + d_std + dm_b + dm_a",
            "components": [
                {
                    "order": 1,
                    "name": "저울 반복 측정",
                    "symbol": "dm_d",
                    "eval_type": "A",
                    "description": "저울로 여러 번 측정한 편차",
                    "input_type": "repeat_data",
                    "default_repeat": "0.010, 0.012, 0.008, 0.011, 0.009",
                },
                {
                    "order": 2,
                    "name": "표준분동 교정 불확도",
                    "symbol": "d_std",
                    "eval_type": "B",
                    "distribution": DistributionType.NORMAL,
                    "description": "표준분동 교정성적서에서",
                    "input_type": "cert_uncertainty",
                    "default_U": 0.05,
                    "default_k": 2.0,
                },
                {
                    "order": 3,
                    "name": "부력 보정",
                    "symbol": "dm_b",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "공기 부력으로 인한 불확도",
                    "input_type": "half_width",
                    "default_a": 0.001,
                },
                {
                    "order": 4,
                    "name": "저울 분해능",
                    "symbol": "dm_a",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "저울의 측정 분해능",
                    "input_type": "resolution",
                    "default_res": 0.001,
                },
            ],
        },
        "온도 (온도계)": {
            "measurand_name": "T",
            "measurand_unit": "°C",
            "measurement_model_expr": "dT_ind + d_std + dT_stab + dT_uni + dT_res",
            "components": [
                {
                    "order": 1,
                    "name": "반복 측정",
                    "symbol": "dT_ind",
                    "eval_type": "A",
                    "description": "온도계로 여러 번 측정한 편차",
                    "input_type": "repeat_data",
                    "default_repeat": "0.01, 0.02, -0.01, 0.00, 0.01",
                },
                {
                    "order": 2,
                    "name": "표준온도계 교정 불확도",
                    "symbol": "d_std",
                    "eval_type": "B",
                    "distribution": DistributionType.NORMAL,
                    "description": "표준온도계 교정성적서에서",
                    "input_type": "cert_uncertainty",
                    "default_U": 0.02,
                    "default_k": 2.0,
                },
                {
                    "order": 3,
                    "name": "항온조 안정도",
                    "symbol": "dT_stab",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "항온조의 온도 안정도",
                    "input_type": "half_width",
                    "default_a": 0.02,
                },
                {
                    "order": 4,
                    "name": "항온조 균일도",
                    "symbol": "dT_uni",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "항온조 내 온도 분포의 균일도",
                    "input_type": "half_width",
                    "default_a": 0.05,
                },
                {
                    "order": 5,
                    "name": "분해능",
                    "symbol": "dT_res",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "온도계의 측정 분해능",
                    "input_type": "resolution",
                    "default_res": 0.01,
                },
            ],
        },
        "압력 (압력계)": {
            "measurand_name": "P",
            "measurand_unit": "MPa",
            "measurement_model_expr": "dP_ind + d_std + dP_res + dP_hyst + dP_zero",
            "components": [
                {
                    "order": 1,
                    "name": "반복 측정",
                    "symbol": "dP_ind",
                    "eval_type": "A",
                    "description": "압력계로 여러 번 측정한 편차",
                    "input_type": "repeat_data",
                    "default_repeat": "0.001, 0.002, -0.001, 0.000, 0.001",
                },
                {
                    "order": 2,
                    "name": "표준기 교정 불확도",
                    "symbol": "d_std",
                    "eval_type": "B",
                    "distribution": DistributionType.NORMAL,
                    "description": "표준기 교정성적서에서",
                    "input_type": "cert_uncertainty",
                    "default_U": 0.002,
                    "default_k": 2.0,
                },
                {
                    "order": 3,
                    "name": "분해능",
                    "symbol": "dP_res",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "압력계의 측정 분해능",
                    "input_type": "resolution",
                    "default_res": 0.001,
                },
                {
                    "order": 4,
                    "name": "이력차",
                    "symbol": "dP_hyst",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "압력 상승/하강 시 히스테리시스",
                    "input_type": "half_width",
                    "default_a": 0.002,
                },
                {
                    "order": 5,
                    "name": "영점 드리프트",
                    "symbol": "dP_zero",
                    "eval_type": "B",
                    "distribution": DistributionType.RECTANGULAR,
                    "description": "장시간 운영 중 영점 변화",
                    "input_type": "half_width",
                    "default_a": 0.001,
                },
            ],
        },
    }

    # ─── Step 2: 불확도 성분 선택 및 입력 ───
    if target != "직접 입력":
        template = templates[target]
        st.session_state.wizard_measurand_name = template["measurand_name"]
        st.session_state.wizard_measurand_unit = template["measurand_unit"]

        st.divider()
        with st.expander("⚙️ Step 2: 불확도 성분 설정", expanded=True):
            st.markdown(f"**측정 모델:** `{template['measurand_name']} = {template['measurement_model_expr']}`")
            st.markdown("**아래 불확도 성분들 중 필요한 항목을 선택하고 값을 입력하세요:**")

            st.session_state.wizard_sources = []
            st.session_state.wizard_symbol_names = []

            for comp_spec in template["components"]:
                symbol = comp_spec["symbol"]
                name = comp_spec["name"]
                init_key = f"wizard_enabled_{symbol}"

                # 체크박스로 포함 여부 선택
                col_cb, col_desc = st.columns([0.15, 0.85])
                with col_cb:
                    enabled = st.checkbox(
                        "포함",
                        value=st.session_state.wizard_enabled_components.get(symbol, True),
                        key=init_key,
                        label_visibility="collapsed",
                    )
                    st.session_state.wizard_enabled_components[symbol] = enabled

                with col_desc:
                    st.markdown(f"**{name}** (`{symbol}`) — {comp_spec['description']}")

                if enabled:
                    # 평가 유형 및 입력 필드 표시
                    input_type = comp_spec.get("input_type", "half_width")

                    col_input = st.columns([0.05, 0.95])[1]  # 들여쓰기 효과

                    with col_input:
                        if input_type == "repeat_data":
                            # A형 평가: 반복 데이터
                            data_str = st.text_input(
                                f"{name} — 측정값 입력 (쉼표 구분)",
                                value=comp_spec.get("default_repeat", ""),
                                key=f"wiz_data_{symbol}",
                                help="예: 0.10, 0.12, 0.08, 0.11, 0.09",
                            )
                            try:
                                data_vals = [float(x.strip()) for x in data_str.split(",") if x.strip()]
                                if len(data_vals) >= 2:
                                    src = UncertaintySource(
                                        name=name, symbol=symbol, eval_type="A",
                                        repeat_data=data_vals,
                                    )
                                    st.session_state.wizard_sources.append(src)
                                    st.session_state.wizard_symbol_names.append(symbol)
                                    st.caption(f"✅ {len(data_vals)}개 데이터 인식됨")
                                else:
                                    st.warning("최소 2개 이상의 데이터가 필요합니다.")
                            except ValueError:
                                st.warning("숫자를 쉼표로 구분하여 입력하세요.")

                        elif input_type == "cert_uncertainty":
                            # B형 평가 (정규분포): 교정성적서 값
                            c1, c2 = st.columns(2)
                            with c1:
                                U_val = st.number_input(
                                    f"{name} — 확장불확도 U",
                                    value=comp_spec.get("default_U", 0.05),
                                    format="%.4e",
                                    key=f"wiz_cert_U_{symbol}",
                                )
                            with c2:
                                k_val = st.number_input(
                                    f"포함인자 k",
                                    value=comp_spec.get("default_k", 2.0),
                                    format="%.2f",
                                    key=f"wiz_cert_k_{symbol}",
                                )
                            src = UncertaintySource(
                                name=name, symbol=symbol, eval_type="B",
                                value=0.0, distribution=DistributionType.NORMAL,
                                expanded_uncertainty_input=U_val, coverage_factor_input=k_val,
                            )
                            st.session_state.wizard_sources.append(src)
                            st.session_state.wizard_symbol_names.append(symbol)
                            u_calc = U_val / k_val
                            st.caption(f"✅ 표준불확도 u = {U_val}/{k_val} = {u_calc:.4e}")

                        elif input_type == "half_width":
                            # B형 평가 (균일분포): 반폭
                            a_val = st.number_input(
                                f"{name} — ±값 (반폭)",
                                value=comp_spec.get("default_a", 0.01),
                                format="%.4e",
                                key=f"wiz_hw_{symbol}",
                            )
                            src = UncertaintySource(
                                name=name, symbol=symbol, eval_type="B",
                                value=0.0, distribution=DistributionType.RECTANGULAR,
                                half_width=a_val,
                            )
                            st.session_state.wizard_sources.append(src)
                            st.session_state.wizard_symbol_names.append(symbol)
                            u_calc = a_val / 1.732
                            st.caption(f"✅ 표준불확도 u = {a_val}/√3 = {u_calc:.4e}")

                        elif input_type == "resolution":
                            # B형 평가 (균일분포): 분해능
                            res_val = st.number_input(
                                f"{name} — 분해능",
                                value=comp_spec.get("default_res", 0.01),
                                format="%.4e",
                                key=f"wiz_res_{symbol}",
                            )
                            src = UncertaintySource(
                                name=name, symbol=symbol, eval_type="B",
                                value=0.0, distribution=DistributionType.RECTANGULAR,
                                half_width=res_val / 2,
                            )
                            st.session_state.wizard_sources.append(src)
                            st.session_state.wizard_symbol_names.append(symbol)
                            u_calc = (res_val / 2) / 1.732
                            st.caption(f"✅ 표준불확도 u = ({res_val}/2)/√3 = {u_calc:.4e}")

    else:
        # 직접 입력 모드
        st.divider()
        with st.expander("⚙️ Step 2: 사용자 정의 모델 입력", expanded=True):
            model_expr = st.text_input(
                "측정 모델 수식",
                value="a + b",
                key="wizard_custom_expr",
                help="Python/sympy 문법. 예: a + b, a * b, a**2 + b/c",
            )
            meas_name = st.text_input("측정량 기호", value="Y", key="wizard_meas_name")
            meas_unit = st.text_input("단위", value="", key="wizard_meas_unit")

            st.session_state.wizard_measurand_name = meas_name
            st.session_state.wizard_measurand_unit = meas_unit
            st.session_state.wizard_model_expr = model_expr

            # 직접 입력 모드에서는 기존의 형식 유지
            with st.form("wizard_add_source_custom", clear_on_submit=True):
                st.markdown("**새 불확도 성분 추가**")

                src_name = st.text_input("성분 이름 (예: 비교기 반복 측정)", key="wiz_src_name_custom")
                src_symbol = st.text_input("수식에서 사용할 기호 (예: dL)", key="wiz_src_sym_custom")

                how_known = st.selectbox(
                    "이 값의 불확도를 어떻게 알았나요?",
                    [
                        "같은 측정을 여러번 반복했어요 (A형)",
                        "교정성적서에 적혀 있어요 (B형-정규분포)",
                        "사양서/규격서에 ±값이 있어요 (B형-균일분포)",
                        "경험적으로 범위를 알아요 (B형-삼각분포)",
                    ],
                    key="wiz_how_known_custom",
                )

                if "반복" in how_known:
                    data_str = st.text_input(
                        "측정값을 쉼표로 입력해주세요",
                        value="", key="wiz_data_custom",
                        help="예: 0.10, 0.12, 0.08, 0.11, 0.09",
                    )
                elif "교정성적서" in how_known:
                    wiz_U = st.number_input("교정성적서의 확장불확도(U) 값은?", value=0.05, format="%.4e", key="wiz_U_custom")
                    wiz_k = st.number_input("포함인자(k) 값은? (보통 2입니다)", value=2.0, key="wiz_k_custom")
                elif "사양서" in how_known:
                    wiz_a = st.number_input("±값(반폭)은 얼마인가요?", value=0.01, format="%.4e", key="wiz_a_custom")
                else:
                    wiz_a_tri = st.number_input("범위(반폭)는 얼마인가요?", value=0.01, format="%.4e", key="wiz_a_tri_custom")

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

    # ─── Step 3: 계산 ───
    with st.expander("🚀 Step 3: 불확도 계산", expanded=True):
        if len(st.session_state.wizard_sources) < 2:
            st.warning("⚠️ 최소 2개 이상의 불확도 성분이 필요합니다. 위 Step 2에서 성분을 선택하고 값을 입력해주세요.")
        else:
            # 모델 수식 구성
            if target == "직접 입력":
                expr = st.session_state.wizard_model_expr
                syms = st.session_state.wizard_symbol_names
            else:
                syms = st.session_state.wizard_symbol_names
                expr = " + ".join(syms)

            st.info(f"**최종 측정 모델:** `{st.session_state.wizard_measurand_name} = {expr}`")
            st.info(f"**선택된 불확도 성분:** {', '.join([s.name for s in st.session_state.wizard_sources])}")

            if st.button("🚀 불확도 계산 실행", type="primary", use_container_width=True, key="wizard_calc"):
                can_proceed, msg = check_and_track_calculation(st.session_state.username)
                if not can_proceed:
                    st.error(msg)
                else:
                    try:
                        model = MeasurementModel(expr, syms)
                        calc = GUMCalculator(
                            model, st.session_state.wizard_sources,
                            measurand_name=st.session_state.wizard_measurand_name,
                            measurand_unit=st.session_state.wizard_measurand_unit,
                        )
                        result = calc.calculate()

                        # 성분별 해설
                        st.markdown("### 📚 성분별 해설")
                        for comp in result.components:
                            src = comp.source
                            if src.eval_type == "A":
                                desc = f"**{src.name}**: A형 평가 (반복 측정 통계), 정규분포를 사용했습니다."
                            else:
                                desc = f"**{src.name}**: B형 평가, {src.distribution.value}를 사용했습니다."
                            st.markdown(f"- {desc} (u = {comp.std_uncertainty:.4e})")

                        config = {
                            "measurand_name": st.session_state.wizard_measurand_name,
                            "measurand_unit": st.session_state.wizard_measurand_unit,
                        }
                        increment_calculation_usage(st.session_state.username)
                        show_results(result, model, st.session_state.wizard_sources, config)

                    except Exception as e:
                        st.error(f"계산 오류: {e}")
