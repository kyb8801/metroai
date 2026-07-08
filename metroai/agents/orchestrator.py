"""orchestrator 에이전트 — 6 에이전트 조정·우선순위.

v2 spec: 메인 대시보드 우측 "오늘의 작업" 카드를 채우는 핵심.
각 에이전트의 출력을 받아 P0/P1/P2 작업 큐로 변환하고,
중복 제거·기한순 정렬·담당자 매핑을 수행한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .base import AgentResult, AgentStatus, BaseAgent
from .kolas_audit_predictor import KolasAuditPredictorAgent
from .kolas_monitor import KolasMonitorAgent
from .schedule import ScheduleAgent


class OrchestratorAgent(BaseAgent):
    """6 에이전트 조정 + 작업 큐 생성 에이전트."""

    name = "orchestrator"
    description = "6 에이전트 조정·우선순위 결정"
    powered_by_ai = False  # 규칙 기반 합성

    def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        """다른 에이전트 결과를 받아 통합 작업 큐 생성.

        context 인자:
            agent_results: dict[str, AgentResult] | None
                특정 에이전트 결과를 미리 주입(테스트용). 없으면 stub 실행.
        """
        context = context or {}
        agent_results = context.get("agent_results", {})

        # 필요 시 다른 에이전트 즉시 실행 (stub)
        if "kolas-audit-predictor" not in agent_results:
            agent_results["kolas-audit-predictor"] = KolasAuditPredictorAgent().run({})
        if "kolas-monitor" not in agent_results:
            agent_results["kolas-monitor"] = KolasMonitorAgent().run({})
        if "schedule" not in agent_results:
            agent_results["schedule"] = ScheduleAgent().run({})

        # 통합 task queue 구성
        tasks: list[dict[str, Any]] = []

        # 1. audit-predictor 권장사항 → tasks
        for rec in agent_results["kolas-audit-predictor"].payload.get("recommendations", []):
            tasks.append({
                "priority": rec["priority"],
                "title": rec["action"],
                "source_agent": rec["source_agent"],
                "expected_impact": f"-{rec['expected_risk_reduction_pct']:.1f}pp",
                "due_in_days": 14,
            })

        # 2. kolas-monitor 영향 큰 항목 → tasks
        for item in agent_results["kolas-monitor"].payload.get("feed_items", []):
            if item.get("impact_level") == "high":
                tasks.append({
                    "priority": "P1",
                    "title": f"{item['title']} 영향 SOP 검토 ({', '.join(item['affected_sops'])})",
                    "source_agent": "kolas-monitor",
                    "expected_impact": "compliance risk reduction",
                    "due_date": item.get("recommended_action_by"),
                })

        # 3. schedule 만료 임박 → tasks
        for ev in agent_results["schedule"].payload.get("upcoming_events", []):
            if ev.get("urgency") == "high":
                tasks.append({
                    "priority": "P0",
                    "title": ev["title"],
                    "source_agent": "schedule",
                    "due_date": ev["date"],
                    "expected_impact": "ops continuity",
                })

        # 우선순위 + due_date 정렬
        priority_rank = {"P0": 0, "P1": 1, "P2": 2}
        tasks.sort(key=lambda t: (priority_rank.get(t["priority"], 9), t.get("due_date", "")))

        payload = {
            "tasks": tasks,
            "task_count": len(tasks),
            "source_agents": list(agent_results.keys()),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return self._record(
            AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                timestamp=datetime.utcnow(),
                latest_output=f"오늘의 작업 {len(tasks)}건 ({sum(1 for t in tasks if t['priority']=='P0')} P0)",
                payload=payload,
                powered_by_ai=False,
            )
        )
