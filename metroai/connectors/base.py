"""Connector 공통 베이스.

각 connector 는:
  - fetch(**kwargs) -> ConnectorResult
  - is_available() -> bool  (네트워크 + 키 등 사용 가능 여부)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ConnectorResult:
    """Connector fetch 결과.

    Attributes:
        source: 데이터 소스 식별자 (e.g., "knab.go.kr")
        is_live: True 시 실 fetch, False 시 stub fallback
        fetched_at: 시각
        records: 추출 레코드 리스트
        fallback_reason: stub fallback 사유 (실패 메시지, 미설정 등)
        warning: 경고 메시지 (e.g., "selectors stale")
    """

    source: str
    is_live: bool
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    records: list[dict[str, Any]] = field(default_factory=list)
    fallback_reason: str | None = None
    warning: str | None = None

    def label(self) -> str:
        """UI 표시용 라벨."""
        if self.is_live:
            return f"🟢 live · {self.source}"
        return f"🟡 stub · {self.source} ({self.fallback_reason or 'fallback'})"


class BaseConnector:
    """모든 connector 의 베이스."""

    source: str = "base"
    requires_key: bool = False
    env_key_name: str | None = None

    def is_available(self) -> tuple[bool, str | None]:
        """현재 환경에서 live fetch 가 가능한지.

        Returns:
            (available, fallback_reason). available=False 면 stub 으로 fallback.
        """
        import os

        # 네트워크 가능성은 fetch 시점에 시도하므로 여기서는 키만 점검
        if self.requires_key and self.env_key_name:
            if not os.environ.get(self.env_key_name):
                return False, f"env {self.env_key_name} not set"
        return True, None

    def fetch(self, **kwargs: Any) -> ConnectorResult:
        raise NotImplementedError

    def _stub_result(self, reason: str, records: list[dict[str, Any]]) -> ConnectorResult:
        return ConnectorResult(
            source=self.source,
            is_live=False,
            records=records,
            fallback_reason=reason,
        )
