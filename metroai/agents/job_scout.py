"""job-scout 에이전트 — 채용·인력 동향 (인력 회전율 신호).

v2 spec: kolas-audit-predictor 의 "인력 회전율" 피처를 공급.
인증 시험·교정 기관의 핵심 인력(품질책임자·기술관리자·인정 자격자)
이탈/충원 신호를 외부 채용공고에서 추정.

데이터 소스 (v0.6.0 stub):
  - 잡코리아 / 사람인 (KOLAS 인정 기관별 채용 공고 모니터)
  - 링크드인 (해외 metrology 인력 동향 — 글로벌 확장 대비)

출력:
  - 기관별 인력 회전율 추정치 (0.0-1.0, AI 추정 신호)
  - 최근 30일 채용 공고 수
  - 인증 자격자 이탈 위험 플래그
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import AgentResult, AgentStatus, BaseAgent


class JobScoutAgent(BaseAgent):
    """채용·인력 동향 추정 에이전트."""

    name = "job-scout"
    description = "채용·인력 동향 (인력 회전율 데이터 소스)"
    powered_by_ai = True  # 자연어 공고 → 신호 추정 단계에서 LLM 사용

    def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        """v0.6.0 stub — 외부 채용 사이트 fetch + LLM 분류 미구현.

        context 인자:
            institution_id: str — 분석 대상 기관 ID
            lookback_days: int — 기본 30
        """
        context = context or {}
        institution_id = context.get("institution_id", "demo-org-001")
        lookback_days = context.get("lookback_days", 30)

        payload = {
            "institution_id": institution_id,
            "lookback_days": lookback_days,
            "open_postings_count": 2,  # placeholder
            "turnover_signal": 0.18,  # 0.0-1.0, 추정값
            "risk_flag": False,
            "ai_evidence": (
                "최근 30일간 품질책임자·기술관리자 직군 공고 0건. "
                "안정적 인력 운영으로 추정."
            ),
            "notes": "v0.6.0 stub — 실제 사이트 스크래핑·LLM 분류 미구현.",
        }

        return self._record(
            AgentResult(
                agent_name=self.name,
                status=AgentStatus.STALE,
                timestamp=datetime.utcnow(),
                latest_output=f"인력 회전율 추정 0.18 (낮음), 직군 공고 2건",
                payload=payload,
                ai_confidence=0.55,
                powered_by_ai=True,
            )
        )
