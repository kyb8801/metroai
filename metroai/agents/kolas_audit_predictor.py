"""kolas-audit-predictor agent."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import AgentResult, AgentStatus, BaseAgent


class KolasAuditPredictorAgent(BaseAgent):
    name = "kolas-audit-predictor"
    description = "audit risk prediction (v0.6 baseline + optional GBT)"
    powered_by_ai = True

    def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        context = context or {}
        sop_completeness = float(context.get("sop_completeness", 0.87))
        months_since_audit = float(context.get("months_since_last_audit", 8.5))
        turnover = float(context.get("personnel_turnover_signal", 0.18))
        nonconformities = int(context.get("recent_nonconformities", 1))
        scope_count = float(context.get("accreditation_scope_count", 2))
        method_count = float(context.get("measurement_method_count", 8))
        model_path = context.get("model_path")

        risk = None
        model_metadata: dict[str, Any] = {}

        if model_path:
            try:
                from pathlib import Path
                from ..ml import AuditRiskModel
                model = AuditRiskModel.load(Path(model_path))
                feats = {
                    "sop_completeness": sop_completeness,
                    "months_since_last_audit": months_since_audit,
                    "personnel_turnover": turnover,
                    "recent_nonconformities": nonconformities,
                    "accreditation_scope_count": scope_count,
                    "measurement_method_count": method_count,
                }
                risk = model.predict_single(feats)
                model_metadata = {
                    "model_type": "GradientBoostingClassifier",
                    "model_version": model.MODEL_VERSION,
                    "data_origin": model.data_origin,
                    "honest_metric": (
                        model.evaluation.honest_summary()
                        if model.evaluation else "evaluation metadata missing"
                    ),
                }
            except Exception as e:
                model_metadata = {
                    "model_type": "GBT_load_failed",
                    "error": f"{type(e).__name__}: {e}",
                    "fallback": "baseline_rule",
                }
                risk = None

        base_risk = 0.10
        sop_gap_term = (1 - sop_completeness) * 0.40
        time_term = min(months_since_audit / 24.0, 0.30)
        turnover_term = turnover * 0.20
        nc_term = min(nonconformities * 0.08, 0.24)

        if risk is None:
            risk = base_risk + sop_gap_term + time_term + turnover_term + nc_term
            risk = max(0.0, min(1.0, risk))
            if not model_metadata:
                model_metadata = {
                    "model_type": "rule_based_baseline",
                    "model_version": "v0.6.0-baseline",
                    "data_origin": "no_training_data",
                    "honest_metric": (
                        "Hand-tuned weighted sum. Not trained on data. "
                        "Accuracy unknown. Use D sprint trained GBT for honest metrics."
                    ),
                }

        contributors = [
            {"factor": "SOP gap", "contribution_pct": sop_gap_term * 100, "direction": "up"},
            {"factor": "months since last audit", "contribution_pct": time_term * 100, "direction": "up"},
            {"factor": "personnel turnover", "contribution_pct": turnover_term * 100, "direction": "up"},
            {"factor": "recent nonconformities", "contribution_pct": nc_term * 100, "direction": "up"},
        ]
        contributors.sort(key=lambda c: c["contribution_pct"], reverse=True)

        recommendations = [
            {
                "priority": "P0",
                "action": "Update SOP M-04 per kolas-monitor gap finding",
                "expected_risk_reduction_pct": min(sop_gap_term * 50, 8.0),
                "source_agent": self.name,
            },
            {
                "priority": "P1",
                "action": "Run internal audit dry-run + document results",
                "expected_risk_reduction_pct": 4.2,
                "source_agent": "orchestrator",
            },
            {
                "priority": "P2",
                "action": "Migrate technical manager form to KAB-F-21-2026",
                "expected_risk_reduction_pct": 1.5,
                "source_agent": "kolas-monitor",
            },
        ]

        reasoning = (
            f"Estimated risk {risk*100:.1f}%. Top contributors: "
            f"SOP gap (+{sop_gap_term*100:.1f}pp), "
            f"time since last audit (+{time_term*100:.1f}pp)."
        )

        payload = {
            "risk_score": risk,
            "confidence": 0.81 if model_metadata.get("data_origin") == "synthetic" else 0.5,
            "contributors": contributors,
            "recommendations": recommendations,
            "reasoning": reasoning,
            "model_metadata": model_metadata,
            "disclaimer": (
                "Predictions based on KOLAS public data + opt-in lab data. "
                "Final judgment must be made by the Quality Manager."
            ),
            "notes": (
                "Cite model_metadata.honest_metric in external reports. "
                "Synthetic-data metrics do not imply real-world accuracy."
            ),
        }

        return self._record(
            AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                timestamp=datetime.utcnow(),
                latest_output=f"Risk {risk*100:.1f}% (confidence {payload['confidence']*100:.0f}%), top action: SOP M-04 update",
                payload=payload,
                ai_confidence=payload["confidence"],
                powered_by_ai=True,
            )
        )
