"""합성 KOLAS 감사 데이터 생성기.

실데이터 미확보 상태에서 모델 학습·평가용 합성 데이터 생성.

설계:
  - 피처: SOP 완성도, 마지막 감사 후 경과(월), 인력 회전율,
          최근 부적합 수, 인정범위 카운트, 측정방법 수
  - 라벨: 다음 정기심사 부적합 여부 (binary)
  - 생성 로직: 도메인 합리적 비선형 결합 + 노이즈
  - 정직 라벨: 모든 row 에 "synthetic_seed=N" 명기

이 데이터셋은 모델의 동작 검증 + workflow 테스트 용이며,
실세계 정확도를 추론할 수 없다는 점이 명확해야 함.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SyntheticAuditDataset:
    """합성 데이터셋 패키지."""

    X: np.ndarray  # (n, n_features)
    y: np.ndarray  # (n,) binary
    feature_names: list[str]
    seed: int
    n_samples: int
    generator_version: str = "v0.6.0-synthetic"

    def describe(self) -> dict:
        return {
            "n_samples": int(self.n_samples),
            "n_features": int(self.X.shape[1]),
            "feature_names": self.feature_names,
            "class_balance": {
                "0 (pass)": int((self.y == 0).sum()),
                "1 (nonconformity)": int((self.y == 1).sum()),
            },
            "positive_rate": float((self.y == 1).mean()),
            "seed": self.seed,
            "generator_version": self.generator_version,
            "disclaimer": (
                "Synthetic data. Real-world predictive accuracy cannot be inferred "
                "from metrics on this dataset alone."
            ),
        }


def generate_synthetic_audit_dataset(
    n_samples: int = 1000,
    seed: int = 42,
    noise_level: float = 0.15,
) -> SyntheticAuditDataset:
    """KOLAS 감사 예측용 합성 데이터셋 생성.

    Args:
        n_samples: 샘플 수
        seed: 재현성 시드
        noise_level: 0.0-1.0, 라벨 노이즈 비율 (1.0 = 완전 랜덤)

    Returns:
        SyntheticAuditDataset
    """
    rng = np.random.default_rng(seed)

    # ── Features ─────────────────────────────
    sop_completeness = rng.beta(8, 2, n_samples)  # skewed high (대부분 잘 관리)
    months_since_audit = rng.gamma(2.0, 6.0, n_samples).clip(0, 36)
    turnover = rng.beta(2, 8, n_samples).clip(0, 1)  # 대부분 낮음
    nonconformities = rng.poisson(0.5, n_samples).clip(0, 6)
    scope_count = rng.integers(1, 5, n_samples).astype(float)
    method_count = rng.integers(3, 25, n_samples).astype(float)

    X = np.column_stack([
        sop_completeness, months_since_audit, turnover,
        nonconformities, scope_count, method_count,
    ])
    feature_names = [
        "sop_completeness", "months_since_last_audit",
        "personnel_turnover", "recent_nonconformities",
        "accreditation_scope_count", "measurement_method_count",
    ]

    # ── Latent risk (도메인 합리적 비선형 결합) ─────
    latent = (
        - 2.0 * sop_completeness               # SOP 좋을수록 위험 낮음
        + 0.08 * months_since_audit            # 오래될수록 위험
        + 1.5 * turnover                       # 회전율 높을수록 위험
        + 0.40 * nonconformities               # 이력 누적
        + 0.05 * method_count / scope_count    # 방법 다양도/범위 비율
    )

    # Sigmoid → P(NC)
    p_nc = 1.0 / (1.0 + np.exp(-latent))

    # Sample binary label
    y_clean = (rng.random(n_samples) < p_nc).astype(int)

    # Inject label noise
    flip_mask = rng.random(n_samples) < noise_level
    y = np.where(flip_mask, 1 - y_clean, y_clean)

    return SyntheticAuditDataset(
        X=X,
        y=y,
        feature_names=feature_names,
        seed=seed,
        n_samples=n_samples,
    )
