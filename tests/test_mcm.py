"""MCM (몬테카를로 시뮬레이션) 테스트."""

import math
import numpy as np
import pytest

from metroai.core.distributions import DistributionType, UncertaintySource
from metroai.core.gum import GUMCalculator
from metroai.core.mcm import MCMCalculator
from metroai.core.model import MeasurementModel


class TestMCMBasic:
    """기본 MCM 테스트."""

    def test_linear_model_agrees_with_gum(self):
        """선형 모델에서 MCM과 GUM이 일치."""
        model = MeasurementModel("a + b", symbol_names=["a", "b"])
        sources = [
            UncertaintySource(
                name="a", symbol="a", eval_type="B",
                value=10.0, std_uncertainty=0.3,
                distribution=DistributionType.NORMAL,
            ),
            UncertaintySource(
                name="b", symbol="b", eval_type="B",
                value=5.0, std_uncertainty=0.4,
                distribution=DistributionType.NORMAL,
            ),
        ]

        # GUM 계산
        gum_calc = GUMCalculator(model, sources)
        gum_result = gum_calc.calculate()

        # MCM 계산
        mcm_calc = MCMCalculator(model, sources, n_samples=200_000, seed=42)
        mcm_result = mcm_calc.simulate(gum_uc=gum_result.combined_uncertainty)

        # 평균이 일치 (1% 이내)
        assert abs(mcm_result.mean - gum_result.measurand_value) / abs(gum_result.measurand_value) < 0.01

        # 표준불확도가 일치 (5% 이내)
        assert abs(mcm_result.std - gum_result.combined_uncertainty) / gum_result.combined_uncertainty < 0.05

        # GUM 일치 판정
        assert mcm_result.gum_agreement is True

    def test_coverage_interval(self):
        """포함구간이 합리적인 범위."""
        model = MeasurementModel("x", symbol_names=["x"])
        sources = [
            UncertaintySource(
                name="x", symbol="x", eval_type="B",
                value=100.0, std_uncertainty=1.0,
                distribution=DistributionType.NORMAL,
            ),
        ]

        mcm = MCMCalculator(model, sources, n_samples=100_000, seed=42)
        result = mcm.simulate()

        # 95% 포함구간: 약 [98, 102]
        assert result.coverage_low < 100.0
        assert result.coverage_high > 100.0
        interval_width = result.coverage_high - result.coverage_low
        # 정규분포 95% 구간 ≈ 2*1.96*1.0 ≈ 3.92
        assert 3.0 < interval_width < 5.0


class TestMCMNonlinear:
    """비선형 모델에서 MCM 테스트."""

    def test_product_model(self):
        """Y = a * b 비선형 모델에서 MCM이 합리적."""
        model = MeasurementModel("a * b", symbol_names=["a", "b"])
        sources = [
            UncertaintySource(
                name="a", symbol="a", eval_type="B",
                value=5.0, std_uncertainty=0.5,
                distribution=DistributionType.NORMAL,
            ),
            UncertaintySource(
                name="b", symbol="b", eval_type="B",
                value=3.0, std_uncertainty=0.3,
                distribution=DistributionType.NORMAL,
            ),
        ]

        mcm = MCMCalculator(model, sources, n_samples=200_000, seed=42)
        result = mcm.simulate()

        # 평균 ≈ 15
        assert abs(result.mean - 15.0) < 0.5
        # 불확도 > 0
        assert result.std > 0
        # 포함구간이 15을 포함
        assert result.coverage_low < 15.0 < result.coverage_high


class TestMCMStatement:
    """MCM 불확도 표현 테스트."""

    def test_statement_contains_mcm_info(self):
        """MCM 문구에 시뮬레이션 정보가 포함."""
        model = MeasurementModel("x", symbol_names=["x"])
        sources = [
            UncertaintySource(
                name="x", symbol="x", eval_type="B",
                value=50.0, std_uncertainty=0.5,
                distribution=DistributionType.NORMAL,
            ),
        ]
        mcm = MCMCalculator(model, sources, n_samples=10_000, seed=42)
        result = mcm.simulate()

        stmt = result.uncertainty_statement(name="L", unit="mm")
        assert "MCM" in stmt
        assert "포함구간" in stmt
        assert "10,000" in stmt
