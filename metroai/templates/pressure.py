"""압력 교정 템플릿 — 압력계 교정 불확도.

측정 모델: P_x = P_s + dP_ind + dP_zero + dP_hyst
  - P_s: 표준 압력계 값
  - dP_ind: 시험편 - 표준기 차이
  - dP_zero: 영점 보정
  - dP_hyst: 이력차
"""

from __future__ import annotations

from ..core.distributions import DistributionType, UncertaintySource
from ..core.model import MeasurementModel


def create_pressure_template(
    cal_point_MPa: float = 10.0,
    std_cert_U_MPa: float = 0.002,
    std_cert_k: float = 2.0,
    readings_MPa: list[float] | None = None,
    resolution_MPa: float = 0.001,
    hysteresis_MPa: float = 0.002,
    zero_drift_MPa: float = 0.001,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """압력계 교정 불확도 예산 템플릿 생성.

    Args:
        cal_point_MPa: 교정점 압력 (MPa)
        std_cert_U_MPa: 표준기 교정 확장불확도 (MPa)
        std_cert_k: 표준기 교정 포함인자
        readings_MPa: 반복 측정 차이값 (MPa)
        resolution_MPa: 시험편 분해능 (MPa)
        hysteresis_MPa: 이력차 최대값 (MPa)
        zero_drift_MPa: 영점 드리프트 (MPa)

    Returns:
        (model, sources, config) 튜플
    """
    if readings_MPa is None:
        readings_MPa = [0.001, 0.002, -0.001, 0.000, 0.001]

    model = MeasurementModel(
        expression_str="dP_ind + d_std + dP_res + dP_hyst + dP_zero",
        symbol_names=["dP_ind", "d_std", "dP_res", "dP_hyst", "dP_zero"],
    )

    sources = [
        # 1. 반복성 (A형)
        UncertaintySource(
            name="반복 측정",
            symbol="dP_ind",
            eval_type="A",
            repeat_data=readings_MPa,
            unit="MPa",
        ),
        # 2. 표준기 교정 불확도 (B형, 정규분포)
        UncertaintySource(
            name="표준기 교정 불확도",
            symbol="d_std",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=std_cert_U_MPa,
            coverage_factor_input=std_cert_k,
            unit="MPa",
        ),
        # 3. 시험편 분해능 (B형, 균일분포)
        UncertaintySource(
            name="시험편 분해능",
            symbol="dP_res",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=resolution_MPa * 0.5,
            unit="MPa",
        ),
        # 4. 이력차 (B형, 균일분포)
        UncertaintySource(
            name="이력차",
            symbol="dP_hyst",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=hysteresis_MPa,
            unit="MPa",
        ),
        # 5. 영점 드리프트 (B형, 균일분포)
        UncertaintySource(
            name="영점 드리프트",
            symbol="dP_zero",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=zero_drift_MPa,
            unit="MPa",
        ),
    ]

    config = {
        "template_name": "압력계 교정",
        "field": "압력",
        "cal_point_MPa": cal_point_MPa,
        "measurand_name": "P",
        "measurand_unit": "MPa",
        "description": f"압력계 교정 ({cal_point_MPa} MPa 교정점) 불확도 예산",
    }

    return model, sources, config
