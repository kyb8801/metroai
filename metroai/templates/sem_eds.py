"""SEM-EDS 원소 정량 분석 불확도 템플릿.

박수연(MetroAI advisor) 통합 — v0.6.0 신규.

주사전자현미경 에너지분산형 X선 분광기(SEM-EDS)를 이용한
원소 농도(wt%) 측정 불확도 예산. ZAF 보정 모델 기반.

측정 모델: C_i = k_i * ZAF_i * C_ref_i
  - k_i: k-ratio (시료/표준시료 X선 강도비)
  - ZAF: matrix correction factor (Z·A·F)
  - C_ref_i: 표준시료 농도

ZAF = Z (원자번호) * A (흡수) * F (형광) 보정
"""

from __future__ import annotations

import numpy as np

from ..core.distributions import DistributionType, UncertaintySource
from ..core.gum import GUMCalculator
from ..core.model import MeasurementModel


def create_sem_eds_template(
    element_symbol: str = "Cu",
    k_ratio_readings: list[float] | None = None,
    standard_concentration_wt: float = 100.0,
    standard_uncertainty_wt: float = 0.1,
    zaf_factor: float = 1.02,
    zaf_uncertainty_pct: float = 2.0,
    beam_current_stability_pct: float = 0.5,
    deadtime_correction: float = 1.0,
    deadtime_uncertainty: float = 0.005,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """SEM-EDS 원소 정량 불확도 예산 템플릿.

    Args:
        element_symbol: 분석 원소 (예: "Cu", "Fe", "Ni")
        k_ratio_readings: k-ratio 반복 측정값
        standard_concentration_wt: 표준시료 농도 (wt%)
        standard_uncertainty_wt: 표준시료 인증 불확도 (wt%)
        zaf_factor: ZAF 보정 인자
        zaf_uncertainty_pct: ZAF 불확도 (% relative)
        beam_current_stability_pct: 빔전류 안정성 (% relative)
        deadtime_correction: 데드타임 보정 인자
        deadtime_uncertainty: 데드타임 불확도 (absolute)

    Returns:
        (model, sources, config) 튜플
    """
    if k_ratio_readings is None:
        # Cu 표준시료 대비 약 0.65 k-ratio (예시)
        k_ratio_readings = [0.6510, 0.6525, 0.6498, 0.6512, 0.6520, 0.6505]

    # 측정 모델: C = k * ZAF * C_ref * I_stab * dt
    model = MeasurementModel(
        expression_str="k * ZAF * C_ref * I_stab * dt",
        symbol_names=["k", "ZAF", "C_ref", "I_stab", "dt"],
    )

    mean_k = float(np.mean(k_ratio_readings))

    sources = [
        # 1. k-ratio 반복 측정 (A형)
        UncertaintySource(
            name="k-ratio 반복 측정",
            symbol="k",
            eval_type="A",
            value=mean_k,  # 측정값 평균 (모델 평가용)
            repeat_data=k_ratio_readings,
            unit="-",
        ),
        # 2. ZAF 보정 불확도 (B형, 정규분포)
        UncertaintySource(
            name="ZAF matrix correction",
            symbol="ZAF",
            eval_type="B",
            value=zaf_factor,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=zaf_factor * zaf_uncertainty_pct / 100.0 * 2,
            coverage_factor_input=2.0,
            unit="-",
        ),
        # 3. 표준시료 인증 농도 (B형, 정규분포 — 인증서 기반)
        UncertaintySource(
            name="표준시료 인증 농도",
            symbol="C_ref",
            eval_type="B",
            value=standard_concentration_wt,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=standard_uncertainty_wt,
            coverage_factor_input=2.0,
            unit="wt%",
        ),
        # 4. 빔 전류 안정성 (B형, 균일분포)
        UncertaintySource(
            name="빔 전류 안정성",
            symbol="I_stab",
            eval_type="B",
            value=1.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=beam_current_stability_pct / 100.0,
            unit="-",
        ),
        # 5. 데드타임 보정 (B형, 균일분포)
        UncertaintySource(
            name="데드타임 보정",
            symbol="dt",
            eval_type="B",
            value=deadtime_correction,
            distribution=DistributionType.RECTANGULAR,
            half_width=deadtime_uncertainty,
            unit="-",
        ),
    ]

    config = {
        "template_name": f"SEM-EDS 원소 정량 ({element_symbol})",
        "field": "원소 분석",
        "standard": "ISO 22489",
        "element": element_symbol,
        "measurand_name": f"C_{element_symbol}",
        "measurand_unit": "wt%",
        "description": "SEM-EDS ZAF 보정 기반 원소 농도 측정 불확도 예산",
    }

    return model, sources, config


def create_sem_eds_calculator(**kwargs) -> GUMCalculator:
    """SEM-EDS 원소 정량 GUM 계산기를 직접 생성하여 반환."""
    model, sources, config = create_sem_eds_template(**kwargs)
    return GUMCalculator(
        model=model,
        sources=sources,
        measurand_name=config["measurand_name"],
        measurand_unit=config["measurand_unit"],
    )
