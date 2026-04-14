"""전기 교정 템플릿 — 직류 전압 비교 교정 (v0.5.0).

KOLAS 전기·자기/전자파 분야 (163항목 중 가장 기본적인 DC 전압).
교정 모델: V = dV_ind + d_std + dV_res + dV_stab + dV_temp
"""

from __future__ import annotations

from ..core.distributions import DistributionType, UncertaintySource
from ..core.model import MeasurementModel


def create_dc_voltage_template(
    *,
    nominal_voltage_V: float = 10.0,
    readings_deviation: list[float] | None = None,
    std_cert_U: float = 0.0001,
    std_cert_k: float = 2.0,
    resolution_V: float = 0.00001,
    stability_V: float = 0.00005,
    temp_coeff_V: float = 0.00002,
) -> tuple:
    """직류 전압 비교 교정 불확도 템플릿.

    Args:
        nominal_voltage_V: 공칭 전압 (V)
        readings_deviation: 반복 측정 편차 (V)
        std_cert_U: 표준기 확장불확도 (V)
        std_cert_k: 표준기 포함인자
        resolution_V: 측정기 분해능 (V)
        stability_V: 측정기 안정도 (V, 24시간 기준)
        temp_coeff_V: 온도 계수에 의한 불확도 (V)

    Returns:
        (model, sources, config)
    """
    if readings_deviation is None:
        readings_deviation = [0.00001, 0.00002, -0.00001, 0.00001, 0.00000]

    model = MeasurementModel(
        "dV_ind + d_std + dV_res + dV_stab + dV_temp",
        symbol_names=["dV_ind", "d_std", "dV_res", "dV_stab", "dV_temp"],
    )

    sources = [
        # 1. 반복 측정 (A형)
        UncertaintySource(
            name="반복 측정",
            symbol="dV_ind",
            eval_type="A",
            repeat_data=readings_deviation,
        ),
        # 2. 표준기 교정 불확도 (B형, 정규)
        UncertaintySource(
            name="표준기 교정 불확도",
            symbol="d_std",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=std_cert_U,
            coverage_factor_input=std_cert_k,
        ),
        # 3. 분해능 (B형, 균일)
        UncertaintySource(
            name="측정기 분해능",
            symbol="dV_res",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=resolution_V / 2,
        ),
        # 4. 안정도 (B형, 균일)
        UncertaintySource(
            name="측정기 안정도 (24h)",
            symbol="dV_stab",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=stability_V,
        ),
        # 5. 온도 계수 (B형, 균일)
        UncertaintySource(
            name="온도 계수",
            symbol="dV_temp",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=temp_coeff_V,
        ),
    ]

    config = {
        "measurand_name": "V",
        "measurand_unit": "V",
        "nominal_value": nominal_voltage_V,
        "template_name": "직류 전압 비교 교정",
    }

    return model, sources, config
