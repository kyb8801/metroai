"""확률분포 처리 모듈.

KOLAS-G-002에서 정의하는 B형 불확도 평가용 분포들을 구현.
각 분포는 표준불확도 u(x)와 자유도 ν를 반환.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np


class DistributionType(Enum):
    """지원하는 확률분포 유형."""

    NORMAL = "정규분포"
    RECTANGULAR = "균일분포(사각)"
    TRIANGULAR = "삼각분포"
    USHAPE = "U자형분포"
    ARCSINE = "아크사인분포"


@dataclass
class UncertaintySource:
    """불확도 성분 하나를 나타내는 데이터 클래스.

    Attributes:
        name: 불확도 성분 이름 (예: "표준기 교정 불확도")
        symbol: 수학 기호 (예: "x1")
        eval_type: 평가 유형 ("A" 또는 "B")
        value: 입력량의 추정값
        std_uncertainty: 표준불확도 u(xi) — 직접 입력 또는 자동 계산
        distribution: B형 평가 시 가정 분포
        half_width: B형 평가 시 반폭 a (예: ±0.5 → a=0.5)
        coverage_factor_input: B형 정규분포 시 입력된 포함인자 k
        expanded_uncertainty_input: B형 정규분포 시 입력된 확장불확도 U
        dof: 자유도 ν (A형: n-1, B형: ∞ 또는 추정값)
        repeat_data: A형 평가용 반복 측정 데이터
        unit: 단위
    """

    name: str
    symbol: str
    eval_type: str  # "A" 또는 "B"
    value: float = 0.0
    std_uncertainty: Optional[float] = None
    distribution: DistributionType = DistributionType.NORMAL
    half_width: Optional[float] = None
    coverage_factor_input: Optional[float] = None
    expanded_uncertainty_input: Optional[float] = None
    dof: Optional[float] = None
    repeat_data: Optional[list[float]] = None
    unit: str = ""

    def compute(self) -> tuple[float, float]:
        """표준불확도 u(xi)와 자유도 ν를 계산하여 반환.

        Returns:
            (std_uncertainty, degrees_of_freedom) 튜플
        """
        if self.eval_type == "A":
            return self._compute_type_a()
        elif self.eval_type == "B":
            return self._compute_type_b()
        else:
            raise ValueError(f"평가 유형은 'A' 또는 'B'여야 합니다: {self.eval_type}")

    def _compute_type_a(self) -> tuple[float, float]:
        """A형 평가: 반복 측정 데이터로부터 표준불확도 계산.

        u(x) = s(x̄) = s(x) / √n
        ν = n - 1
        """
        if self.repeat_data is not None and len(self.repeat_data) >= 2:
            data = np.array(self.repeat_data)
            n = len(data)
            s = float(np.std(data, ddof=1))  # 표본표준편차
            u = s / math.sqrt(n)  # 평균의 표준불확도
            nu = n - 1  # 자유도
            self.std_uncertainty = u
            self.dof = float(nu)
            self.value = float(np.mean(data))
            return u, float(nu)
        elif self.std_uncertainty is not None:
            # 이미 계산된 표준불확도가 주어진 경우
            if self.dof is None:
                self.dof = float("inf")
            return self.std_uncertainty, self.dof
        else:
            raise ValueError(
                f"A형 평가 '{self.name}': 반복 측정 데이터 또는 표준불확도가 필요합니다."
            )

    def _compute_type_b(self) -> tuple[float, float]:
        """B형 평가: 분포 가정으로부터 표준불확도 계산.

        정규분포:   u = U / k  (U: 확장불확도, k: 포함인자)
        균일분포:   u = a / √3
        삼각분포:   u = a / √6
        U자형분포:  u = a / √2
        """
        if self.std_uncertainty is not None:
            # 표준불확도가 직접 주어진 경우
            if self.dof is None:
                self.dof = float("inf")
            return self.std_uncertainty, self.dof

        if self.distribution == DistributionType.NORMAL:
            return self._compute_b_normal()
        elif self.distribution == DistributionType.RECTANGULAR:
            return self._compute_b_rectangular()
        elif self.distribution == DistributionType.TRIANGULAR:
            return self._compute_b_triangular()
        elif self.distribution in (DistributionType.USHAPE, DistributionType.ARCSINE):
            return self._compute_b_ushape()
        else:
            raise ValueError(f"지원하지 않는 분포: {self.distribution}")

    def _compute_b_normal(self) -> tuple[float, float]:
        """B형 정규분포: U = k * u → u = U / k."""
        if self.expanded_uncertainty_input is not None and self.coverage_factor_input is not None:
            k = self.coverage_factor_input
            U = self.expanded_uncertainty_input
            u = U / k
        elif self.half_width is not None:
            # 반폭이 주어진 경우 (95% 신뢰구간 가정, k=2)
            k = self.coverage_factor_input if self.coverage_factor_input else 2.0
            u = self.half_width / k
        else:
            raise ValueError(
                f"B형 정규분포 '{self.name}': 확장불확도(U)와 포함인자(k), "
                f"또는 반폭(a)이 필요합니다."
            )
        self.std_uncertainty = u
        if self.dof is None:
            self.dof = float("inf")
        return u, self.dof

    def _compute_b_rectangular(self) -> tuple[float, float]:
        """B형 균일분포: u = a / √3."""
        if self.half_width is None:
            raise ValueError(f"B형 균일분포 '{self.name}': 반폭(a)이 필요합니다.")
        u = self.half_width / math.sqrt(3)
        self.std_uncertainty = u
        if self.dof is None:
            self.dof = float("inf")
        return u, self.dof

    def _compute_b_triangular(self) -> tuple[float, float]:
        """B형 삼각분포: u = a / √6."""
        if self.half_width is None:
            raise ValueError(f"B형 삼각분포 '{self.name}': 반폭(a)이 필요합니다.")
        u = self.half_width / math.sqrt(6)
        self.std_uncertainty = u
        if self.dof is None:
            self.dof = float("inf")
        return u, self.dof

    def _compute_b_ushape(self) -> tuple[float, float]:
        """B형 U자형(아크사인)분포: u = a / √2."""
        if self.half_width is None:
            raise ValueError(f"B형 U자형분포 '{self.name}': 반폭(a)이 필요합니다.")
        u = self.half_width / math.sqrt(2)
        self.std_uncertainty = u
        if self.dof is None:
            self.dof = float("inf")
        return u, self.dof

    def sample(self, n_samples: int = 10000, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """MCM용 랜덤 샘플 생성.

        Args:
            n_samples: 생성할 샘플 수
            rng: numpy 난수 생성기 (재현성을 위해)

        Returns:
            n_samples 크기의 numpy 배열
        """
        if rng is None:
            rng = np.random.default_rng()

        u, _ = self.compute()

        if self.eval_type == "A":
            # A형: 정규분포 가정
            return rng.normal(self.value, u, n_samples)

        # B형: 분포별 샘플링
        if self.distribution == DistributionType.NORMAL:
            return rng.normal(self.value, u, n_samples)
        elif self.distribution == DistributionType.RECTANGULAR:
            a = self.half_width if self.half_width else u * math.sqrt(3)
            return rng.uniform(self.value - a, self.value + a, n_samples)
        elif self.distribution == DistributionType.TRIANGULAR:
            a = self.half_width if self.half_width else u * math.sqrt(6)
            return rng.triangular(self.value - a, self.value, self.value + a, n_samples)
        elif self.distribution in (DistributionType.USHAPE, DistributionType.ARCSINE):
            a = self.half_width if self.half_width else u * math.sqrt(2)
            # 아크사인 분포: Beta(0.5, 0.5)을 스케일링
            beta_samples = rng.beta(0.5, 0.5, n_samples)
            return self.value - a + 2 * a * beta_samples
        else:
            return rng.normal(self.value, u, n_samples)
