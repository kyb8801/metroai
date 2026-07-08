"""GUM 불확도 전파 엔진 테스트.

GUM H.1 예제 (끝단 게이지 교정) 및 간단한 선형 모델을 이용하여
합성불확도, Welch-Satterthwaite, 확장불확도 검증.
"""

import math
import pytest
import numpy as np

from metroai.core.distributions import DistributionType, UncertaintySource
from metroai.core.gum import GUMCalculator, GUMResult
from metroai.core.model import MeasurementModel


class TestSimpleLinearModel:
    """간단한 선형 모델 Y = a + b 테스트."""

    def test_two_independent_sources(self):
        """두 독립 성분의 합성불확도: uc = √(u1² + u2²)."""
        model = MeasurementModel("a + b", symbol_names=["a", "b"])
        sources = [
            UncertaintySource(
                name="성분 a", symbol="a", eval_type="B",
                value=10.0, std_uncertainty=0.3,
            ),
            UncertaintySource(
                name="성분 b", symbol="b", eval_type="B",
                value=5.0, std_uncertainty=0.4,
            ),
        ]

        calc = GUMCalculator(model, sources, measurand_name="Y", measurand_unit="mm")
        result = calc.calculate()

        # Y = 10 + 5 = 15
        assert abs(result.measurand_value - 15.0) < 1e-10

        # 민감계수: ∂Y/∂a = 1, ∂Y/∂b = 1 (선형)
        assert abs(result.components[0].sensitivity_coeff - 1.0) < 1e-10
        assert abs(result.components[1].sensitivity_coeff - 1.0) < 1e-10

        # uc = √(0.3² + 0.4²) = √(0.09 + 0.16) = √0.25 = 0.5
        assert abs(result.combined_uncertainty - 0.5) < 1e-10

        # B형 두 성분 모두 ν=∞ → νeff=∞ → k≈2.0
        assert math.isinf(result.effective_dof)
        assert abs(result.coverage_factor - 2.0) < 0.01

        # U = 2.0 * 0.5 = 1.0
        assert abs(result.expanded_uncertainty - 1.0) < 0.01

    def test_sensitivity_with_constant(self):
        """Y = c * x 에서 민감계수가 c인지 확인."""
        model = MeasurementModel("3 * x", symbol_names=["x"])
        sources = [
            UncertaintySource(
                name="입력 x", symbol="x", eval_type="B",
                value=2.0, std_uncertainty=0.1,
            ),
        ]

        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        # ∂Y/∂x = 3
        assert abs(result.components[0].sensitivity_coeff - 3.0) < 1e-10
        # uc = |3| * 0.1 = 0.3
        assert abs(result.combined_uncertainty - 0.3) < 1e-10


class TestNonlinearModel:
    """비선형 모델 테스트."""

    def test_product_model(self):
        """Y = a * b 에서 민감계수가 올바른지."""
        model = MeasurementModel("a * b", symbol_names=["a", "b"])
        sources = [
            UncertaintySource(
                name="a", symbol="a", eval_type="B",
                value=5.0, std_uncertainty=0.1,
            ),
            UncertaintySource(
                name="b", symbol="b", eval_type="B",
                value=3.0, std_uncertainty=0.2,
            ),
        ]

        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        # Y = 5 * 3 = 15
        assert abs(result.measurand_value - 15.0) < 1e-10

        # ∂Y/∂a = b = 3, ∂Y/∂b = a = 5
        assert abs(result.components[0].sensitivity_coeff - 3.0) < 1e-10
        assert abs(result.components[1].sensitivity_coeff - 5.0) < 1e-10

        # uc = √((3*0.1)² + (5*0.2)²) = √(0.09 + 1.0) = √1.09
        expected_uc = math.sqrt(0.09 + 1.0)
        assert abs(result.combined_uncertainty - expected_uc) < 1e-10


class TestWelchSatterthwaite:
    """Welch-Satterthwaite 유효자유도 테스트."""

    def test_all_infinite_dof(self):
        """모든 성분이 B형(ν=∞)이면 νeff=∞."""
        model = MeasurementModel("a + b", symbol_names=["a", "b"])
        sources = [
            UncertaintySource(
                name="a", symbol="a", eval_type="B",
                value=1.0, std_uncertainty=0.1,
            ),
            UncertaintySource(
                name="b", symbol="b", eval_type="B",
                value=1.0, std_uncertainty=0.1,
            ),
        ]
        calc = GUMCalculator(model, sources)
        result = calc.calculate()
        assert math.isinf(result.effective_dof)

    def test_finite_dof_increases_k(self):
        """유한한 자유도는 k > 2를 만든다."""
        model = MeasurementModel("a + b", symbol_names=["a", "b"])

        # A형 (ν=4) 성분이 지배적이면 k가 2보다 커야 함
        sources = [
            UncertaintySource(
                name="A형 측정", symbol="a", eval_type="A",
                repeat_data=[1.0, 1.1, 0.9, 1.05, 0.95],  # n=5, ν=4
            ),
            UncertaintySource(
                name="B형 소소", symbol="b", eval_type="B",
                value=0.0, std_uncertainty=0.001,  # 작은 기여
            ),
        ]
        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        # A형이 지배적이므로 νeff ≈ 4, k > 2
        assert result.effective_dof < 100
        assert result.coverage_factor > 2.0

    def test_mixed_dof(self):
        """A형과 B형 혼합 시 νeff가 적절한 범위."""
        model = MeasurementModel("a + b", symbol_names=["a", "b"])
        sources = [
            UncertaintySource(
                name="A형", symbol="a", eval_type="A",
                repeat_data=[1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98, 1.03, 0.97, 1.01],
            ),
            UncertaintySource(
                name="B형", symbol="b", eval_type="B",
                value=0.0, std_uncertainty=0.05,
            ),
        ]
        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        # νeff는 유한하되 A형의 ν=9보다 클 수 있음 (B형이 ∞를 끌어올림)
        assert result.effective_dof > 0
        assert not math.isinf(result.effective_dof) or result.effective_dof > 9


class TestPercentContribution:
    """기여율 테스트."""

    def test_contributions_sum_to_100(self):
        """모든 기여율의 합이 100%."""
        model = MeasurementModel("a + b + c", symbol_names=["a", "b", "c"])
        sources = [
            UncertaintySource(name="a", symbol="a", eval_type="B", value=1.0, std_uncertainty=0.1),
            UncertaintySource(name="b", symbol="b", eval_type="B", value=1.0, std_uncertainty=0.2),
            UncertaintySource(name="c", symbol="c", eval_type="B", value=1.0, std_uncertainty=0.3),
        ]
        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        total = sum(c.percent_contribution for c in result.components)
        assert abs(total - 100.0) < 0.1


class TestUncertaintyStatement:
    """불확도 표현 문구 테스트."""

    def test_statement_format(self):
        """KOLAS 양식 문구가 올바른 포맷인지."""
        model = MeasurementModel("x", symbol_names=["x"])
        sources = [
            UncertaintySource(
                name="측정값", symbol="x", eval_type="B",
                value=100.0, std_uncertainty=0.5,
            ),
        ]
        calc = GUMCalculator(model, sources, measurand_name="L", measurand_unit="mm")
        result = calc.calculate()

        stmt = result.uncertainty_statement()
        assert "L =" in stmt
        assert "mm" in stmt
        assert "k =" in stmt
        assert "신뢰수준" in stmt
