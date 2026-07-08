"""v0.6.0 ML 모듈 테스트 — kolas-audit-predictor GBT 모델 + 합성 데이터.

D sprint 산출 — 정직 메트릭 검증.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

# scikit-learn 미설치 환경 skip
sklearn_required = pytest.importorskip("sklearn")


def test_synthetic_dataset_shape():
    from metroai.ml import generate_synthetic_audit_dataset

    ds = generate_synthetic_audit_dataset(n_samples=500, seed=7, noise_level=0.10)
    assert ds.X.shape == (500, 6)
    assert ds.y.shape == (500,)
    assert set(np.unique(ds.y).tolist()).issubset({0, 1})
    # class balance reasonable (10% noise, beta-skewed features → both classes present)
    assert 0.05 < ds.y.mean() < 0.95


def test_synthetic_dataset_describe_has_disclaimer():
    from metroai.ml import generate_synthetic_audit_dataset

    desc = generate_synthetic_audit_dataset(n_samples=100).describe()
    assert "synthetic" in desc["disclaimer"].lower()
    assert "real-world" in desc["disclaimer"].lower()


def test_model_cv_metrics_returned():
    from metroai.ml import train_audit_risk_model

    model, evaluation = train_audit_risk_model(n_samples=400, seed=42, cv_folds=5)
    # 합성 데이터에서 정확도 메트릭이 유의미한 범위에 있어야 함
    assert 0.4 < evaluation.cv_accuracy_mean < 0.95
    assert 0.5 < evaluation.cv_roc_auc_mean < 0.95
    assert evaluation.data_origin == "synthetic"
    assert evaluation.cv_folds == 5
    assert evaluation.n_samples == 400


def test_model_honest_summary_includes_origin():
    from metroai.ml import train_audit_risk_model

    _, ev = train_audit_risk_model(n_samples=200, seed=1, cv_folds=3)
    s = ev.honest_summary()
    assert "synthetic" in s
    assert "CV" in s
    assert "acc" in s


def test_high_risk_scenario_higher_than_low_risk():
    """도메인 sanity check — 부실 기관 위험 > 양호 기관.
    단일 시드 예측은 합성·저정확도(~60.6%) 모델 + 플랫폼별 부동소수 차이로
    경계에서 뒤집힐 수 있다(seed=42 가 Python 3.10 통과 / 3.11·3.12 실패였음).
    여러 시드의 다수결로 도메인 단조성을 견고하게 검증한다."""
    from metroai.ml import train_audit_risk_model

    low_risk_features = {
        "sop_completeness": 0.95, "months_since_last_audit": 3.0,
        "personnel_turnover": 0.05, "recent_nonconformities": 0,
        "accreditation_scope_count": 2, "measurement_method_count": 8,
    }
    high_risk_features = {
        "sop_completeness": 0.55, "months_since_last_audit": 22.0,
        "personnel_turnover": 0.6, "recent_nonconformities": 4,
        "accreditation_scope_count": 3, "measurement_method_count": 15,
    }
    n_seeds = 7
    wins = 0
    for s in range(n_seeds):
        model, _ = train_audit_risk_model(n_samples=1000, seed=s, cv_folds=3)
        if model.predict_single(high_risk_features) > model.predict_single(low_risk_features):
            wins += 1
    assert wins >= 6, f"high>low holds only in {wins}/{n_seeds} seeds (expected >=6)"

def test_save_load_roundtrip(tmp_path: Path):
    from metroai.ml import AuditRiskModel, train_audit_risk_model

    model, _ = train_audit_risk_model(n_samples=300, seed=42, cv_folds=3)
    path = tmp_path / "model.joblib"
    model.save(path)

    loaded = AuditRiskModel.load(path)
    assert loaded.data_origin == "synthetic"
    assert loaded.evaluation is not None

    # 동일 예측
    feats = {
        "sop_completeness": 0.8, "months_since_last_audit": 10.0,
        "personnel_turnover": 0.2, "recent_nonconformities": 1,
        "accreditation_scope_count": 2, "measurement_method_count": 10,
    }
    assert abs(model.predict_single(feats) - loaded.predict_single(feats)) < 1e-9


def test_baseline_no_inflation_in_predict_single():
    """베이스라인 룰 모드에서 risk 가 0-1 범위 안에 있어야."""
    from metroai.agents import KolasAuditPredictorAgent

    ag = KolasAuditPredictorAgent().run({
        "sop_completeness": 0.0,
        "months_since_last_audit": 60.0,
        "personnel_turnover_signal": 1.0,
        "recent_nonconformities": 10,
    })
    assert 0.0 <= ag.payload["risk_score"] <= 1.0
