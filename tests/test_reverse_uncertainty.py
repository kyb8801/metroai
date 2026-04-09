"""불확도 역설계 엔진 테스트."""

import math
import pytest

from metroai.core.reverse_uncertainty import (
    ReverseUncertaintyEngine,
    ReverseResult,
    ComponentBudget,
)


@pytest.fixture
def simple_engine():
    """단순 덧셈 모델 (ci=1 for all)."""
    return ReverseUncertaintyEngine(
        model_expression="a + b + c",
        symbol_names=["a", "b", "c"],
        sensitivity_coefficients={"a": 1.0, "b": 1.0, "c": 1.0},
        measurand_name="Y",
        measurand_unit="mm",
    )


@pytest.fixture
def gauge_block_engine():
    """블록게이지 모델 (비대칭 민감계수)."""
    return ReverseUncertaintyEngine(
        model_expression="dL + d_std + alpha_diff * Ls * dT + d_res",
        symbol_names=["dL", "d_std", "alpha_diff", "dT", "d_res"],
        sensitivity_coefficients={
            "dL": 1.0, "d_std": 1.0, "alpha_diff": 50000.0,
            "dT": 1e-6, "d_res": 1.0,
        },
        measurand_unit="µm",
    )


class TestReverseEqual:
    """균등 배분 역설계 테스트."""

    def test_basic_allocation(self, simple_engine):
        result = simple_engine.reverse_equal(target_U=0.1, k=2.0)
        assert result.target_combined_uncertainty == pytest.approx(0.05, rel=1e-10)
        assert len(result.components) == 3
        # 균등 배분: 각 u_max = uc / sqrt(3)
        for comp in result.components:
            assert comp.max_allowed_std_uncertainty == pytest.approx(
                0.05 / math.sqrt(3), rel=1e-10
            )

    def test_forward_backward_consistency(self, simple_engine):
        """역산된 u로 순방향 계산하면 정확히 uc_target이 나와야 한다."""
        result = simple_engine.reverse_equal(target_U=0.2, k=2.0)
        uc_forward = math.sqrt(sum(
            (c.sensitivity_coeff * c.max_allowed_std_uncertainty) ** 2
            for c in result.components
        ))
        assert uc_forward == pytest.approx(result.target_combined_uncertainty, rel=1e-10)

    def test_asymmetric_sensitivities(self, gauge_block_engine):
        """비대칭 민감계수에서도 정합성 유지."""
        result = gauge_block_engine.reverse_equal(target_U=0.1, k=2.0)
        uc_forward = math.sqrt(sum(
            (c.sensitivity_coeff * c.max_allowed_std_uncertainty) ** 2
            for c in result.components
        ))
        assert uc_forward == pytest.approx(0.05, rel=1e-10)

    def test_feasibility_check(self, simple_engine):
        """현재값이 허용범위 초과하면 is_feasible=False."""
        current = {"a": 0.1, "b": 0.001, "c": 0.001}
        result = simple_engine.reverse_equal(
            target_U=0.1, k=2.0, current_uncertainties=current
        )
        # a의 현재값 0.1은 허용값(~0.0289)보다 큼
        comp_a = [c for c in result.components if c.symbol == "a"][0]
        assert comp_a.is_feasible is False
        assert result.overall_feasible is False

    def test_all_feasible(self, simple_engine):
        """현재값이 허용범위 내면 overall_feasible=True."""
        current = {"a": 0.001, "b": 0.001, "c": 0.001}
        result = simple_engine.reverse_equal(
            target_U=0.1, k=2.0, current_uncertainties=current
        )
        assert result.overall_feasible is True

    def test_contribution_ratio_equal(self, simple_engine):
        """균등 배분이면 모든 성분 비율이 동일."""
        result = simple_engine.reverse_equal(target_U=0.1, k=2.0)
        for comp in result.components:
            assert comp.contribution_ratio == pytest.approx(100.0 / 3, rel=1e-5)

    def test_half_width_rect_conversion(self, simple_engine):
        """균일분포 반폭 환산: a = u * sqrt(3)."""
        result = simple_engine.reverse_equal(target_U=0.1, k=2.0)
        for comp in result.components:
            assert comp.max_allowed_half_width_rect == pytest.approx(
                comp.max_allowed_std_uncertainty * math.sqrt(3), rel=1e-10
            )


class TestReverseWeighted:
    """가중 배분 역설계 테스트."""

    def test_weighted_preserves_total(self, simple_engine):
        """가중 배분도 순방향 합산하면 uc_target과 일치."""
        current = {"a": 0.03, "b": 0.01, "c": 0.02}
        result = simple_engine.reverse_weighted(
            target_U=0.1, k=2.0, current_uncertainties=current
        )
        uc_forward = math.sqrt(sum(
            (c.sensitivity_coeff * c.max_allowed_std_uncertainty) ** 2
            for c in result.components
        ))
        assert uc_forward == pytest.approx(0.05, rel=1e-10)

    def test_higher_contribution_gets_more_budget(self, simple_engine):
        """기여도가 큰 성분이 더 많은 예산을 받는다."""
        current = {"a": 0.05, "b": 0.01, "c": 0.01}
        result = simple_engine.reverse_weighted(
            target_U=0.1, k=2.0, current_uncertainties=current
        )
        comp_a = [c for c in result.components if c.symbol == "a"][0]
        comp_b = [c for c in result.components if c.symbol == "b"][0]
        # a의 기여도가 높으므로 더 많은 예산
        assert comp_a.max_allowed_std_uncertainty > comp_b.max_allowed_std_uncertainty


class TestReverseSingleComponent:
    """단일 성분 역산 테스트."""

    def test_single_component_basic(self, simple_engine):
        """한 성분만 역산 — 나머지 고정."""
        fixed = {"b": 0.01, "c": 0.01}
        result = simple_engine.reverse_single_component(
            target_U=0.1, target_symbol="a",
            fixed_uncertainties=fixed, k=2.0,
        )
        # uc² = 0.05² = 0.0025
        # fixed_var = (1*0.01)² + (1*0.01)² = 0.0002
        # target_var = 0.0025 - 0.0002 = 0.0023
        # u_max_a = sqrt(0.0023) / 1 = 0.04796
        comp_a = [c for c in result.components if c.symbol == "a"][0]
        expected = math.sqrt(0.05**2 - 0.01**2 - 0.01**2)
        assert comp_a.max_allowed_std_uncertainty == pytest.approx(expected, rel=1e-10)
        assert result.overall_feasible is True

    def test_impossible_scenario(self, simple_engine):
        """고정 성분만으로 목표 초과 — 불가능."""
        fixed = {"b": 0.04, "c": 0.04}
        result = simple_engine.reverse_single_component(
            target_U=0.1, target_symbol="a",
            fixed_uncertainties=fixed, k=2.0,
        )
        # fixed_var = 0.04² + 0.04² = 0.0032 > uc² = 0.0025
        assert result.overall_feasible is False
        comp_a = [c for c in result.components if c.symbol == "a"][0]
        assert comp_a.max_allowed_std_uncertainty == 0.0


class TestResultMetadata:
    """결과 메타데이터 테스트."""

    def test_summary_string(self, simple_engine):
        result = simple_engine.reverse_equal(target_U=0.1, k=2.0)
        summary = result.summary()
        assert "0.1" in summary
        assert "mm" in summary

    def test_allocation_method_recorded(self, simple_engine):
        result = simple_engine.reverse_equal(target_U=0.1, k=2.0)
        assert result.allocation_method == "equal"

    def test_expanded_U_conversion(self, simple_engine):
        """U_max = k * u_max."""
        result = simple_engine.reverse_equal(target_U=0.1, k=2.0)
        for comp in result.components:
            assert comp.max_allowed_expanded_U == pytest.approx(
                2.0 * comp.max_allowed_std_uncertainty, rel=1e-10
            )
