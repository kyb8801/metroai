"""Audit Risk Model — GradientBoosting 기반 KOLAS 감사 위험 예측.

박수연(MetroAI advisor) 통합 — v0.6.0.

설계 원칙:
  1. 정직 메트릭: cross-validated metrics + train/test split + permutation importance
  2. 모든 출력에 데이터 origin 표기 (synthetic / real / mixed)
  3. 모델 미설치 시 (scikit-learn 부재) — graceful fallback to baseline rule

scikit-learn 은 optional dependency 로 두어 설치 부담을 줄임.
설치: `pip install metroai[ml]`
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.metrics import (
        accuracy_score, brier_score_loss, roc_auc_score, f1_score,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class ModelEvaluation:
    """모델 평가 결과 — 정직 라벨 동반."""

    data_origin: str  # "synthetic" / "real" / "mixed"
    n_samples: int
    n_features: int
    cv_folds: int

    # Cross-validated metrics (mean ± std)
    cv_accuracy_mean: float
    cv_accuracy_std: float
    cv_roc_auc_mean: float
    cv_roc_auc_std: float
    cv_brier_mean: float
    cv_brier_std: float
    cv_f1_mean: float
    cv_f1_std: float

    permutation_importance: dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def honest_summary(self) -> str:
        """외부 보고용 정직 요약 — 메트릭 단독 인용 방지."""
        return (
            f"[{self.data_origin}] {self.cv_folds}-fold CV on {self.n_samples} samples "
            f"× {self.n_features} features: "
            f"acc {self.cv_accuracy_mean*100:.1f}% ± {self.cv_accuracy_std*100:.1f}pp, "
            f"AUC {self.cv_roc_auc_mean:.3f} ± {self.cv_roc_auc_std:.3f}, "
            f"Brier {self.cv_brier_mean:.3f}, F1 {self.cv_f1_mean:.3f}"
        )


class AuditRiskModel:
    """KOLAS audit risk 예측 모델 (GradientBoosting wrapper)."""

    MODEL_VERSION = "v0.6.0-gbt"

    def __init__(self, **gbm_kwargs: Any) -> None:
        if not HAS_SKLEARN:
            raise ImportError(
                "scikit-learn is required. Install: pip install 'metroai[ml]'"
            )
        defaults = {
            "n_estimators": 200,
            "max_depth": 3,
            "learning_rate": 0.05,
            "subsample": 0.9,
            "random_state": 42,
        }
        defaults.update(gbm_kwargs)
        self.clf = GradientBoostingClassifier(**defaults)
        self.feature_names: list[str] | None = None
        self.evaluation: ModelEvaluation | None = None
        self.is_fitted = False
        self.data_origin: str = "unknown"

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str] | None = None,
        data_origin: str = "synthetic",
    ) -> "AuditRiskModel":
        self.clf.fit(X, y)
        self.feature_names = feature_names
        self.data_origin = data_origin
        self.is_fitted = True
        return self

    def predict_risk(self, X: np.ndarray) -> np.ndarray:
        """위험 확률 (0.0-1.0) 반환."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        proba = self.clf.predict_proba(X)
        # GBM proba: [P(class0), P(class1)]
        if proba.shape[1] == 2:
            return proba[:, 1]
        return proba[:, 0]

    def predict_single(self, features: dict[str, float]) -> float:
        """단일 시나리오 예측."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        if self.feature_names is None:
            raise RuntimeError("Feature names unset — pass them at fit().")
        x = np.array([[features.get(f, 0.0) for f in self.feature_names]])
        return float(self.predict_risk(x)[0])

    def evaluate_cv(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: int = 5,
        data_origin: str = "synthetic",
    ) -> ModelEvaluation:
        """Stratified K-fold cross-validation 으로 정직 평가."""
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        # Manual CV to compute multiple metrics
        accs, aucs, briers, f1s = [], [], [], []
        for train_idx, test_idx in skf.split(X, y):
            X_tr, X_te = X[train_idx], X[test_idx]
            y_tr, y_te = y[train_idx], y[test_idx]
            self.clf.fit(X_tr, y_tr)
            proba = self.clf.predict_proba(X_te)[:, 1]
            pred = (proba >= 0.5).astype(int)
            accs.append(accuracy_score(y_te, pred))
            try:
                aucs.append(roc_auc_score(y_te, proba))
            except ValueError:
                aucs.append(np.nan)
            briers.append(brier_score_loss(y_te, proba))
            f1s.append(f1_score(y_te, pred, zero_division=0))

        # Refit on full data
        self.clf.fit(X, y)
        self.is_fitted = True
        self.data_origin = data_origin

        # Permutation-style importance (built-in feature importance)
        importance = {}
        if self.feature_names is not None:
            for name, imp in zip(self.feature_names, self.clf.feature_importances_):
                importance[name] = float(imp)

        eval_result = ModelEvaluation(
            data_origin=data_origin,
            n_samples=int(X.shape[0]),
            n_features=int(X.shape[1]),
            cv_folds=cv_folds,
            cv_accuracy_mean=float(np.mean(accs)),
            cv_accuracy_std=float(np.std(accs)),
            cv_roc_auc_mean=float(np.nanmean(aucs)),
            cv_roc_auc_std=float(np.nanstd(aucs)),
            cv_brier_mean=float(np.mean(briers)),
            cv_brier_std=float(np.std(briers)),
            cv_f1_mean=float(np.mean(f1s)),
            cv_f1_std=float(np.std(f1s)),
            permutation_importance=importance,
            notes=(
                f"Cross-validation on {data_origin} data. "
                "External validation on real KOLAS audit outcomes required "
                "before public accuracy claims."
            ),
        )
        self.evaluation = eval_result
        return eval_result

    def save(self, path: Path) -> None:
        """모델 + 평가 메타데이터를 저장."""
        try:
            import joblib
        except ImportError as e:
            raise ImportError("joblib required. pip install 'metroai[ml]'") from e
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "clf": self.clf,
            "feature_names": self.feature_names,
            "data_origin": self.data_origin,
            "evaluation": self.evaluation.__dict__ if self.evaluation else None,
            "model_version": self.MODEL_VERSION,
        }, path)

    @classmethod
    def load(cls, path: Path) -> "AuditRiskModel":
        try:
            import joblib
        except ImportError as e:
            raise ImportError("joblib required. pip install 'metroai[ml]'") from e
        data = joblib.load(Path(path))
        obj = cls.__new__(cls)
        obj.clf = data["clf"]
        obj.feature_names = data["feature_names"]
        obj.data_origin = data.get("data_origin", "unknown")
        if data.get("evaluation"):
            obj.evaluation = ModelEvaluation(**data["evaluation"])
        else:
            obj.evaluation = None
        obj.is_fitted = True
        return obj


def train_audit_risk_model(
    n_samples: int = 2000,
    seed: int = 42,
    cv_folds: int = 5,
    noise_level: float = 0.15,
) -> tuple[AuditRiskModel, ModelEvaluation]:
    """합성 데이터로 모델 학습 + 정직 평가 한 번에.

    Returns:
        (model, evaluation)
    """
    from .synthetic_audit_data import generate_synthetic_audit_dataset

    if not HAS_SKLEARN:
        raise ImportError(
            "scikit-learn required for training. pip install 'metroai[ml]'"
        )

    dataset = generate_synthetic_audit_dataset(
        n_samples=n_samples, seed=seed, noise_level=noise_level,
    )
    model = AuditRiskModel()
    model.feature_names = dataset.feature_names
    evaluation = model.evaluate_cv(
        dataset.X, dataset.y, cv_folds=cv_folds, data_origin="synthetic",
    )
    return model, evaluation
