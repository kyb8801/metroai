"""v0.6.0 신규 모듈 통합 테스트.

박수연(MetroAI advisor) 통합 — 모든 신규 모듈을 한 파일에서 검증.

테스트 대상:
  - metroai.exceptions
  - metroai.templates (TEM/SEM-EDS/AFM/OCD 신규 4종)
  - metroai.agents (6 백본)
  - metroai.audit (Ed25519 + PROV-O)
  - metroai.schemas (Pydantic v2)
  - metroai.math (Sobol QMC)
"""

from __future__ import annotations

import math

import numpy as np
import pytest


# ============================================================
# 1. exceptions
# ============================================================

def test_exceptions_hierarchy():
    from metroai.exceptions import (
        MetroAIError, UserInputError, InvalidDistributionError,
        DomainError, IllPosedInverseError, MathError, ConvergenceError,
        InfraError, ExportError,
    )
    # MRO 검증
    assert issubclass(UserInputError, MetroAIError)
    assert issubclass(InvalidDistributionError, UserInputError)
    assert issubclass(IllPosedInverseError, DomainError)
    assert issubclass(ConvergenceError, MathError)


def test_invalid_distribution_message():
    from metroai.exceptions import InvalidDistributionError
    with pytest.raises(InvalidDistributionError) as exc_info:
        raise InvalidDistributionError("weird_dist")
    assert "weird_dist" in str(exc_info.value)
    assert "normal" in str(exc_info.value)  # supported list 포함


# ============================================================
# 2. templates (v0.6.0 신규 4종)
# ============================================================

@pytest.mark.parametrize("template_factory_name", [
    "create_tem_lattice_template",
    "create_sem_eds_template",
    "create_afm_roughness_template",
    "create_ocd_scatterometry_template",
])
def test_v06_template_constructs(template_factory_name):
    import metroai.templates as tpl
    factory = getattr(tpl, template_factory_name)
    model, sources, config = factory()
    # 최소 4개 불확도 성분
    assert len(sources) >= 4
    # config 필수 키
    assert "template_name" in config
    assert "measurand_name" in config
    assert "measurand_unit" in config


def test_tem_lattice_calculator_runs():
    from metroai.templates import create_tem_lattice_calculator
    calc = create_tem_lattice_calculator()
    r = calc.calculate()
    # uc 와 U 가 양수
    assert r.combined_uncertainty > 0
    assert r.expanded_uncertainty > 0
    # k 가 2 근처
    assert 1.9 < r.coverage_factor < 3.0


def test_sem_eds_calculator_runs():
    from metroai.templates import create_sem_eds_calculator
    calc = create_sem_eds_calculator()
    r = calc.calculate()
    assert r.combined_uncertainty > 0
    # 5개 성분
    assert len(r.components) == 5


def test_afm_roughness_calculator_runs():
    from metroai.templates import create_afm_roughness_calculator
    calc = create_afm_roughness_calculator(parameter="Sa")
    r = calc.calculate()
    assert r.combined_uncertainty > 0


def test_ocd_scatterometry_calculator_runs():
    from metroai.templates import create_ocd_scatterometry_calculator
    calc = create_ocd_scatterometry_calculator()
    r = calc.calculate()
    assert r.combined_uncertainty > 0


# ============================================================
# 3. agents (6 백본)
# ============================================================

def test_all_agents_have_distinct_names():
    from metroai.agents import all_agents
    names = [a.name for a in all_agents()]
    assert len(names) == 6
    assert len(set(names)) == 6


@pytest.mark.parametrize("agent_idx", range(6))
def test_each_agent_runs(agent_idx):
    from metroai.agents import all_agents
    from metroai.agents.base import AgentResult, AgentStatus
    a = all_agents()[agent_idx]
    r = a.run({})
    assert isinstance(r, AgentResult)
    assert r.agent_name == a.name
    assert r.status in (AgentStatus.OK, AgentStatus.STALE, AgentStatus.ERROR,
                        AgentStatus.DISABLED)
    assert r.latest_output  # non-empty


def test_orchestrator_integrates_sub_agents():
    from metroai.agents import all_agents, OrchestratorAgent
    sub = {a.name: a.run({}) for a in all_agents()
           if a.name != "orchestrator"}
    orch = OrchestratorAgent().run({"agent_results": sub})
    assert orch.payload["task_count"] >= 1
    # P0 작업이 최소 하나 (schedule + audit-predictor 결합)
    p0_count = sum(1 for t in orch.payload["tasks"] if t["priority"] == "P0")
    assert p0_count >= 1


def test_kolas_audit_predictor_risk_within_range():
    from metroai.agents import KolasAuditPredictorAgent
    r = KolasAuditPredictorAgent().run({
        "sop_completeness": 0.95,
        "months_since_last_audit": 3.0,
        "personnel_turnover_signal": 0.05,
        "recent_nonconformities": 0,
    })
    risk = r.payload["risk_score"]
    assert 0.0 <= risk <= 1.0
    # 우호적 입력 → 낮은 위험
    assert risk < 0.35


# ============================================================
# 4. audit (Ed25519 + PROV-O)
# ============================================================

def test_ed25519_sign_verify_roundtrip():
    from metroai.audit import Ed25519Signer, generate_keypair
    priv, pub = generate_keypair()
    assert len(priv) == 32
    assert len(pub) == 32
    signer = Ed25519Signer(priv, pub, key_id="test-key")
    rec = signer.sign({"y": 0.31356, "uc": 2.0e-4}, "calculation")
    assert Ed25519Signer.verify(rec) is True


def test_ed25519_tamper_detected():
    from metroai.audit import (
        Ed25519Signer, generate_keypair, SignatureVerificationError,
    )
    priv, pub = generate_keypair()
    rec = Ed25519Signer(priv, pub).sign({"y": 1.0}, "test")
    # 변조
    rec.payload["y"] = 999.0
    with pytest.raises(SignatureVerificationError):
        Ed25519Signer.verify(rec)


def test_provenance_graph_has_required_relations():
    from metroai.audit import build_calculation_provenance, serialize_provenance_jsonld
    prov = build_calculation_provenance(
        activity_label="test",
        inputs={"x": 1.0, "y": 2.0},
        output={"result": 3.0},
        model_expression="x + y",
        standard_refs=["ISO/IEC 17025"],
        user_agent="tester",
    )
    rel_types = {r["type"] for r in prov.relations}
    assert "wasGeneratedBy" in rel_types
    assert "used" in rel_types
    assert "wasAssociatedWith" in rel_types
    assert "wasDerivedFrom" in rel_types

    jsonld = serialize_provenance_jsonld(prov)
    assert "@context" in jsonld
    assert "@graph" in jsonld


# ============================================================
# 5. schemas (Pydantic v2)
# ============================================================

def test_pydantic_available():
    from metroai.schemas import HAS_PYDANTIC
    assert HAS_PYDANTIC


def test_calc_request_template_mode():
    from metroai.schemas import CalculateUncertaintyRequest, TemplateEnum
    req = CalculateUncertaintyRequest(template=TemplateEnum.TEM_LATTICE)
    assert req.template == TemplateEnum.TEM_LATTICE


def test_calc_request_rejects_empty():
    from metroai.schemas import CalculateUncertaintyRequest
    with pytest.raises(Exception):  # pydantic ValidationError
        CalculateUncertaintyRequest()


def test_a_type_source_requires_data():
    from metroai.schemas import UncertaintySourceInput, EvalTypeEnum
    with pytest.raises(Exception):
        UncertaintySourceInput(name="bad", symbol="z", eval_type=EvalTypeEnum.TYPE_A)


# ============================================================
# 6. math (Sobol QMC)
# ============================================================

def test_sobol_sampling_shape():
    from metroai.math import SobolQMC
    qmc = SobolQMC(dim=3, scramble=True, seed=42)
    s = qmc.sample(2 ** 10)
    assert s.shape == (1024, 3)
    assert s.min() >= 0.0
    assert s.max() < 1.0


def test_qmc_matches_gum_analytic_linear_model():
    """y = a + b*x — QMC std 가 GUM 해석해와 ±5% 일치해야 함."""
    from metroai.math import qmc_uncertainty_propagation
    u_x, u_a, u_b = 0.05, 0.01 / math.sqrt(3), 0.005
    expected_u_y = math.sqrt((1.0 * u_x) ** 2 + (1.0 * u_a) ** 2 + (10.0 * u_b) ** 2)

    r = qmc_uncertainty_propagation(
        f=lambda x, a, b: a + b * x,
        input_specs=[
            {"name": "x", "dist": "normal", "value": 10.0, "std": 0.05},
            {"name": "a", "dist": "rectangular", "value": 0.0, "half_width": 0.01},
            {"name": "b", "dist": "normal", "value": 1.0, "std": 0.005},
        ],
        n_samples=2 ** 14,
        seed=42,
    )
    assert abs(r.std - expected_u_y) / expected_u_y < 0.05
    assert r.is_power_of_two
    # CI 가 mean 을 포함
    assert r.coverage_interval[0] < r.mean < r.coverage_interval[1]


def test_distribution_transforms():
    from metroai.math import sample_from_distribution_qmc
    u = np.array([0.25, 0.5, 0.75])
    # rectangular [-1, 1] : 0.25 → -0.5, 0.5 → 0, 0.75 → 0.5
    rect = sample_from_distribution_qmc(u, "rectangular", 0.0, 1.0)
    assert abs(rect[1]) < 1e-9
    # normal: 0.5 → 0 (median)
    normal = sample_from_distribution_qmc(u, "normal", 0.0, 1.0)
    assert abs(normal[1]) < 1e-9
