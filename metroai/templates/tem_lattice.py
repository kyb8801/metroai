"""TEM 격자상수 측정 불확도 템플릿.

박수연(MetroAI advisor) 통합 — v0.6.0 신규.

투과전자현미경(TEM)을 이용한 단결정 격자상수(d-spacing) 측정 불확도 예산.
ISO 18516, ISO/IEC 17025 호환.

측정 모델: d = lambda / (2 * sin(theta))
  - lambda: 전자선 파장 (가속전압 V_acc로 결정)
  - theta: 회절각 (Bragg 각)

또는 직접 영상(HRTEM) 격자 간격 측정:
  d = L / N
  - L: 영상 내 측정 거리 (캘리브레이션된 nm 단위)
  - N: 격자 줄 수

기준 시료: Si (111) d-spacing = 0.31356 nm (CRM)
           Si (220) d-spacing = 0.19200 nm
           격자상수 a₀(Si) = 0.54307 nm (NIST SRM 640)
"""

from __future__ import annotations

import numpy as np

from ..core.distributions import DistributionType, UncertaintySource
from ..core.gum import GUMCalculator
from ..core.model import MeasurementModel


def create_tem_lattice_template(
    nominal_d_spacing_nm: float = 0.31356,  # Si (111)
    image_distance_readings_nm: list[float] | None = None,
    pixel_calibration_nm_per_px: float = 0.005,
    pixel_calibration_uncertainty_pct: float = 1.0,
    n_lattice_rows: int = 10,
    n_uncertainty: float = 0.05,  # 격자 줄 카운팅 불확실성
    drift_correction_nm: float = 0.0,
    drift_uncertainty_nm: float = 0.002,
    tilt_correction_factor: float = 1.0,
    tilt_uncertainty_pct: float = 0.5,
) -> tuple[MeasurementModel, list[UncertaintySource], dict]:
    """TEM 격자상수 측정 불확도 예산 템플릿.

    Args:
        nominal_d_spacing_nm: 공칭 d-spacing (nm). 기본값 Si (111) = 0.31356 nm
        image_distance_readings_nm: HRTEM 영상에서 측정한 격자 간격 반복값 (nm)
        pixel_calibration_nm_per_px: 픽셀 캘리브레이션 (nm/pixel)
        pixel_calibration_uncertainty_pct: 픽셀 캘리브레이션 불확도 (% relative)
        n_lattice_rows: 측정한 격자 줄 수
        n_uncertainty: 격자 줄 카운팅 불확실성
        drift_correction_nm: 시료 드리프트 보정값 (nm)
        drift_uncertainty_nm: 드리프트 불확도 (nm)
        tilt_correction_factor: 시료 기울기 보정 인자
        tilt_uncertainty_pct: 기울기 불확도 (% relative)

    Returns:
        (model, sources, config) 튜플
    """
    if image_distance_readings_nm is None:
        # Si (111) 10줄 간격 기본값 ≈ 3.1356 nm
        image_distance_readings_nm = [
            3.1340, 3.1372, 3.1358, 3.1349, 3.1361,
            3.1355, 3.1370, 3.1348, 3.1359, 3.1352,
        ]

    # 측정 모델: d = (L_measured + drift) * tilt_factor / N
    model = MeasurementModel(
        expression_str="(L_meas + drift) * tilt / N_rows",
        symbol_names=["L_meas", "drift", "tilt", "N_rows"],
    )

    mean_L = float(np.mean(image_distance_readings_nm))

    sources = [
        # 1. 영상 거리 측정 반복성 (A형)
        UncertaintySource(
            name="HRTEM 격자 거리 반복 측정",
            symbol="L_meas",
            eval_type="A",
            value=mean_L,  # 측정값 평균 (모델 평가용)
            repeat_data=image_distance_readings_nm,
            unit="nm",
        ),
        # 2. 시료 드리프트 보정 (B형, 정규분포)
        UncertaintySource(
            name="시료 드리프트",
            symbol="drift",
            eval_type="B",
            value=drift_correction_nm,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=drift_uncertainty_nm * 2,
            coverage_factor_input=2.0,
            unit="nm",
        ),
        # 3. 시료 기울기 보정 (B형, 균일분포)
        UncertaintySource(
            name="시료 기울기 보정",
            symbol="tilt",
            eval_type="B",
            value=tilt_correction_factor,
            distribution=DistributionType.RECTANGULAR,
            half_width=tilt_correction_factor * tilt_uncertainty_pct / 100.0,
            unit="-",
        ),
        # 4. 격자 줄 수 (상수, 카운팅 불확실성)
        UncertaintySource(
            name="격자 줄 수",
            symbol="N_rows",
            eval_type="B",
            value=float(n_lattice_rows),
            distribution=DistributionType.RECTANGULAR,
            half_width=n_uncertainty,
            unit="-",
        ),
    ]

    config = {
        "template_name": "TEM 격자상수 측정",
        "field": "나노스케일 길이",
        "standard": "ISO 18516",
        "reference_material": "NIST SRM 640 (Si)",
        "nominal_d_spacing_nm": nominal_d_spacing_nm,
        "measurand_name": "d",
        "measurand_unit": "nm",
        "description": "HRTEM 영상 기반 단결정 격자상수 측정 불확도 예산",
        "pixel_calibration": f"{pixel_calibration_nm_per_px} nm/px ± {pixel_calibration_uncertainty_pct}%",
    }

    return model, sources, config


def create_tem_lattice_calculator(**kwargs) -> GUMCalculator:
    """TEM 격자상수 측정 GUM 계산기를 직접 생성하여 반환."""
    model, sources, config = create_tem_lattice_template(**kwargs)
    return GUMCalculator(
        model=model,
        sources=sources,
        measurand_name=config["measurand_name"],
        measurand_unit=config["measurand_unit"],
    )
