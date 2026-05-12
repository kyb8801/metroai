"""MetroAI 6-Agent 백본 (v2 spec — KOLAS 컴플라이언스 OS).

박수연(MetroAI advisor) 통합 — v0.6.0 신규 모듈.
"""

from .base import AgentResult, AgentStatus, BaseAgent
from .semi_intel import SemiIntelAgent
from .job_scout import JobScoutAgent
from .kolas_monitor import KolasMonitorAgent
from .kolas_audit_predictor import KolasAuditPredictorAgent
from .orchestrator import OrchestratorAgent
from .schedule import ScheduleAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "AgentStatus",
    "SemiIntelAgent",
    "JobScoutAgent",
    "KolasMonitorAgent",
    "KolasAuditPredictorAgent",
    "OrchestratorAgent",
    "ScheduleAgent",
    "all_agents",
]


def all_agents():
    """6개 에이전트 인스턴스 리스트 (대시보드 strip 용)."""
    return [
        SemiIntelAgent(),
        JobScoutAgent(),
        KolasMonitorAgent(),
        KolasAuditPredictorAgent(),
        OrchestratorAgent(),
        ScheduleAgent(),
    ]
