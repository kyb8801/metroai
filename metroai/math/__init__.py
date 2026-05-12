"""수학 유틸리티 모듈 — v0.6.0 신규.

박수연(MetroAI advisor) 통합.

서브 모듈:
  - sobol_qmc: Quasi-Monte Carlo (Sobol sequence) — MCM 분산 감소
"""

from .sobol_qmc import (
    SobolQMC,
    qmc_uncertainty_propagation,
    sample_from_distribution_qmc,
)

__all__ = [
    "SobolQMC",
    "qmc_uncertainty_propagation",
    "sample_from_distribution_qmc",
]
