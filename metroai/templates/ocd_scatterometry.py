"""OCD (Optical Critical Dimension) Scatterometry 측정 불확도 템플릿.

박수연(MetroAI advisor) 통합 — v0.6.0 신규.

광학 산란 측정(Spectroscopic Ellipsometry / Reflectometry) 기반
반도체 패턴 CD(Critical Dimension), 높이, 측벽각도 측정 불확도.

측정 모델 (간소화): CD = CD_fit + bias_model + drift_tool
  - CD_fit: RCWA 역추정 결과
  - bias_model: 모델-실측 편향 (TEM 대비)
  - drift_tool: 장비 드리프트

참조: SEMI MF-1789, ISO 18516
RCWA(Rigorous Coupled Wave Analysis) 기반 forward modeling.
"""

from __future__ import annotations

import numpy as np

from ..core.distributions import DistributionType, UncertaintySource
from ..core.gum import GUMCalculator
from ..core.model import MeasurementModel


def create_ocd_scatterometry_template(
    nominal_cd_nm: float = 32.0,
    cd_fit_readings_nm: list[float] | None = None,
    model_bias_nm: float = 0.3,
    model_bias_uncertainty_nm: float = 0.5,
    tool_drift_nm: float = 0.0,
    tool_drift_uncertainty_nm: float = 0.2,
    wavelength_calibration_nm: float = 1.0,
    wavelength_uncertainty_pct: float = 0.1,
    n_k_uncertainty_pct: float = 1.0,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """OCD Scatterometry CD 측정 불확도 예산 템플릿.

    Args:
        nominal_cd_nm: 공칭 CD (nm)
        cd_fit_readings_nm: RCWA fit 반복 결과 (nm)
        model_bias_nm: 모델-실측 편향 (TEM 기준, nm)
        model_bias_uncertainty_nm: 편향 불확도 (nm)
        tool_drift_nm: 장비 드리프트 (nm)
        tool_drift_uncertainty_nm: 드리프트 불확도 (nm)
        wavelength_calibration_nm: 파장 캘리브레이션 인자
        wavelength_uncertainty_pct: 파장 불확도 (% relative)
        n_k_uncertainty_pct: 광학상수(n,k) 불확도 (% relative)

    Returns:
        (model, sources, config) 튜플
    """
    if cd_fit_readings_nm is None:
        # 32nm 노드 라인 패턴 예시
        cd_fit_readings_nm = [
            31.85, 32.12, 31.98, 32.05, 31.92,
            32.08, 31.95, 32.02, 31.88, 32.10,
        ]

    # 측정 모델: CD = CD_fit + bias + drift + nk_corr * CD_fit
    # nk_corr는 광학상수 불확도가 CD에 미치는 영향을 비례 항으로 표현
    model = MeasurementModel(
        expression_str="CD_fit + bias + drift + nk_corr * CD_fit / 100",
        symbol_names=["CD_fit", "bias", "drift", "nk_corr"],
    )

    mean_cd = float(np.mean(cd_fit_readings_nm))

    sources = [
        # 1. RCWA fit 결과 반복성 (A형)
        UncertaintySource(
            name="RCWA fit 반복",
            symbol="CD_fit",
            eval_type="A",
            value=mean_cd,  # 측정값 평균 (모델 평가용)
            repeat_data=cd_fit_readings_nm,
            unit="nm",
        ),
        # 2. 모델-실측 편향 (B형, 정규분포 — TEM 기준)
        UncertaintySource(
            name="모델-실측 편향 (TEM ref)",
            symbol="bias",
            eval_type="B",
            value=model_bias_nm,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=model_bias_uncertainty_nm * 2,
            coverage_factor_input=2.0,
            unit="nm",
        ),
        # 3. 장비 드리프트 (B형, 균일분포)
        UncertaintySource(
            name="장비 드리프트",
            symbol="drift",
            eval_type="B",
            value=tool_drift_nm,
            distribution=DistributionType.RECTANGULAR,
            half_width=tool_drift_uncertainty_nm,
            unit="nm",
        ),
        # 4. 광학상수 (n,k) 불확도 (B형, 균일분포, % relative)
        UncertaintySource(
            name="광학상수 (n, k) 불확도",
            symbol="nk_corr",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=n_k_uncertainty_pct,
            unit="%",
        ),
    ]

    config = {
        "template_name": "OCD Scatterometry CD 측정",
        "field": "반도체 CD",
        "standard": "SEMI MF-1789, ISO 18516",
        "method": "RCWA (Rigorous Coupled Wave Analysis)",
        "nominal_cd_nm": nominal_cd_nm,
        "measurand_name": "CD",
        "measurand_unit": "nm",
        "description": "광학 산란 측정 기반 반도체 패턴 CD 측정 불확도 예산",
    }

    return model, sources, config


def create_ocd_scatterometry_calculator(**kwargs) -> GUMCalculator:
    """OCD Scatterometry GUM 계산기를 직접 생성하여 반환."""
    model, sources, config = create_ocd_scatterometry_template(**kwargs)
    return GUMCalculator(
        model=model,
        sources=sources,
        measurand_name=config["measurand_name"],
        measurand_unit=config["measurand_unit"],
    )
