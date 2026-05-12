"""DART (Korea FSS 전자공시) connector.

API: https://opendart.fss.or.kr
환경변수: DART_API_KEY (40자, 무료 발급)

semi-intel agent 가 반도체 capex 신호를 추출할 때 사용.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseConnector, ConnectorResult

logger = logging.getLogger(__name__)


# 반도체 metrology 장비/소재 관련 상장사 코드 (DART corp_code 기준 일부)
SEMICONDUCTOR_FOCUS_CORPS: list[dict[str, str]] = [
    {"name": "삼성전자", "corp_code": "00126380"},
    {"name": "SK하이닉스", "corp_code": "00164779"},
    # 추후 확장: 동진쎄미켐, 솔브레인, 한미반도체 등
]


class DartConnector(BaseConnector):
    """DART OpenAPI connector."""

    source = "opendart.fss.or.kr"
    requires_key = True
    env_key_name = "DART_API_KEY"

    def fetch(self, *, corp_codes: list[str] | None = None,
              bgn_de: str | None = None) -> ConnectorResult:
        """주요 반도체 기업의 최근 공시 fetch.

        Args:
            corp_codes: 대상 corp_code 리스트 (None 시 기본 focus set)
            bgn_de: yyyymmdd 형식 시작일 (None 시 30일 전)
        """
        available, reason = self.is_available()
        if not available:
            return self._stub_result(reason or "unknown", _default_stub())

        try:
            import requests  # noqa: F401
        except ImportError:
            return self._stub_result(
                "requests not installed", _default_stub()
            )

        try:
            return self._live_fetch(corp_codes=corp_codes, bgn_de=bgn_de)
        except Exception as e:
            logger.warning(f"DART live fetch failed: {e}")
            return ConnectorResult(
                source=self.source,
                is_live=False,
                records=_default_stub(),
                fallback_reason=f"live fetch error: {type(e).__name__}: {e}",
            )

    def _live_fetch(self, *, corp_codes, bgn_de) -> ConnectorResult:
        import os
        from datetime import datetime, timedelta

        import requests

        key = os.environ["DART_API_KEY"]
        if not bgn_de:
            bgn_de = (datetime.utcnow() - timedelta(days=30)).strftime("%Y%m%d")
        end_de = datetime.utcnow().strftime("%Y%m%d")

        targets = corp_codes or [c["corp_code"] for c in SEMICONDUCTOR_FOCUS_CORPS]
        records: list[dict[str, Any]] = []
        for corp_code in targets:
            url = "https://opendart.fss.or.kr/api/list.json"
            params = {
                "crtfc_key": key,
                "corp_code": corp_code,
                "bgn_de": bgn_de,
                "end_de": end_de,
                "page_no": 1,
                "page_count": 10,
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("status") != "000":
                continue  # 공시 없음 또는 에러
            for item in data.get("list", []):
                records.append({
                    "corp_name": item.get("corp_name"),
                    "corp_code": item.get("corp_code"),
                    "report_name": item.get("report_nm"),
                    "rcept_dt": item.get("rcept_dt"),
                    "rcept_no": item.get("rcept_no"),
                })

        return ConnectorResult(
            source=self.source,
            is_live=True,
            records=records,
        )


def _default_stub() -> list[dict[str, Any]]:
    return [
        {
            "corp_name": "삼성전자",
            "corp_code": "00126380",
            "report_name": "주요사항보고서(자기주식취득결정)",
            "rcept_dt": "2026-05-08",
            "rcept_no": "stub-001",
        },
        {
            "corp_name": "SK하이닉스",
            "corp_code": "00164779",
            "report_name": "정기공시(분기보고서)",
            "rcept_dt": "2026-05-02",
            "rcept_no": "stub-002",
        },
    ]
