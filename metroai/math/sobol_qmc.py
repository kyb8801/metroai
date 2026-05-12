"""Sobol Quasi-Monte Carlo 모듈.

박수연(MetroAI advisor) 통합 — v0.6.0 신규.

MCM (ISO/IEC Guide 98-3/Suppl. 1) 의 표준 Monte Carlo 는 의사난수 기반.
QMC (Sobol low-discrepancy sequence) 를 사용하면 동일 표본 수로
약 O(1/N) 수렴 (표준 MC 는 O(1/√N)) — 측정 불확도 평가에서
빠른 수렴과 결정론적 결과를 얻을 수 있음.

수학:
  - Sobol sequence: [0,1)^d 균등분포 quasi-random 시퀀스
  - Inverse CDF transform 으로 임의 분포 샘플링
  - Owen scrambling 옵션 (분산 감소 + 신뢰구간 추정)

표준 참조:
  - ISO/IEC Guide 98-3/Suppl. 1 (MCM)
  - JCGM 100:2008 §G.4
  - Owen, A. (1997). Scrambled net variance for integrals of smooth functions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from scipy.stats import qmc as scipy_qmc


@dataclass
class SobolQMCResult:
    """QMC 불확도 전파 결과."""

    samples: np.ndarray  # shape (N, dim_inputs)
    outputs: np.ndarray  # shape (N,)
    mean: float
    std: float
    median: float
    coverage_interval: tuple[float, float]  # (low, high)
    coverage_probability: float  # 0.0-1.0 (e.g., 0.9545)
    n_samples: int
    is_power_of_two: bool


class SobolQMC:
    """Sobol Quasi-Monte Carlo sampler.

    사용:
        qmc = SobolQMC(dim=3, scramble=True, seed=42)
        u01 = qmc.sample(n=2**12)  # (4096, 3) in [0, 1)
    """

    def __init__(
        self,
        dim: int,
        scramble: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        if dim < 1:
            raise ValueError(f"dim must be >= 1, got {dim}")
        self.dim = dim
        self.scramble = scramble
        self.seed = seed
        self._sampler = scipy_qmc.Sobol(d=dim, scramble=scramble, seed=seed)

    def sample(self, n: int) -> np.ndarray:
        """[0, 1)^d 에서 n 개 Sobol 점 생성.

        Notes:
            n 이 2의 거듭제곱일 때 quasi-random property 가 가장 잘 보존됨.
            scipy 는 UserWarning 을 발생시키므로 비추천 시 silence 한다.
        """
        if n <= 0:
            raise ValueError(f"n must be > 0, got {n}")
        # Sobol 은 next_n 단위로 best — power of 2 권장
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            return self._sampler.random(n)

    def reset(self) -> None:
        """샘플러 상태 초기화."""
        self._sampler = scipy_qmc.Sobol(
            d=self.dim, scramble=self.scramble, seed=self.seed
        )


def sample_from_distribution_qmc(
    u01: np.ndarray,
    dist_type: str,
    value: float,
    std_or_half_width: float,
) -> np.ndarray:
    """[0,1) 균등 샘플 → 임의 분포 샘플 (inverse CDF transform).

    Args:
        u01: shape (N,) in [0, 1)
        dist_type: 'normal' | 'rectangular' | 'triangular' | 'u_shape'
        value: 분포 중심
        std_or_half_width:
            - normal: standard uncertainty u
            - rectangular: half-width a (u = a/√3)
            - triangular: half-width a (u = a/√6)
            - u_shape: half-width a (u = a/√2)

    Returns:
        분포에서 추출한 샘플 (shape N).
    """
    from scipy.stats import norm

    u = np.clip(u01, 1e-12, 1.0 - 1e-12)  # 경계 회피

    if dist_type == "normal":
        # u01 → Φ^-1
        return value + std_or_half_width * norm.ppf(u)
    elif dist_type == "rectangular":
        # u01 → linear in [value - a, value + a]
        return value + (2 * u - 1) * std_or_half_width
    elif dist_type == "triangular":
        # u01 → triangular [value - a, value, value + a]
        a = std_or_half_width
        out = np.where(
            u < 0.5,
            value - a + a * np.sqrt(2 * u),
            value + a - a * np.sqrt(2 * (1 - u)),
        )
        return out
    elif dist_type == "u_shape":
        # arcsine distribution on [value - a, value + a]
        a = std_or_half_width
        return value + a * np.cos(np.pi * (1 - u))
    else:
        raise ValueError(f"Unsupported distribution for QMC: {dist_type}")


def qmc_uncertainty_propagation(
    f: Callable[..., float],
    input_specs: list[dict],
    n_samples: int = 2 ** 14,
    coverage_probability: float = 0.9545,
    scramble: bool = True,
    seed: Optional[int] = 42,
) -> SobolQMCResult:
    """QMC 기반 측정 불확도 전파 (MCM 대안).

    Args:
        f: 측정 모델 함수 — f(**inputs) → 출력값
        input_specs: 각 입력에 대한 분포 정보 dict 리스트:
            [{"name": "L", "dist": "normal", "value": 100.0, "std": 0.05}, ...]
        n_samples: 샘플 수 (2의 거듭제곱 권장)
        coverage_probability: 신뢰수준 (기본 95.45%)
        scramble: Owen scrambling 사용 여부
        seed: 재현성용 시드

    Returns:
        SobolQMCResult — 평균·표준편차·신뢰구간 등.
    """
    dim = len(input_specs)
    if dim == 0:
        raise ValueError("input_specs가 비어 있습니다.")

    qmc = SobolQMC(dim=dim, scramble=scramble, seed=seed)
    u01 = qmc.sample(n_samples)  # (N, dim)

    # 각 차원별 분포 변환
    samples = np.zeros_like(u01)
    for i, spec in enumerate(input_specs):
        dist = spec.get("dist", "normal")
        val = float(spec["value"])
        if dist == "normal":
            sw = float(spec["std"])
        else:
            sw = float(spec.get("half_width", spec.get("std", 0)))
        samples[:, i] = sample_from_distribution_qmc(u01[:, i], dist, val, sw)

    # 함수 평가
    outputs = np.array([
        f(**{spec["name"]: samples[k, i] for i, spec in enumerate(input_specs)})
        for k in range(n_samples)
    ])

    # 통계
    mean = float(np.mean(outputs))
    std = float(np.std(outputs, ddof=1))
    median = float(np.median(outputs))

    # 신뢰구간 (양측 분위수)
    alpha = (1 - coverage_probability) / 2
    low = float(np.quantile(outputs, alpha))
    high = float(np.quantile(outputs, 1 - alpha))

    is_pow2 = (n_samples & (n_samples - 1) == 0) and n_samples > 0

    return SobolQMCResult(
        samples=samples,
        outputs=outputs,
        mean=mean,
        std=std,
        median=median,
        coverage_interval=(low, high),
        coverage_probability=coverage_probability,
        n_samples=n_samples,
        is_power_of_two=is_pow2,
    )
