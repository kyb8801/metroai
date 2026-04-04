"""온도 교정 템플릿 — 온도계 교정 불확도.

측정 모델: T_x = T_s + dT_ind + dT_drift + dT_homog
  - T_s: 표준 온도계 지시값 (교정점)
  - dT_ind: 시험편 - 표준기 지시값 차이
  - dT_drift: 항온조 안정도
  - dT_homog: 항온조 균일도
"""

from __future__ import annotations

from ..core.distributions import DistributionType, UncertaintySource
from ..core.model import MeasurementModel


def create_temperature_template(
    cal_point_C: float = 100.0,
    std_cert_U_C: float = 0.02,
    std_cert_k: float = 2.0,
    readings_C: list[float] | None = None,
    stability_C: float = 0.02,
    uniformity_C: float = 0.05,
    resolution_C: float = 0.01,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """온도계 교정 불확도 예산 템플릿 생성.

    Args:
        cal_point_C: 교정점 온도 (°C)
        std_cert_U_C: 표준 온도계 교정 확장불확도 (°C)
        std_cert_k: 표준 온도계 교정 포함인자
        readings_C: 반복 측정 (시험편-표준기 차이, °C)
        stability_C: 항온조 안정도 반폭 (°C)
        uniformity_C: 항온조 균일도 반폭 (°C)
        resolution_C: 시험편 분해능 반폭 (°C)

    Returns:
        (model, sources, config) 튜플
    """
    if readings_C is None:
        readings_C = [0.01, 0.02, -0.01, 0.00, 0.01]

    model = MeasurementModel(
        expression_str="dT_ind + d_std + dT_stab + dT_uni + dT_res",
        symbol_names=["dT_ind", "d_std", "dT_stab", "dT_uni", "dT_res"],
    )

    sources = [
        # 1. 반복성 (A형)
        UncertaintySource(
            name="반복 측정",
            symbol="dT_ind",
            eval_type="A",
            repeat_data=readings_C,
            unit="°C",
        ),
        # 2. 표준 온도계 교정 불확도 (B형, 정규분포)
        UncertaintySource(
            name="표준 온도계 교정 불확도",
            symbol="d_std",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=std_cert_U_C,
            coverage_factor_input=std_cert_k,
            unit="°C",
        ),
        # 3. 항온조 안정도 (B형, 균일분포)
        UncertaintySource(
            name="항온조 안정도",
            symbol="dT_stab",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=stability_C,
            unit="°C",
        ),
        # 4. 항온조 균일도 (B형, 균일분포)
        UncertaintySource(
            name="항온조 균일도",
            symbol="dT_uni",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=uniformity_C,
            unit="°C",
        ),
        # 5. 시험편 분해능 (B형, 균일분포)
        UncertaintySource(
            name="시험편 분해능",
            symbol="dT_res",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=resolution_C * 0.5,
            unit="°C",
        ),
    ]

    config = {
        "template_name": "온도계 교정",
        "field": "온도",
        "cal_point_C": cal_point_C,
        "measurand_name": "T",
        "measurand_unit": "°C",
        "description": f"온도계 교정 ({cal_point_C}°C 교정점) 불확도 예산",
    }

    return model, sources, config
