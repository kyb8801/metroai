"""PROV-O 프로비넌스 모듈 — W3C provenance graph.

각 계산·예측·SOP 변경에 대해 입력·모델·출력의 lineage 를 추적.
KOLAS 정기심사 시 'AI 출력이 어떤 입력·모델로부터 도출되었는지'
명시할 수 있어야 함.

표준: W3C PROV-O (https://www.w3.org/TR/prov-o/)
경량 구현 (rdflib 없이 dict 기반) — 추후 rdflib 풀 통합 가능.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


PROV_NAMESPACE = "http://www.w3.org/ns/prov#"
METROAI_NAMESPACE = "https://metroai.kr/ns/v1#"


@dataclass
class ProvenanceRecord:
    """PROV-O 호환 프로비넌스 레코드.

    Core PROV-O classes mapped to dict structure:
      - Entity: 데이터·문서·결과
      - Activity: 계산·예측·서명 행위
      - Agent: 사용자·소프트웨어·기관

    Core relations:
      - wasGeneratedBy: Entity → Activity
      - used: Activity → Entity
      - wasAssociatedWith: Activity → Agent
      - wasAttributedTo: Entity → Agent
      - wasDerivedFrom: Entity → Entity
    """

    activity_id: str
    activity_label: str  # 예: "GUM uncertainty calculation"
    activity_type: str  # 예: "uncertainty_calculation"
    started_at: str
    ended_at: str

    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    """ entity_id → {label, type, value_summary, hash} """

    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    """ agent_id → {label, type, version} """

    relations: list[dict[str, Any]] = field(default_factory=list)
    """ [{type: 'used'|'wasGeneratedBy'|..., source, target}] """

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "activity_label": self.activity_label,
            "activity_type": self.activity_type,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "entities": self.entities,
            "agents": self.agents,
            "relations": self.relations,
            "metadata": self.metadata,
        }


def build_calculation_provenance(
    *,
    activity_label: str,
    activity_type: str = "uncertainty_calculation",
    inputs: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    model_expression: str | None = None,
    standard_refs: list[str] | None = None,
    user_agent: str | None = None,
    software_agent: str = "metroai/0.6.0",
    started_at: str | None = None,
    ended_at: str | None = None,
) -> ProvenanceRecord:
    """GUM/MCM 계산을 위한 표준 프로비넌스 그래프 생성.

    Returns:
        ProvenanceRecord — 즉시 JSON-LD 직렬화 가능.
    """
    import hashlib
    import json

    now = datetime.utcnow().isoformat() + "Z"
    started_at = started_at or now
    ended_at = ended_at or now

    activity_id = str(uuid.uuid4())
    rec = ProvenanceRecord(
        activity_id=activity_id,
        activity_label=activity_label,
        activity_type=activity_type,
        started_at=started_at,
        ended_at=ended_at,
    )

    # Agents
    sw_id = f"agent:{software_agent}"
    rec.agents[sw_id] = {
        "label": software_agent,
        "type": "SoftwareAgent",
        "version": software_agent.split("/")[-1] if "/" in software_agent else "?",
    }
    rec.relations.append({"type": "wasAssociatedWith", "activity": activity_id, "agent": sw_id})

    if user_agent:
        u_id = f"agent:user:{user_agent}"
        rec.agents[u_id] = {"label": user_agent, "type": "Person"}
        rec.relations.append({"type": "wasAssociatedWith", "activity": activity_id, "agent": u_id})

    # Input entities
    if inputs:
        canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()
        h = hashlib.sha256(canonical).hexdigest()
        in_id = f"entity:input:{h[:12]}"
        rec.entities[in_id] = {
            "label": "Calculation inputs",
            "type": "InputData",
            "hash_sha256": h,
            "summary_keys": sorted(inputs.keys()) if isinstance(inputs, dict) else None,
        }
        rec.relations.append({"type": "used", "activity": activity_id, "entity": in_id})

    # Model entity
    if model_expression:
        m_id = f"entity:model:{abs(hash(model_expression)) % 10**10}"
        rec.entities[m_id] = {
            "label": "Measurement model",
            "type": "MeasurementModel",
            "expression": model_expression,
        }
        rec.relations.append({"type": "used", "activity": activity_id, "entity": m_id})

    # Standards as entities
    for std in standard_refs or []:
        s_id = f"entity:standard:{std.replace(' ', '_')}"
        rec.entities[s_id] = {"label": std, "type": "Standard"}
        rec.relations.append({"type": "used", "activity": activity_id, "entity": s_id})

    # Output entity
    if output:
        canonical = json.dumps(output, sort_keys=True, ensure_ascii=False, default=str).encode()
        h = hashlib.sha256(canonical).hexdigest()
        out_id = f"entity:output:{h[:12]}"
        rec.entities[out_id] = {
            "label": "Calculation result",
            "type": "OutputResult",
            "hash_sha256": h,
            "summary_keys": sorted(output.keys()) if isinstance(output, dict) else None,
        }
        rec.relations.append({"type": "wasGeneratedBy", "entity": out_id, "activity": activity_id})

        # Output derived from input
        if inputs:
            rec.relations.append({
                "type": "wasDerivedFrom",
                "generated_entity": out_id,
                "used_entity": in_id,
            })

    return rec


def serialize_provenance_jsonld(rec: ProvenanceRecord) -> dict[str, Any]:
    """ProvenanceRecord 를 JSON-LD (PROV-O context) 로 직렬화.

    Returns:
        JSON-LD 호환 dict. json.dumps() 로 직렬화 가능.
    """
    context = {
        "@vocab": METROAI_NAMESPACE,
        "prov": PROV_NAMESPACE,
        "Activity": "prov:Activity",
        "Entity": "prov:Entity",
        "Agent": "prov:Agent",
        "used": "prov:used",
        "wasGeneratedBy": "prov:wasGeneratedBy",
        "wasAssociatedWith": "prov:wasAssociatedWith",
        "wasAttributedTo": "prov:wasAttributedTo",
        "wasDerivedFrom": "prov:wasDerivedFrom",
        "startedAtTime": "prov:startedAtTime",
        "endedAtTime": "prov:endedAtTime",
    }

    activity = {
        "@id": f"metroai:activity:{rec.activity_id}",
        "@type": "Activity",
        "label": rec.activity_label,
        "activityType": rec.activity_type,
        "startedAtTime": rec.started_at,
        "endedAtTime": rec.ended_at,
    }

    entities = [
        {"@id": f"metroai:{eid}", "@type": "Entity", **edata}
        for eid, edata in rec.entities.items()
    ]
    agents = [
        {"@id": f"metroai:{aid}", "@type": "Agent", **adata}
        for aid, adata in rec.agents.items()
    ]

    return {
        "@context": context,
        "@graph": [activity, *entities, *agents] + rec.relations,
        "metroai:metadata": rec.metadata,
    }
