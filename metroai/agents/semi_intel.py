"""semi-intel 에이전트 — 반도체 산업 동향 스캔."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import AgentResult, AgentStatus, BaseAgent


class SemiIntelAgent(BaseAgent):
    """반도체 산업 동향 스캔 에이전트."""

    name = "semi-intel"
    description = "반도체 산업 동향 스캔 (DART · NTIS 공시)"
    powered_by_ai = False

    def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        """DART + NTIS connector wiring."""
        from ..connectors import DartConnector, NtisConnector

        context = context or {}
        quarter = context.get("quarter", "2026Q1")
        ntis_keyword = context.get("ntis_keyword", "측정 표준")

        dart = DartConnector().fetch()
        ntis = NtisConnector().fetch(keyword=ntis_keyword)

        disclosure_count = len(dart.records)
        if disclosure_count >= 4:
            capex_signal = "high_activity"
        elif disclosure_count >= 2:
            capex_signal = "moderate_uptrend"
        else:
            capex_signal = "quiet"

        ntis_total_budget = sum(r.get("budget_won", 0) for r in ntis.records)
        any_live = dart.is_live or ntis.is_live
        status = AgentStatus.OK if any_live else AgentStatus.STALE

        payload = {
            "quarter": quarter,
            "capex_signal": capex_signal,
            "dart_disclosure_count": disclosure_count,
            "ntis_total_budget_won": ntis_total_budget,
            "ntis_record_count": len(ntis.records),
            "dart_source": dart.source,
            "dart_is_live": dart.is_live,
            "dart_fallback_reason": dart.fallback_reason,
            "ntis_source": ntis.source,
            "ntis_is_live": ntis.is_live,
            "ntis_fallback_reason": ntis.fallback_reason,
            "dart_records_preview": dart.records[:3],
            "ntis_records_preview": ntis.records[:3],
            "notes": "Live fetch with stub fallback. Use *_is_live for external claims.",
        }

        dart_flag = "live" if dart.is_live else "stub"
        ntis_flag = "live" if ntis.is_live else "stub"
        return self._record(
            AgentResult(
                agent_name=self.name,
                status=status,
                timestamp=datetime.utcnow(),
                latest_output=(
                    f"{quarter} capex={capex_signal}, "
                    f"DART {disclosure_count} disclosures ({dart_flag}), "
                    f"NTIS R&D KRW {ntis_total_budget/1e8:.1f} 100M ({ntis_flag})"
                ),
                payload=payload,
                powered_by_ai=False,
            )
        )
