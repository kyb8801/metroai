"""NTIS (Korea National Science & Technology Information Service) connector.

데이터: ntis.go.kr — 국가 R&D 과제·공고·프로그램.
KEY 불필요 (공개 검색 페이지).

semi-intel + kolas-audit-predictor 외부 피처로 사용:
  - 측정·표준 관련 R&D 과제 트렌드
  - KOLAS 인정 시험소가 받은 정부 과제 현황
"""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseConnector, ConnectorResult

logger = logging.getLogger(__name__)


class NtisConnector(BaseConnector):
    """NTIS 공개 검색 connector."""

    source = "ntis.go.kr"
    requires_key = False

    def fetch(self, *, keyword: str = "측정 표준", max_items: int = 20) -> ConnectorResult:
        """NTIS 과제 검색.

        Note: 실 구현 시 ntis.go.kr/ndb/ko/ndb_searchOpenApi.do 등 사용.
        본 v0.6.0 stub 은 키워드를 검증만 하고 합리적 더미 반환.
        """
        try:
            import requests  # noqa: F401
        except ImportError:
            return self._stub_result(
                "requests not installed", _default_stub(keyword)
            )

        try:
            return self._live_fetch(keyword=keyword, max_items=max_items)
        except Exception as e:
            logger.warning(f"NTIS live fetch failed: {e}")
            return ConnectorResult(
                source=self.source,
                is_live=False,
                records=_default_stub(keyword),
                fallback_reason=f"live fetch error: {type(e).__name__}: {e}",
            )

    def _live_fetch(self, *, keyword: str, max_items: int) -> ConnectorResult:
        """v0.6.0 — NTIS 공개 검색 페이지 스크래핑은 추후 정밀화."""
        # 현재 구현은 stub fallback (NTIS 검색 API 가 인증을 요구하는지,
        # 공개 검색 페이지 selector 가 안정적인지 미검증)
        raise NotImplementedError(
            "NTIS live fetch not yet implemented. Returning stub. "
            "TODO: ntis.go.kr 공개 검색 페이지 selector 검증 후 구현."
        )


def _default_stub(keyword: str) -> list[dict[str, Any]]:
    return [
        {
            "title": f"({keyword}) 첨단 나노소자 표면 거칠기 측정 표준 개발",
            "agency": "한국표준과학연구원 (KRISS)",
            "year": 2026,
            "budget_won": 850_000_000,
            "status": "진행중",
        },
        {
            "title": f"({keyword}) Si CRM 인증값 추적성 확보 연구",
            "agency": "한국화학융합시험연구원 (KTR)",
            "year": 2026,
            "budget_won": 320_000_000,
            "status": "공고중",
        },
    ]
