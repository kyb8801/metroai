"""schedule 에이전트 — 검토·교정·심사 일정 자동 관리.

v2 spec: 인증서/인력/일정 통합 뷰(블록 6)의 Tab 3 "일정" 캘린더 데이터
공급. 메인 대시보드의 "다음 정기심사 D-37" KPI 도 이 에이전트가 채움.

이벤트 종류:
  - 정기심사 (KOLAS) — 인정 주기 기반
  - 내부 감사 — 분기/반기 주기
  - 교정 (보유 표준기) — 인증서 만료일 기반
  - 인력 자격 갱신 — 인력 DB 기반
  - 표준 개정 알림 (kolas-monitor 연동)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .base import AgentResult, AgentStatus, BaseAgent


class ScheduleAgent(BaseAgent):
    """일정 자동 관리 에이전트."""

    name = "schedule"
    description = "검토·교정·심사 일정 자동 관리"
    powered_by_ai = False

    def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        """v0.6.0 stub — 하드코딩된 예시 일정.

        context 인자:
            today: datetime — 기준일 (테스트 reproducibility)
            horizon_days: int — 미래 N일까지 lookup. 기본 90.
        """
        context = context or {}
        today = context.get("today", datetime.utcnow())
        horizon_days = int(context.get("horizon_days", 90))

        # v0.6.0 stub events — 추후 SQLite events 테이블 + cron rules 로 대체
        events = [
            {
                "date": (today + timedelta(days=37)).strftime("%Y-%m-%d"),
                "type": "정기심사",
                "title": "KOLAS 정기심사 (RMP 인정범위)",
                "urgency": "high",  # D-37 → high
                "days_until": 37,
            },
            {
                "date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                "type": "인증서 만료",
                "title": "교정 인증서 #2026-CL-014 만료",
                "urgency": "medium",
                "days_until": 60,
            },
            {
                "date": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
                "type": "내부 감사",
                "title": "2분기 내부 감사 시작",
                "urgency": "medium",
                "days_until": 14,
            },
            {
                "date": (today + timedelta(days=22)).strftime("%Y-%m-%d"),
                "type": "표준기 교정",
                "title": "Block gauge 25mm 교정 (만료 D-7 전)",
                "urgency": "medium",
                "days_until": 22,
            },
        ]

        # urgency 자동 갱신 (정기심사는 D-30 이내 high, D-60 이내 medium)
        for ev in events:
            d = ev["days_until"]
            if ev["type"] == "정기심사":
                ev["urgency"] = "high" if d <= 45 else ("medium" if d <= 90 else "low")
            elif ev["type"] == "인증서 만료":
                ev["urgency"] = "high" if d <= 30 else ("medium" if d <= 60 else "low")

        next_audit = next((e for e in events if e["type"] == "정기심사"), None)
        d_day = next_audit["days_until"] if next_audit else None

        payload = {
            "upcoming_events": events,
            "horizon_days": horizon_days,
            "next_regulatory_audit_d_day": d_day,
            "today": today.isoformat() if isinstance(today, datetime) else str(today),
        }

        return self._record(
            AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                timestamp=datetime.utcnow(),
                latest_output=f"향후 {horizon_days}일 이벤트 {len(events)}건, 정기심사 D-{d_day}",
                payload=payload,
                powered_by_ai=False,
            )
        )
