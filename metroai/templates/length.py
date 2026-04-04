"""길이 교정 템플릿 — 블록게이지 교정 불확도.

KOLAS-G-002 부록 예제 기반 블록게이지 비교 교정 불확도 예산.
측정 모델: L = Ls + dL + (alpha_s - alpha_x) * Ls * dT
  - Ls: 표준 블록게이지 길이 (공칭값)
  - dL: 비교기 지시값 차이 (시험편 - 표준기)
  - alpha_s: 표준기 열팽창계수
  - alpha_x: 시험편 열팽창계수
  - dT: 온도 편차 (시험편 온도 - 20°C)
"""

from __future__ import annotations

from ..core.distributions import DistributionType, UncertaintySource
from ..core.gum import GUMCalculator
from ..core.model import MeasurementModel


def create_gauge_block_template(
    nominal_length_mm: float = 50.0,
    comparator_readings: list[float] | None = None,
    std_cert_uncertainty_um: float = 0.05,
    std_cert_k: float = 2.0,
    alpha_s: float = 11.5e-6,
    alpha_x: float = 11.5e-6,
    alpha_uncertainty: float = 1.0e-6,
    temp_deviation_C: float = 0.0,
    temp_uncertainty_C: float = 0.5,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """블록게이지 교정 불확도 예산 템플릿 생성.

    Args:
        nominal_length_mm: 공칭 길이 (mm)
        comparator_readings: 비교기 반복 측정값 (μm 단위 차이)
        std_cert_uncertainty_um: 표준기 교정 확장불확도 (μm)
        std_cert_k: 표준기 교정 포함인자
        alpha_s: 표준기 열팽창계수 (/°C)
        alpha_x: 시험편 열팽창계수 (/°C)
        alpha_uncertainty: 열팽창계수 불확도 (/°C)
        temp_deviation_C: 온도 편차 (°C)
        temp_uncertainty_C: 온도 불확도 (°C, 반폭)

    Returns:
        (model, sources, config) 튜플
    """
    if comparator_readings is None:
        comparator_readings = [0.10, 0.12, 0.08, 0.11, 0.09]  # μm 단위 예시

    # 측정 모델 (μm 단위 통일)
    # L = Ls + dL + (alpha_s - alpha_x) * Ls * dT
    # Ls는 mm → μm 변환하여 열팽창 항 계산 시 사용
    # 단순화: 열팽창 보정항이 μm 단위가 되도록 Ls를 mm로 두고 alpha*Ls*dT의 단위를 μm로
    model = MeasurementModel(
        expression_str="dL + d_std + alpha_diff * Ls_mm * 1000 * dT",
        symbol_names=["dL", "d_std", "alpha_diff", "Ls_mm", "dT"],
    )

    import numpy as np

    mean_dL = float(np.mean(comparator_readings))

    sources = [
        # 1. 비교 측정 반복성 (A형)
        UncertaintySource(
            name="비교기 반복 측정",
            symbol="dL",
            eval_type="A",
            repeat_data=comparator_readings,
            unit="μm",
        ),
        # 2. 표준기 교정 불확도 (B형, 정규분포)
        UncertaintySource(
            name="표준기 교정 불확도",
            symbol="d_std",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=std_cert_uncertainty_um,
            coverage_factor_input=std_cert_k,
            unit="μm",
        ),
        # 3. 열팽창계수 차이 불확도 (B형, 균일분포)
        UncertaintySource(
            name="열팽창계수 차이",
            symbol="alpha_diff",
            eval_type="B",
            value=alpha_s - alpha_x,
            distribution=DistributionType.RECTANGULAR,
            half_width=alpha_uncertainty,
            unit="/°C",
        ),
        # 4. 표준기 공칭 길이 (상수 — 불확도 0으로 처리)
        UncertaintySource(
            name="표준기 공칭 길이",
            symbol="Ls_mm",
            eval_type="B",
            value=nominal_length_mm,
            std_uncertainty=0.0,  # 공칭값은 정확
            unit="mm",
        ),
        # 5. 온도 편차 (B형, 균일분포)
        UncertaintySource(
            name="온도 편차",
            symbol="dT",
            eval_type="B",
            value=temp_deviation_C,
            distribution=DistributionType.RECTANGULAR,
            half_width=temp_uncertainty_C,
            unit="°C",
        ),
    ]

    config = {
        "template_name": "블록게이지 비교 교정",
        "field": "길이",
        "nominal_length_mm": nominal_length_mm,
        "measurand_name": "L",
        "measurand_unit": "μm",
        "description": "블록게이지 비교법에 의한 길이 교정 불확도 예산",
    }

    return model, sources, config


def create_gauge_block_calculator(
    **kwargs,
) -> GUMCalculator:
    """블록게이지 교정 GUM 계산기를 직접 생성하여 반환."""
    model, sources, config = create_gauge_block_template(**kwargs)
    return GUMCalculator(
        model=model,
        sources=sources,
        measurand_name=config["measurand_name"],
        measurand_unit=config["measurand_unit"],
    )
