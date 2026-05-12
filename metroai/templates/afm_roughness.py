"""AFM 표면 거칠기(Sa, Sq) 측정 불확도 템플릿.

박수연(MetroAI advisor) 통합 — v0.6.0 신규.

원자력간현미경(AFM)을 이용한 표면 거칠기 파라미터(ISO 25178-2) 측정 불확도.

측정 파라미터:
  - Sa: 산술 평균 높이 (arithmetic mean height)
  - Sq: RMS 높이 (root mean square height)

측정 모델: Sa_corrected = Sa_raw * k_z * (1 + tilt_corr) - bg
  - Sa_raw: 원시 측정값 (nm)
  - k_z: z-축 스캐너 캘리브레이션 인자
  - tilt_corr: 시료 기울기 보정
  - bg: 백그라운드 노이즈

참조: VLSI Standards STR10-180nm (Si grating CRM)
"""

from __future__ import annotations

import numpy as np

from ..core.distributions import DistributionType, UncertaintySource
from ..core.gum import GUMCalculator
from ..core.model import MeasurementModel


def create_afm_roughness_template(
    parameter: str = "Sa",  # "Sa" or "Sq"
    sa_readings_nm: list[float] | None = None,
    z_calibration_factor: float = 1.0,
    z_calibration_uncertainty_pct: float = 1.5,
    tilt_correction: float = 0.0,
    tilt_uncertainty_pct: float = 0.3,
    background_noise_nm: float = 0.05,
    background_uncertainty_nm: float = 0.02,
    scan_size_um: float = 10.0,
    pixel_density: int = 512,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """AFM 표면 거칠기 측정 불확도 예산 템플릿.

    Args:
        parameter: 측정 파라미터 ("Sa" or "Sq")
        sa_readings_nm: 반복 측정값 (nm)
        z_calibration_factor: z-축 캘리브레이션 인자
        z_calibration_uncertainty_pct: z-축 캘리브레이션 불확도 (% relative)
        tilt_correction: 시료 기울기 보정
        tilt_uncertainty_pct: 기울기 불확도 (% relative)
        background_noise_nm: 백그라운드 노이즈 평균 (nm)
        background_uncertainty_nm: 백그라운드 노이즈 불확도 (nm)
        scan_size_um: 스캔 크기 (μm)
        pixel_density: 픽셀 밀도

    Returns:
        (model, sources, config) 튜플
    """
    if sa_readings_nm is None:
        # 일반적 Si wafer Sa ≈ 0.3 nm
        sa_readings_nm = [0.298, 0.305, 0.302, 0.299, 0.301, 0.304, 0.297]

    # 측정 모델: Sa_corr = Sa_raw * k_z * (1 + tilt) - bg
    model = MeasurementModel(
        expression_str="Sa_raw * k_z * (1 + tilt) - bg",
        symbol_names=["Sa_raw", "k_z", "tilt", "bg"],
    )

    mean_sa = float(np.mean(sa_readings_nm))

    sources = [
        # 1. 원시 거칠기 측정 반복성 (A형)
        UncertaintySource(
            name=f"{parameter} 반복 측정",
            symbol="Sa_raw",
            eval_type="A",
            value=mean_sa,  # 측정값 평균 (모델 평가용)
            repeat_data=sa_readings_nm,
            unit="nm",
        ),
        # 2. z-축 스캐너 캘리브레이션 (B형, 정규분포)
        UncertaintySource(
            name="z-축 스캐너 캘리브레이션",
            symbol="k_z",
            eval_type="B",
            value=z_calibration_factor,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=z_calibration_factor * z_calibration_uncertainty_pct / 100.0 * 2,
            coverage_factor_input=2.0,
            unit="-",
        ),
        # 3. 시료 기울기 보정 (B형, 균일분포)
        UncertaintySource(
            name="시료 기울기 보정",
            symbol="tilt",
            eval_type="B",
            value=tilt_correction,
            distribution=DistributionType.RECTANGULAR,
            half_width=tilt_uncertainty_pct / 100.0,
            unit="-",
        ),
        # 4. 백그라운드 노이즈 (B형, 정규분포)
        UncertaintySource(
            name="백그라운드 노이즈",
            symbol="bg",
            eval_type="B",
            value=background_noise_nm,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=background_uncertainty_nm * 2,
            coverage_factor_input=2.0,
            unit="nm",
        ),
    ]

    config = {
        "template_name": f"AFM 표면 거칠기 ({parameter})",
        "field": "표면 거칠기",
        "standard": "ISO 25178-2",
        "reference_material": "VLSI Standards STR10-180nm",
        "parameter": parameter,
        "scan_size_um": scan_size_um,
        "pixel_density": pixel_density,
        "measurand_name": parameter,
        "measurand_unit": "nm",
        "description": f"AFM 기반 표면 거칠기 ({parameter}) 측정 불확도 예산",
    }

    return model, sources, config


def create_afm_roughness_calculator(**kwargs) -> GUMCalculator:
    """AFM 거칠기 측정 GUM 계산기를 직접 생성하여 반환."""
    model, sources, config = create_afm_roughness_template(**kwargs)
    return GUMCalculator(
        model=model,
        sources=sources,
        measurand_name=config["measurand_name"],
        measurand_unit=config["measurand_unit"],
    )
