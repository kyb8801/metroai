"""KOLAS / KAB / KTR 고시 페이지 connector.

데이터 소스:
  - knab.go.kr — KOLAS 공식 안내·고시 페이지 (KATS 국가표준기술원 산하)
  - 백업: vertical-mcp/kolas-mcp 의 동일 scrape 로직 (Node.js)

전략:
  1. 네트워크 가능 + requests/beautifulsoup4 설치되어 있으면 live fetch
  2. 실패 시 stub fallback (kolas_monitor agent 의 디폴트 데이터)

KOLAS notice 페이지 구조 (2026-04 기준):
  - https://www.knab.go.kr/usr/inf/srh/NoticeList.do (예시 — 실제 URL 은 검증 필요)
  - 일반적으로 HTML 게시판 테이블 → 행마다 (날짜, 제목, 첨부) 추출
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from .base import BaseConnector, ConnectorResult

logger = logging.getLogger(__name__)


KOLAS_NOTICE_URL_CANDIDATES = [
    "https://www.knab.go.kr/usr/cmm/srh/NoticeList.do",
    "https://www.knab.go.kr/usr/cmm/srh/NoticeBoardList.do",
]


class KolasConnector(BaseConnector):
    """KOLAS 고시·공지 수집 connector."""

    source = "knab.go.kr"
    requires_key = False

    def fetch(self, *, lookback_days: int = 30, max_items: int = 20) -> ConnectorResult:
        """KOLAS 고시 페이지에서 최근 변경사항 수집.

        Args:
            lookback_days: 최근 N일 안의 변경만 추출
            max_items: 최대 항목 수
        """
        available, reason = self.is_available()
        if not available:
            return self._stub_result(reason or "unknown", _default_stub())

        # 의존성 점검
        try:
            import requests  # noqa: F401
            from bs4 import BeautifulSoup  # noqa: F401
        except ImportError:
            return self._stub_result(
                "requests/beautifulsoup4 not installed (pip install requests beautifulsoup4)",
                _default_stub(),
            )

        # 실제 fetch 시도
        try:
            return self._live_fetch(lookback_days=lookback_days, max_items=max_items)
        except Exception as e:
            logger.warning(f"KOLAS live fetch failed: {e}")
            return ConnectorResult(
                source=self.source,
                is_live=False,
                records=_default_stub(),
                fallback_reason=f"live fetch error: {type(e).__name__}: {e}",
                warning="실제 페이지 구조가 변경되었을 수 있음 — selectors 검토 필요.",
            )

    def _live_fetch(self, *, lookback_days: int, max_items: int) -> ConnectorResult:
        """실 fetch 구현 — knab.go.kr 의 KOLAS 공지 게시판.

        주의: 페이지 구조가 변경되면 selector 갱신 필요. 실패 시 명확히 raise.
        """
        import requests
        from bs4 import BeautifulSoup

        last_error: Exception | None = None
        for url in KOLAS_NOTICE_URL_CANDIDATES:
            try:
                resp = requests.get(
                    url,
                    timeout=10,
                    headers={
                        "User-Agent": "MetroAI/0.6.0 (KOLAS compliance monitoring; +https://github.com/kyb8801/metroai)"
                    },
                )
                if resp.status_code != 200:
                    last_error = RuntimeError(f"HTTP {resp.status_code} from {url}")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                rows = soup.select("table.board_list tbody tr") or soup.select("table tbody tr")
                if not rows:
                    last_error = RuntimeError(f"No rows found in {url}")
                    continue

                records: list[dict[str, Any]] = []
                for r in rows[:max_items]:
                    cells = r.find_all("td")
                    if len(cells) < 2:
                        continue
                    title_a = r.find("a")
                    title = title_a.get_text(strip=True) if title_a else cells[1].get_text(strip=True)
                    date_text = cells[-1].get_text(strip=True) if cells[-1] else ""
                    records.append({
                        "title": title,
                        "date": date_text,
                        "source": "KOLAS",
                        "url": (title_a.get("href") if title_a else None),
                        "impact_level": "unknown",  # LLM 분류 단계에서 결정
                        "affected_sops": [],
                    })

                if not records:
                    last_error = RuntimeError(f"Parsed 0 records from {url}")
                    continue

                return ConnectorResult(
                    source=self.source,
                    is_live=True,
                    records=records,
                )
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All KOLAS endpoints failed; last error: {last_error}")


def _default_stub() -> list[dict[str, Any]]:
    """v0.6.0 stub fallback — 합리적 더미 데이터 (실 형식과 동일 schema)."""
    return [
        {
            "date": "2026-05-08",
            "source": "KOLAS",
            "title": "KOLAS 일반지침 KAB-S-15 개정 (불확도 평가 절차)",
            "summary": (
                "5.3절 불확도 평가 절차의 표현이 ISO/IEC Guide 98-3:2008 "
                "최신 conformity 평가 가이드와 정합되도록 개정."
            ),
            "url": None,
            "impact_level": "high",
            "affected_sops": ["M-04-2024", "M-07-2024"],
            "affected_scope": ["RMP"],
            "recommended_action_by": "2026-05-22",
            "ai_confidence": 0.86,
        },
        {
            "date": "2026-05-05",
            "source": "KAB",
            "title": "KAB 인정 행정 절차 안내 v3.2 (인력 자격 입증 문서)",
            "summary": (
                "기술관리자 자격 입증 문서 양식이 양식 KAB-F-21-2026 으로 변경. "
                "기존 양식 사용 시 2026-09-30 까지 마이그레이션 필요."
            ),
            "url": None,
            "impact_level": "medium",
            "affected_sops": [],
            "affected_scope": ["all"],
            "recommended_action_by": "2026-09-30",
            "ai_confidence": 0.92,
        },
    ]
