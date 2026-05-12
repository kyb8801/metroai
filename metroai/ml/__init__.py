"""ML 모듈 — v0.6.0 신규.

박수연(MetroAI advisor) 통합. 정직 표기 우선.

서브 모듈:
  - synthetic_audit_data: 합성 KOLAS 감사 데이터 생성기
  - audit_risk_model: GradientBoosting 기반 audit risk predictor

핵심 원칙:
  - 모델 메트릭은 항상 (a) 어떤 데이터로 (b) 어떤 split 으로 평가됐는지 명기
  - "X% accuracy" 단독 인용 금지. 항상 컨텍스트 동반
  - 실데이터 학습 전까지는 모든 메트릭에 "synthetic" 라벨
"""

from .audit_risk_model import (
    AuditRiskModel,
    ModelEvaluation,
    train_audit_risk_model,
)
from .synthetic_audit_data import generate_synthetic_audit_dataset

__all__ = [
    "AuditRiskModel",
    "ModelEvaluation",
    "train_audit_risk_model",
    "generate_synthetic_audit_dataset",
]
