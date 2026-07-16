"""DCC (Digital Calibration Certificate) 모듈 — 실험적 1차 구현.

PTB 주도의 디지털 교정성적서 XML 표준(DCC 스키마 3.3.0, https://wiki.dcc.ptb.de)을
KOLAS/ISO 17025 문맥에서 다루기 위한 파서·빌더.

- :mod:`metroai.dcc.parser` — DCC XML 읽기 + 경량 구조 점검 + (선택) XSD 검증
- :mod:`metroai.dcc.builder` — GUM 계산 결과 → DCC XML 초안
- :mod:`metroai.dcc.units` — 상용 단위 → D-SI 표기 변환
- ``kolas_map.md`` — KOLAS/ISO 17025 성적서 필수 기재사항 ↔ DCC 요소 매핑 문서

전자서명(ds:Signature)·PDF/A-3 임베딩·refType 국제 어휘 정합은 미구현(로드맵).
"""

from .builder import DCCBuilder, export_dcc_xml
from .parser import (
    DCC_NS,
    OFFICIAL_XSD_URL,
    SI_NS,
    TARGET_SCHEMA_VERSION,
    DCCDocument,
    DCCQuantity,
    DCCUncertainty,
    check_required_structure,
    parse_dcc,
    validate_dcc,
)
from .units import DSI_UNIT_MAP, to_dsi_unit

__all__ = [
    "DCC_NS",
    "SI_NS",
    "TARGET_SCHEMA_VERSION",
    "OFFICIAL_XSD_URL",
    "DCCDocument",
    "DCCQuantity",
    "DCCUncertainty",
    "DCCBuilder",
    "export_dcc_xml",
    "parse_dcc",
    "check_required_structure",
    "validate_dcc",
    "DSI_UNIT_MAP",
    "to_dsi_unit",
]
