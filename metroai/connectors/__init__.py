"""External data connectors — v0.6.0 신규.

박수연(MetroAI advisor) 통합.

각 connector 는 명확히 두 모드를 가진다:
  - live: 실제 외부 API/페이지 fetch (네트워크 필요)
  - stub: 하드코딩 데모 데이터 (CI/오프라인용)

사용 시 connector 의 `fetch()` 메서드가 자동으로 환경을 감지하고
fallback 한다. 결과 객체는 항상 `is_live` 플래그를 포함하므로
에이전트는 출력에 정직히 표시할 수 있다.
"""

from .base import ConnectorResult, BaseConnector
from .kolas_connector import KolasConnector
from .dart_connector import DartConnector
from .ntis_connector import NtisConnector

__all__ = [
    "ConnectorResult",
    "BaseConnector",
    "KolasConnector",
    "DartConnector",
    "NtisConnector",
]
