"""질량 교정 템플릿 — 분동 교정 불확도.

측정 모델: m_conv = m_s + dm_d + dm_b + dm_a
  - m_s: 표준 분동 질량 (공칭값에서의 보정값)
  - dm_d: 저울 지시값 차이 (시험편 - 표준분동)
  - dm_b: 부력 보정
  - dm_a: 자기적 효과 보정 (기본 0)
"""

from __future__ import annotations

from ..core.distributions import DistributionType, UncertaintySource
from ..core.gum import GUMCalculator
from ..core.model import MeasurementModel


def create_mass_template(
    nominal_mass_g: float = 100.0,
    class_name: str = "E2",
    std_cert_U: float = 0.05,
    std_cert_k: float = 2.0,
    readings_mg: list[float] | None = None,
    resolution_mg: float = 0.001,
    buoyancy_unc_mg: float = 0.001,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """분동 교정 불확도 예산 템플릿 생성.

    Args:
        nominal_mass_g: 공칭 질량 (g)
        class_name: 분동 등급
        std_cert_U: 표준분동 교정 확장불확도 (mg)
        std_cert_k: 표준분동 교정 포함인자
        readings_mg: 반복 측정 차이값 (mg), 시험편 - 표준분동
        resolution_mg: 저울 분해능 최소 눈금 (mg)
        buoyancy_unc_mg: 부력 보정 불확도 (mg)

    Returns:
        (model, sources, config) 튜플
    """
    if readings_mg is None:
        readings_mg = [0.010, 0.012, 0.008, 0.011, 0.009]

    model = MeasurementModel(
        expression_str="dm_d + d_std + dm_b + dm_a",
        symbol_names=["dm_d", "d_std", "dm_b", "dm_a"],
    )

    sources = [
        # 1. 저울 반복성 (A형)
        UncertaintySource(
            name="저울 반복 측정",
            symbol="dm_d",
            eval_type="A",
            repeat_data=readings_mg,
            unit="mg",
        ),
        # 2. 표준분동 교정 불확도 (B형, 정규분포)
        UncertaintySource(
            name="표준분동 교정 불확도",
            symbol="d_std",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=std_cert_U,
            coverage_factor_input=std_cert_k,
            unit="mg",
        ),
        # 3. 저울 분해능 (B형, 균일분포)
        UncertaintySource(
            name="저울 분해능",
            symbol="dm_b",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=resolution_mg * 0.5,
            unit="mg",
        ),
        # 4. 부력 보정 불확도 (B형, 균일분포)
        UncertaintySource(
            name="부력 보정 불확도",
            symbol="dm_a",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=buoyancy_unc_mg,
            unit="mg",
        ),
    ]

    config = {
        "template_name": "분동 교정",
        "field": "질량",
        "nominal_mass_g": nominal_mass_g,
        "class_name": class_name,
        "measurand_name": "m",
        "measurand_unit": "mg",
        "description": f"{class_name}급 분동 {nominal_mass_g}g 교정 불확도 예산",
    }

    return model, sources, config
