"""6-Agent 공통 베이스 클래스.

v2 spec — 모든 MetroAI 에이전트는 BaseAgent 를 상속하며,
run() 호출 시 AgentResult 를 반환한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentStatus(Enum):
    """대시보드 상태 strip 표시용."""

    OK = "ok"  # 녹색 — 정상
    STALE = "stale"  # 황색 — 출력이 오래됨
    ERROR = "error"  # 적색 — 마지막 실행 실패
    DISABLED = "disabled"  # 회색 — 사용자가 끔


@dataclass
class AgentResult:
    """에이전트 실행 결과 — 대시보드·orchestrator 가 소비.

    Attributes:
        agent_name: 에이전트 이름 (mono 폰트 표시용)
        status: 실행 상태
        timestamp: 실행 시각
        latest_output: 1줄 요약 (대시보드 strip 표시)
        payload: 상세 데이터 (다른 에이전트나 대시보드 위젯이 사용)
        ai_confidence: 0.0-1.0, AI 출력의 신뢰도 (kolas-audit-predictor 등)
        powered_by_ai: True 시 UI에 cyan 'AI suggestion' 라벨 표시
    """

    agent_name: str
    status: AgentStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latest_output: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    ai_confidence: float | None = None
    powered_by_ai: bool = False

    def to_dashboard_card(self) -> dict[str, str]:
        """대시보드 하단 6-strip 카드 표시용 딕셔너리."""
        return {
            "name": self.agent_name,
            "status": self.status.value,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "output": self.latest_output,
        }


class BaseAgent:
    """모든 MetroAI 에이전트의 베이스.

    하위 클래스는:
      - name: 에이전트 식별자 (mono 표시용, e.g., "kolas-audit-predictor")
      - description: 1줄 설명 (랜딩 페이지 카드 표시)
      - powered_by_ai: 출력이 AI 추론 결과인지 (UI cyan 라벨)
      - run(context: dict) -> AgentResult: 실제 실행
    를 오버라이드한다.
    """

    name: str = "base-agent"
    description: str = "Base agent (override in subclass)"
    powered_by_ai: bool = False

    def __init__(self) -> None:
        self._last_result: AgentResult | None = None

    def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        """하위 클래스에서 오버라이드."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.run() must be implemented"
        )

    @property
    def last_result(self) -> AgentResult | None:
        """가장 최근 결과 (대시보드 캐시용)."""
        return self._last_result

    def _record(self, result: AgentResult) -> AgentResult:
        """결과 캐시 + 반환."""
        self._last_result = result
        return result
