"""몬테카를로 시뮬레이션(MCM) 불확도 평가 엔진.

GUM Supplement 1 (JCGM 101:2008)에 따른 몬테카를로 방법으로
GUM 결과를 검증하거나 비선형 모델의 불확도를 직접 평가.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .distributions import UncertaintySource
from .model import MeasurementModel


@dataclass
class MCMResult:
    """MCM 시뮬레이션 결과."""

    # 기본 통계
    mean: float = 0.0
    std: float = 0.0  # 합성불확도에 해당
    median: float = 0.0

    # 포함구간 (Shortest Coverage Interval)
    coverage_low: float = 0.0
    coverage_high: float = 0.0
    coverage_level: float = 0.95

    # 확장불확도 (대칭 근사)
    expanded_uncertainty: float = 0.0
    coverage_factor: float = 2.0

    # 시뮬레이션 정보
    n_samples: int = 0
    samples: Optional[np.ndarray] = field(default=None, repr=False)

    # GUM 비교
    gum_uc: Optional[float] = None
    gum_agreement: Optional[bool] = None  # GUM과 MCM이 일치하는지

    def uncertainty_statement(self, name: str = "Y", unit: str = "") -> str:
        """불확도 표현 문구 (MCM 기반)."""
        unit_str = f" {unit}" if unit else ""
        conf_pct = self.coverage_level * 100
        return (
            f"{name} = {self.mean:.6g}{unit_str}"
            f", 95 % 포함구간: [{self.coverage_low:.4g}, {self.coverage_high:.4g}]{unit_str}"
            f" (MCM, M = {self.n_samples:,}회)"
        )


class MCMCalculator:
    """몬테카를로 시뮬레이션 계산기.

    사용법:
        model = MeasurementModel("L0 + dL", ["L0", "dL"])
        sources = [UncertaintySource(...), ...]
        mcm = MCMCalculator(model, sources, n_samples=100_000)
        result = mcm.simulate()
    """

    def __init__(
        self,
        model: MeasurementModel,
        sources: list[UncertaintySource],
        n_samples: int = 100_000,
        seed: Optional[int] = None,
        coverage_level: float = 0.95,
    ):
        self.model = model
        self.sources = sources
        self.n_samples = n_samples
        self.coverage_level = coverage_level
        self.rng = np.random.default_rng(seed)

    def simulate(self, gum_uc: Optional[float] = None) -> MCMResult:
        """MCM 시뮬레이션 실행.

        1. 각 입력량에서 분포에 따라 N개 샘플 생성
        2. 측정 모델을 벡터 연산으로 N회 평가
        3. 결과 분포에서 통계량 추출

        Args:
            gum_uc: GUM 합성불확도 (비교용, 선택)

        Returns:
            MCMResult 객체
        """
        # 모델 파싱 + callable 변환
        self.model.parse()
        func = self.model.get_callable()

        # 각 입력량에서 샘플 생성
        input_samples = []
        for src in self.sources:
            samples = src.sample(n_samples=self.n_samples, rng=self.rng)
            input_samples.append(samples)

        # 측정 모델 벡터 연산
        output_samples = func(*input_samples)
        output_samples = np.asarray(output_samples, dtype=np.float64)

        # 통계량 계산
        mean = float(np.mean(output_samples))
        std = float(np.std(output_samples, ddof=1))
        median = float(np.median(output_samples))

        # 최단 포함구간 (Shortest Coverage Interval)
        low, high = self._shortest_coverage_interval(
            output_samples, self.coverage_level
        )

        # 대칭 확장불확도 근사
        expanded_u = (high - low) / 2
        k = expanded_u / std if std > 0 else 2.0

        # GUM과 비교
        gum_agreement = None
        if gum_uc is not None:
            # GUM Supplement 1 기준: |u_MCM - u_GUM| / u_GUM < 임계값
            # 일반적으로 5% 이내면 일치로 판정
            relative_diff = abs(std - gum_uc) / gum_uc if gum_uc > 0 else float("inf")
            gum_agreement = relative_diff < 0.05

        return MCMResult(
            mean=mean,
            std=std,
            median=median,
            coverage_low=low,
            coverage_high=high,
            coverage_level=self.coverage_level,
            expanded_uncertainty=expanded_u,
            coverage_factor=k,
            n_samples=self.n_samples,
            samples=output_samples,
            gum_uc=gum_uc,
            gum_agreement=gum_agreement,
        )

    @staticmethod
    def _shortest_coverage_interval(
        samples: np.ndarray, level: float
    ) -> tuple[float, float]:
        """최단 포함구간(Shortest Coverage Interval) 계산.

        정렬된 샘플에서 주어진 포함확률에 해당하는 최소 폭 구간을 찾음.

        Args:
            samples: 출력 샘플 배열
            level: 포함확률 (예: 0.95)

        Returns:
            (하한, 상한) 튜플
        """
        sorted_samples = np.sort(samples)
        n = len(sorted_samples)
        n_in = int(np.ceil(level * n))

        if n_in >= n:
            return float(sorted_samples[0]), float(sorted_samples[-1])

        # 모든 가능한 구간의 폭 계산
        widths = sorted_samples[n_in:] - sorted_samples[: n - n_in]
        min_idx = int(np.argmin(widths))

        return float(sorted_samples[min_idx]), float(sorted_samples[min_idx + n_in])
