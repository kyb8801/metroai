"""확률분포 모듈 테스트."""

import math
import pytest
import numpy as np

from metroai.core.distributions import DistributionType, UncertaintySource


class TestTypeAEvaluation:
    """A형 불확도 평가 테스트."""

    def test_repeat_data_mean_and_std(self):
        """반복 측정 데이터로부터 평균, 표준불확도, 자유도 계산."""
        data = [10.001, 10.002, 9.999, 10.000, 10.003]
        src = UncertaintySource(
            name="반복 측정", symbol="x", eval_type="A", repeat_data=data
        )
        u, nu = src.compute()

        # 수동 계산
        n = 5
        mean_expected = np.mean(data)
        s = np.std(data, ddof=1)
        u_expected = s / math.sqrt(n)

        assert abs(src.value - mean_expected) < 1e-10
        assert abs(u - u_expected) < 1e-10
        assert nu == n - 1

    def test_type_a_minimum_data(self):
        """최소 2개 데이터로 A형 평가."""
        src = UncertaintySource(
            name="2회 측정", symbol="x", eval_type="A", repeat_data=[1.0, 2.0]
        )
        u, nu = src.compute()
        assert nu == 1
        assert u > 0

    def test_type_a_no_data_raises(self):
        """데이터 없이 A형 평가 시 에러."""
        src = UncertaintySource(name="빈 데이터", symbol="x", eval_type="A")
        with pytest.raises(ValueError):
            src.compute()


class TestTypeBEvaluation:
    """B형 불확도 평가 테스트."""

    def test_rectangular_distribution(self):
        """균일분포: u = a / √3."""
        a = 0.5
        src = UncertaintySource(
            name="분해능",
            symbol="x",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=a,
        )
        u, nu = src.compute()
        assert abs(u - a / math.sqrt(3)) < 1e-10
        assert math.isinf(nu)

    def test_triangular_distribution(self):
        """삼각분포: u = a / √6."""
        a = 1.0
        src = UncertaintySource(
            name="삼각분포 소스",
            symbol="x",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.TRIANGULAR,
            half_width=a,
        )
        u, nu = src.compute()
        assert abs(u - a / math.sqrt(6)) < 1e-10

    def test_ushape_distribution(self):
        """U자형분포: u = a / √2."""
        a = 0.3
        src = UncertaintySource(
            name="U자형 소스",
            symbol="x",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.USHAPE,
            half_width=a,
        )
        u, nu = src.compute()
        assert abs(u - a / math.sqrt(2)) < 1e-10

    def test_normal_from_expanded_uncertainty(self):
        """정규분포: U와 k로부터 u = U/k."""
        U = 0.1
        k = 2.0
        src = UncertaintySource(
            name="교정 불확도",
            symbol="x",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.NORMAL,
            expanded_uncertainty_input=U,
            coverage_factor_input=k,
        )
        u, nu = src.compute()
        assert abs(u - U / k) < 1e-10

    def test_direct_std_uncertainty(self):
        """표준불확도 직접 입력."""
        src = UncertaintySource(
            name="직접 입력",
            symbol="x",
            eval_type="B",
            value=5.0,
            std_uncertainty=0.01,
        )
        u, nu = src.compute()
        assert u == 0.01
        assert math.isinf(nu)


class TestSampling:
    """MCM용 랜덤 샘플링 테스트."""

    def test_normal_sample_statistics(self):
        """정규분포 샘플의 평균/표준편차가 설정값과 일치."""
        src = UncertaintySource(
            name="정규",
            symbol="x",
            eval_type="B",
            value=100.0,
            std_uncertainty=0.5,
            distribution=DistributionType.NORMAL,
        )
        samples = src.sample(n_samples=100_000, rng=np.random.default_rng(42))
        assert abs(np.mean(samples) - 100.0) < 0.01
        assert abs(np.std(samples) - 0.5) < 0.01

    def test_rectangular_sample_bounds(self):
        """균일분포 샘플이 [value-a, value+a] 범위 내."""
        src = UncertaintySource(
            name="균일",
            symbol="x",
            eval_type="B",
            value=0.0,
            distribution=DistributionType.RECTANGULAR,
            half_width=1.0,
        )
        samples = src.sample(n_samples=10_000, rng=np.random.default_rng(42))
        assert np.all(samples >= -1.0)
        assert np.all(samples <= 1.0)
