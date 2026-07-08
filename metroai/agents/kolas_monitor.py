"""kolas-monitor 에이전트 — KOLAS 고시·표준 변경 일일 스캔.

v2 spec: 메인 대시보드 우하단 카드 + KOLAS 모니터링 피드(블록 5)
의 핵심 데이터 공급원. SOP 갭 분석(블록 4)도 이 에이전트의 출력에
의존.

데이터 소스 (v0.6.0 stub):
  - KOLAS 공식 사이트 (knab.go.kr) — vertical-mcp/kolas-mcp 연동 예정
  - KAB / KTR 공시
  - 데이터.고크 (data.go.kr) — 시험·교정 관련 고시
  - ISO/IEC, OIML 표준 개정 알림 (글로벌 확장 시)

핵심 출력:
  - feed_items: 최근 변경사항 리스트
  - impact_map: 변경 → 영향 받는 SOP/인정범위 매핑
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .base import AgentResult, AgentStatus, BaseAgent


class KolasMonitorAgent(BaseAgent):
    """KOLAS 고시·표준 변경 일일 스캔 에이전트."""

    name = "kolas-monitor"
    description = "KOLAS 고시·표준 변경 일일 스캔"
    powered_by_ai = True  # 변경 텍스트 → 영향 SOP 매핑에 LLM 사용

    def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        """KOLAS 고시 페이지 monitor — KolasConnector 자동 live/stub fallback.

        context 인자:
            institution_scope: list[str] — 기관 인정범위 (예: ["RMP", "교정"])
            lookback_days: int — 기본 7
            use_live: bool — True 시 강제 live fetch 시도 (기본 True, 실패 시 stub)
        """
        from ..connectors import KolasConnector

        context = context or {}
        scope = context.get("institution_scope", ["RMP"])
        lookback_days = context.get("lookback_days", 7)
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        # Connector 호출 — live 시도 후 자동 fallback
        connector = KolasConnector()
        cresult = connector.fetch(lookback_days=lookback_days, max_items=20)

        feed_items = cresult.records
        # 상태 결정: live + 데이터 있음 → OK, stub → STALE
        if cresult.is_live and feed_items:
            status = AgentStatus.OK
            data_label = "live"
        else:
            status = AgentStatus.STALE
            data_label = f"stub ({cresult.fallback_reason or 'unknown'})"

        top_item = feed_items[0] if feed_items else None
        if top_item:
            summary_line = (
                f"최근 {lookback_days}일 변경 {len(feed_items)}건 — "
                f"{top_item.get('title','?')[:40]} "
                f"({top_item.get('impact_level','-')}) · {data_label}"
            )
        else:
            summary_line = f"최근 {lookback_days}일 변경 없음 · {data_label}"

        payload = {
            "feed_items": feed_items,
            "scope_filter": scope,
            "cutoff": cutoff.isoformat(),
            "data_source": cresult.source,
            "is_live": cresult.is_live,
            "fallback_reason": cresult.fallback_reason,
            "warning": cresult.warning,
            "notes": (
                "KolasConnector 가 knab.go.kr 실 페이지 fetch 를 시도하고, "
                "실패 시 보수적 stub 으로 fallback 합니다. "
                "live 표시일 때만 외부 약속에 사용 가능."
            ),
        }

        return self._record(
            AgentResult(
                agent_name=self.name,
                status=status,
                timestamp=datetime.utcnow(),
                latest_output=summary_line,
                payload=payload,
                ai_confidence=0.85 if cresult.is_live else 0.5,
                powered_by_ai=True,
            )
        )
