"""불확도 역설계 페이지 — Reverse Uncertainty Engineering.

목표 확장불확도(CMC)를 달성하기 위해
각 불확도 성분의 허용 최대값을 자동 산출.

세계 최초 기능. GUM Workbench, GTC, LNE Uncertainty 등
기존 소프트웨어에 없는 MetroAI 독점 기능.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import streamlit as st

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.core.reverse_uncertainty import ReverseUncertaintyEngine, ReverseResult
from metroai.core.model import MeasurementModel
from metroai.core.distributions import DistributionType

st.set_page_config(
    page_title="MetroAI — 불확도 역설계",
    page_icon="🔄",
    layout="wide",
)

# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.title("🔄 불확도 역설계")
    st.caption("목표 CMC에서 허용 불확도를 역산합니다.")
    st.divider()

    analysis_mode = st.radio(
        "분석 모드",
        ["🎯 목표 CMC → 허용 불확도", "🔍 단일 성분 역산 (What-If)"],
        index=0,
    )

    st.divider()
    st.markdown(
        "**💡 활용 시나리오**\n\n"
        "• KOLAS 신규 인정 신청: 필요 장비 스펙 결정\n\n"
        "• 장비 교체 의사결정: 목표 달성 여부 확인\n\n"
        "• 불확도 예산 최적화: 병목 성분 파악"
    )

# ──────────────────────────────────────────
# 메인 영역
# ──────────────────────────────────────────
st.header("🔄 불확도 역설계 (Reverse Uncertainty Engineering)")

st.info(
    "**기존 소프트웨어:** 입력 → 불확도 계산 (순방향)\n\n"
    "**MetroAI 역설계:** 목표 불확도 → 각 성분 허용 범위 (역방향)\n\n"
    "\"CMC를 0.1 µm로 주장하려면, 각 성분이 얼마 이하여야 하는가?\""
)

st.divider()

# ──────────────────────────────────────────
# 결과 표시 함수 (호출 전에 정의)
# ──────────────────────────────────────────
def _show_reverse_results(result: ReverseResult):
    """역설계 결과를 화면에 표시."""

    st.divider()
    st.subheader("📊 역설계 결과")

    # 요약 메트릭
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            "목표 확장불확도 U",
            f"{result.target_expanded_uncertainty:.4g} {result.measurand_unit}",
        )
    with m2:
        st.metric(
            "허용 합성불확도 uc",
            f"{result.target_combined_uncertainty:.4g} {result.measurand_unit}",
        )
    with m3:
        status = "✅ 달성 가능" if result.overall_feasible else "❌ 목표 초과"
        st.metric("판정", status)

    if result.bottleneck_component:
        st.warning(f"⚠️ **병목 성분:** `{result.bottleneck_component}` — 이 성분이 가장 빡빡합니다.")

    st.markdown(f"**{result.summary()}**")

    # 상세 예산표
    st.subheader("📋 허용 불확도 예산표")

    budget_data = []
    for comp in result.components:
        row = {
            "성분": comp.symbol,
            "민감계수 ci": f"{comp.sensitivity_coeff:.4g}",
            "배분 비율": f"{comp.contribution_ratio:.1f}%",
            "허용 u(xi) max": f"{comp.max_allowed_std_uncertainty:.4e}",
            "허용 반폭 a (균일)": f"{comp.max_allowed_half_width_rect:.4e}",
            "허용 U (k=2)": f"{comp.max_allowed_expanded_U:.4e}",
        }

        if comp.current_std_uncertainty is not None:
            row["현재 u(xi)"] = f"{comp.current_std_uncertainty:.4e}"
            margin = comp.max_allowed_std_uncertainty - comp.current_std_uncertainty
            if margin >= 0:
                row["여유"] = f"✅ +{margin:.4e}"
            else:
                row["여유"] = f"❌ {margin:.4e}"
        else:
            row["현재 u(xi)"] = "—"
            row["여유"] = "—"

        row["판정"] = "✅" if comp.is_feasible else "❌"
        budget_data.append(row)

    st.dataframe(budget_data, use_container_width=True)

    # 시각화: 바 차트
    import plotly.graph_objects as go

    fig = go.Figure()

    symbols = [c.symbol for c in result.components]
    max_u = [c.max_allowed_std_uncertainty for c in result.components]
    current_u = [c.current_std_uncertainty if c.current_std_uncertainty is not None else 0 for c in result.components]

    fig.add_trace(go.Bar(
        name="허용 최대 u(xi)",
        x=symbols,
        y=max_u,
        marker_color="steelblue",
        opacity=0.7,
    ))

    if any(c.current_std_uncertainty is not None for c in result.components):
        colors = ["green" if c.is_feasible else "red" for c in result.components]
        fig.add_trace(go.Bar(
            name="현재 u(xi)",
            x=symbols,
            y=current_u,
            marker_color=colors,
            opacity=0.9,
        ))

    fig.update_layout(
        title="성분별 허용 불확도 vs 현재 불확도",
        xaxis_title="불확도 성분",
        yaxis_title=f"표준불확도 ({result.measurand_unit})",
        barmode="group",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # 실무 가이드
    st.divider()
    st.subheader("💡 실무 가이드")

    for comp in result.components:
        u_max = comp.max_allowed_std_uncertainty
        a_max = comp.max_allowed_half_width_rect

        with st.expander(f"**{comp.symbol}** — 허용 u ≤ {u_max:.4e} {result.measurand_unit}"):
            st.markdown(
                f"- **표준불확도 상한:** u({comp.symbol}) ≤ {u_max:.4e} {result.measurand_unit}\n"
                f"- **균일분포 반폭 상한:** a ≤ {a_max:.4e} {result.measurand_unit}\n"
                f"- **확장불확도 상한 (k=2):** U ≤ {comp.max_allowed_expanded_U:.4e} {result.measurand_unit}\n"
                f"- **예산 배분 비율:** {comp.contribution_ratio:.1f}%\n"
            )

            if not comp.is_feasible and comp.current_std_uncertainty is not None:
                reduction = comp.current_std_uncertainty - u_max
                pct = (reduction / comp.current_std_uncertainty) * 100
                st.error(
                    f"⚠️ 현재값 {comp.current_std_uncertainty:.4e}에서 "
                    f"{reduction:.4e} ({pct:.0f}%) 줄여야 합니다."
                )


# ──────────────────────────────────────────
# Step 1: 측정 모델 정의
# ──────────────────────────────────────────
st.subheader("📐 Step 1: 측정 모델 정의")

model_presets = {
    "직접 입력": {"expr": "a + b + c", "symbols": "a, b, c"},
    "길이 (블록게이지)": {"expr": "dL + d_std + alpha_diff * Ls * dT + d_res", "symbols": "dL, d_std, alpha_diff, dT, d_res"},
    "질량 (분동)": {"expr": "dm_d + d_std + dm_b + dm_a", "symbols": "dm_d, d_std, dm_b, dm_a"},
    "온도 (온도계)": {"expr": "dT_ind + d_std + dT_stab + dT_uni + dT_res", "symbols": "dT_ind, d_std, dT_stab, dT_uni, dT_res"},
    "압력 (압력계)": {"expr": "dP_ind + d_std + dP_res + dP_hyst + dP_zero", "symbols": "dP_ind, d_std, dP_res, dP_hyst, dP_zero"},
}

preset_name = st.selectbox("프리셋 선택", list(model_presets.keys()))
preset = model_presets[preset_name]

col_model1, col_model2 = st.columns(2)
with col_model1:
    model_expr = st.text_input("측정 모델 수학식", value=preset["expr"], key="rev_model")
with col_model2:
    symbols_str = st.text_input("입력량 기호 (쉼표 구분)", value=preset["symbols"], key="rev_symbols")

symbol_names = [s.strip() for s in symbols_str.split(",") if s.strip()]

col_unit1, col_unit2 = st.columns(2)
with col_unit1:
    measurand_name = st.text_input("측정량 이름", value="Y", key="rev_meas_name")
with col_unit2:
    measurand_unit = st.text_input("단위", value="µm", key="rev_meas_unit")

# ──────────────────────────────────────────
# Step 2: 민감계수 입력
# ──────────────────────────────────────────
st.divider()
st.subheader("📊 Step 2: 민감계수 (ci) 입력")

st.markdown(
    "각 입력량의 민감계수를 입력하세요. "
    "이미 불확도 계산을 해본 경우 예산표에서 확인할 수 있습니다. "
    "모델이 `a + b + c` 형태(모두 덧셈)이면 민감계수는 전부 1입니다."
)

# 모델 파싱 시도 — 자동 민감계수 계산
auto_sensitivities = {}
try:
    test_model = MeasurementModel(model_expr, symbol_names)
    test_model.parse()
    test_model.compute_sensitivities()
    # 기본 입력값(모두 1)으로 평가
    default_vals = {sym: 1.0 for sym in symbol_names}
    for sym in symbol_names:
        try:
            ci = test_model.evaluate_sensitivity(sym, default_vals)
            auto_sensitivities[sym] = ci
        except Exception:
            auto_sensitivities[sym] = 1.0
except Exception:
    pass

sensitivity_inputs = {}
cols = st.columns(min(len(symbol_names), 4))
for i, sym in enumerate(symbol_names):
    with cols[i % len(cols)]:
        default_ci = auto_sensitivities.get(sym, 1.0)
        ci = st.number_input(
            f"c({sym})",
            value=float(default_ci),
            format="%.4g",
            key=f"rev_ci_{sym}",
            help=f"∂f/∂{sym} — 민감계수",
        )
        sensitivity_inputs[sym] = ci

# ──────────────────────────────────────────
# Step 3: 목표 설정 및 역설계 실행
# ──────────────────────────────────────────
st.divider()
st.subheader("🎯 Step 3: 목표 확장불확도 설정")

col_t1, col_t2 = st.columns(2)
with col_t1:
    target_U = st.number_input(
        f"목표 확장불확도 U ({measurand_unit})",
        value=0.1,
        format="%.4g",
        step=0.01,
        key="rev_target_U",
        help="KOLAS CMC 등록을 위한 목표 확장불확도",
    )
with col_t2:
    target_k = st.number_input(
        "포함인자 k",
        value=2.0,
        step=0.1,
        key="rev_target_k",
    )

# ──────────────────────────────────────────
# 모드 A: 목표 CMC → 허용 불확도
# ──────────────────────────────────────────
if analysis_mode == "🎯 목표 CMC → 허용 불확도":

    st.divider()
    allocation = st.radio(
        "예산 배분 방법",
        ["균등 배분 — 모든 성분에 동일 예산", "가중 배분 — 현재 기여율 비례"],
        index=0,
        horizontal=True,
    )

    # 가중 배분일 때 현재 불확도 입력
    current_uncertainties = {}
    if "가중" in allocation:
        st.markdown("**현재 각 성분의 표준불확도 u(xi):**")
        cu_cols = st.columns(min(len(symbol_names), 4))
        for i, sym in enumerate(symbol_names):
            with cu_cols[i % len(cu_cols)]:
                cu = st.number_input(
                    f"u({sym}) 현재값",
                    value=0.01,
                    format="%.4e",
                    key=f"rev_cu_{sym}",
                )
                current_uncertainties[sym] = cu

    if st.button("🔄 역설계 실행", type="primary", use_container_width=True, key="rev_calc"):
        engine = ReverseUncertaintyEngine(
            model_expression=model_expr,
            symbol_names=symbol_names,
            sensitivity_coefficients=sensitivity_inputs,
            measurand_name=measurand_name,
            measurand_unit=measurand_unit,
        )

        if "균등" in allocation:
            result = engine.reverse_equal(
                target_U=target_U,
                k=target_k,
                current_uncertainties=current_uncertainties if current_uncertainties else None,
            )
        else:
            result = engine.reverse_weighted(
                target_U=target_U,
                k=target_k,
                current_uncertainties=current_uncertainties,
            )

        _show_reverse_results(result)

# ──────────────────────────────────────────
# 모드 B: 단일 성분 역산 (What-If)
# ──────────────────────────────────────────
elif analysis_mode == "🔍 단일 성분 역산 (What-If)":

    st.divider()
    st.markdown(
        "**시나리오:** 나머지 성분을 고정하고, 특정 성분의 허용 최대값만 역산합니다.\n\n"
        "예: \"표준기 불확도가 이 값인 상태에서, 반복성은 얼마까지 허용되는가?\""
    )

    target_sym = st.selectbox("역산할 성분", symbol_names, key="rev_target_sym")

    st.markdown("**고정할 나머지 성분의 표준불확도:**")
    fixed_uncertainties = {}
    fix_cols = st.columns(min(len(symbol_names), 4))
    for i, sym in enumerate(symbol_names):
        with fix_cols[i % len(fix_cols)]:
            if sym == target_sym:
                st.text_input(f"u({sym})", value="← 역산 대상", disabled=True, key=f"rev_fix_{sym}")
            else:
                fu = st.number_input(
                    f"u({sym})",
                    value=0.01,
                    format="%.4e",
                    key=f"rev_fix_{sym}",
                )
                fixed_uncertainties[sym] = fu

    if st.button("🔄 역설계 실행", type="primary", use_container_width=True, key="rev_single_calc"):
        engine = ReverseUncertaintyEngine(
            model_expression=model_expr,
            symbol_names=symbol_names,
            sensitivity_coefficients=sensitivity_inputs,
            measurand_name=measurand_name,
            measurand_unit=measurand_unit,
        )

        result = engine.reverse_single_component(
            target_U=target_U,
            target_symbol=target_sym,
            fixed_uncertainties=fixed_uncertainties,
            k=target_k,
        )

        _show_reverse_results(result)
