"""Ed25519 디지털 서명 모듈.

KOLAS 정기심사·내부감사 시 AI 출력의 무결성을 입증하기 위한 서명.
표준: RFC 8032 (Edwards-curve Digital Signature Algorithm).

선택적 의존성:
  - cryptography>=42.0 (Ed25519 native)
  - 미설치 시 ImportError 명확히 안내
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class SignatureVerificationError(Exception):
    """서명 검증 실패."""


@dataclass
class SignedRecord:
    """서명된 감사 레코드.

    Attributes:
        record_id: UUID4 형식의 레코드 식별자
        timestamp: 서명 시각 (UTC ISO-8601)
        record_type: 'calculation' / 'agent_output' / 'sop_change' / 'audit_event'
        payload: 서명 대상 데이터 (직렬화 가능)
        payload_sha256: payload 의 SHA-256 다이제스트 (hex)
        signature_b64: Ed25519 서명 (base64)
        public_key_b64: 검증용 공개키 (base64)
        signing_key_id: 키 식별자 (e.g., "metroai-2026-key-01")
    """

    record_id: str
    timestamp: str
    record_type: str
    payload: dict[str, Any]
    payload_sha256: str
    signature_b64: str
    public_key_b64: str
    signing_key_id: str = "metroai-default"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "record_type": self.record_type,
            "payload": self.payload,
            "payload_sha256": self.payload_sha256,
            "signature_b64": self.signature_b64,
            "public_key_b64": self.public_key_b64,
            "signing_key_id": self.signing_key_id,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def _require_crypto() -> None:
    if not HAS_CRYPTOGRAPHY:
        raise ImportError(
            "cryptography 패키지가 필요합니다.\n"
            "설치: pip install 'cryptography>=42.0'\n"
            "(KOLAS 감사 추적용 Ed25519 서명에 필수)"
        )


def generate_keypair() -> tuple[bytes, bytes]:
    """새로운 Ed25519 키페어 생성.

    Returns:
        (private_key_bytes, public_key_bytes) 튜플.
        둘 다 raw 32바이트.
    """
    _require_crypto()
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_bytes, pub_bytes


def _canonicalize(payload: dict[str, Any]) -> bytes:
    """JSON 정규화 (서명 reproducibility 위해).

    - 키 정렬, ensure_ascii=False, 공백 최소화.
    """
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _digest_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Ed25519Signer:
    """Ed25519 서명자.

    사용:
        priv, pub = generate_keypair()
        signer = Ed25519Signer(priv, pub, key_id="kim-ref-2026-01")
        rec = signer.sign({"y": 0.31356, "uc": 2.0e-4}, record_type="calculation")
        # 검증
        Ed25519Signer.verify(rec)  # True or raises
    """

    def __init__(
        self,
        private_key_bytes: bytes,
        public_key_bytes: bytes,
        key_id: str = "metroai-default",
    ) -> None:
        _require_crypto()
        self._priv = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        self._pub = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        self._pub_bytes = public_key_bytes
        self.key_id = key_id

    def sign(
        self,
        payload: dict[str, Any],
        record_type: str = "calculation",
        record_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SignedRecord:
        """payload 에 디지털 서명을 추가한 SignedRecord 반환."""
        import uuid

        rid = record_id or str(uuid.uuid4())
        ts = datetime.utcnow().isoformat() + "Z"

        # 서명 대상 = payload + record_id + timestamp + record_type
        signing_payload = {
            "record_id": rid,
            "timestamp": ts,
            "record_type": record_type,
            "payload": payload,
        }
        canonical = _canonicalize(signing_payload)
        payload_hash = _digest_hex(canonical)
        sig = self._priv.sign(canonical)

        return SignedRecord(
            record_id=rid,
            timestamp=ts,
            record_type=record_type,
            payload=payload,
            payload_sha256=payload_hash,
            signature_b64=base64.b64encode(sig).decode("ascii"),
            public_key_b64=base64.b64encode(self._pub_bytes).decode("ascii"),
            signing_key_id=self.key_id,
            metadata=metadata or {},
        )

    @staticmethod
    def verify(record: SignedRecord) -> bool:
        """레코드 서명 검증.

        Returns:
            True 시 검증 성공.
        Raises:
            SignatureVerificationError: 검증 실패.
        """
        _require_crypto()
        pub_bytes = base64.b64decode(record.public_key_b64)
        sig = base64.b64decode(record.signature_b64)

        signing_payload = {
            "record_id": record.record_id,
            "timestamp": record.timestamp,
            "record_type": record.record_type,
            "payload": record.payload,
        }
        canonical = _canonicalize(signing_payload)

        # 해시 정합성 사전 체크
        expected_hash = _digest_hex(canonical)
        if expected_hash != record.payload_sha256:
            raise SignatureVerificationError(
                f"Payload hash mismatch: stored={record.payload_sha256[:16]}... "
                f"recomputed={expected_hash[:16]}..."
            )

        try:
            pub = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub.verify(sig, canonical)
            return True
        except Exception as e:  # InvalidSignature
            raise SignatureVerificationError(f"Ed25519 verify failed: {e}") from e
