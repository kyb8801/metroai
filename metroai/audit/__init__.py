"""Audit 모듈 — verifiable MCP 의 핵심.

박수연(MetroAI advisor) 통합 — v0.6.0 신규.

각 측정 결과·예측·SOP 변경에 대해 변조 불가능한 감사 추적을 제공:
  - Ed25519 디지털 서명 — 결과의 무결성 보증
  - PROV-O 프로비넌스 — 입력·모델·산출의 전체 lineage
  - 일자별 audit log (JSON-LD)

이 모듈은 KOLAS 정기심사·내부감사 시 'AI 출력이 사후 변조되지 않았음'
을 입증하는 데 사용된다.
"""

from .signature import (
    Ed25519Signer,
    SignedRecord,
    SignatureVerificationError,
    generate_keypair,
)
from .provenance import (
    ProvenanceRecord,
    build_calculation_provenance,
    serialize_provenance_jsonld,
)

__all__ = [
    "Ed25519Signer",
    "SignedRecord",
    "SignatureVerificationError",
    "generate_keypair",
    "ProvenanceRecord",
    "build_calculation_provenance",
    "serialize_provenance_jsonld",
]
