"""Pydantic v2 입력 검증 스키마.

박수연(MetroAI advisor) 통합 — v0.6.0 신규 모듈.

MCP 도구·FastAPI 백엔드·Streamlit 폼 모두 동일 스키마를 사용하여
'한 곳에서 검증, 모든 곳에서 신뢰' 원칙을 유지한다.

주요 스키마:
  - DistributionEnum: 분포 enum
  - UncertaintySourceInput: 불확도 성분 입력
  - CalculateUncertaintyRequest: GUM 계산 요청
  - PTAnalysisRequest: 프로피시언시 테스트 분석 요청
  - ReverseUncertaintyRequest: 역설계 요청
  - AgentRunRequest: 6-agent 실행 요청
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    # Fallback — dummy base so imports don't fail
    BaseModel = object  # type: ignore[assignment, misc]
    Field = lambda *a, **kw: None  # type: ignore[assignment]
    field_validator = lambda *a, **kw: (lambda f: f)  # type: ignore[assignment]
    model_validator = lambda *a, **kw: (lambda f: f)  # type: ignore[assignment]


# ============================================================
# Enums
# ============================================================

class DistributionEnum(str, Enum):
    """지원 분포."""

    NORMAL = "normal"
    RECTANGULAR = "rectangular"
    TRIANGULAR = "triangular"
    U_SHAPE = "u_shape"
    ARCSINE = "arcsine"


class EvalTypeEnum(str, Enum):
    """A형/B형 불확도 평가."""

    TYPE_A = "A"
    TYPE_B = "B"


class TemplateEnum(str, Enum):
    """지원 템플릿."""

    # v0.5.0
    GAUGE_BLOCK = "gauge_block"
    MASS = "mass"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    DC_VOLTAGE = "dc_voltage"
    # v0.6.0 신규
    TEM_LATTICE = "tem_lattice"
    SEM_EDS = "sem_eds"
    AFM_ROUGHNESS = "afm_roughness"
    OCD_SCATTEROMETRY = "ocd_scatterometry"


class AgentNameEnum(str, Enum):
    """6 에이전트 식별자."""

    SEMI_INTEL = "semi-intel"
    JOB_SCOUT = "job-scout"
    KOLAS_MONITOR = "kolas-monitor"
    KOLAS_AUDIT_PREDICTOR = "kolas-audit-predictor"
    ORCHESTRATOR = "orchestrator"
    SCHEDULE = "schedule"


# ============================================================
# Schemas (Pydantic v2)
# ============================================================

if HAS_PYDANTIC:

    class UncertaintySourceInput(BaseModel):
        """불확도 성분 1개 입력."""

        name: str = Field(..., min_length=1, max_length=200, description="성분 이름")
        symbol: str = Field(..., min_length=1, max_length=50, description="수학 기호")
        eval_type: EvalTypeEnum = EvalTypeEnum.TYPE_B
        value: float = Field(0.0, description="입력량 추정값")
        distribution: DistributionEnum = DistributionEnum.NORMAL
        std_uncertainty: Optional[float] = Field(None, ge=0)
        half_width: Optional[float] = Field(None, ge=0)
        expanded_uncertainty: Optional[float] = Field(None, ge=0)
        coverage_factor: Optional[float] = Field(None, gt=0)
        repeat_data: Optional[list[float]] = None
        unit: str = ""

        @field_validator("repeat_data")
        @classmethod
        def repeat_data_min_length(cls, v: Optional[list[float]]) -> Optional[list[float]]:
            if v is not None and len(v) < 2:
                raise ValueError("repeat_data는 최소 2개 이상의 반복 측정값이 필요합니다.")
            return v

        @model_validator(mode="after")
        def consistency(self) -> "UncertaintySourceInput":
            """A형은 repeat_data 또는 std_uncertainty 중 하나 필수."""
            if self.eval_type == EvalTypeEnum.TYPE_A:
                if self.repeat_data is None and self.std_uncertainty is None:
                    raise ValueError(
                        f"성분 '{self.name}': A형 평가는 repeat_data 또는 std_uncertainty 가 필요합니다."
                    )
            return self


    class CalculateUncertaintyRequest(BaseModel):
        """GUM 불확도 계산 요청 (MCP 도구 입력)."""

        template: Optional[TemplateEnum] = Field(
            None, description="템플릿 사용 시. 미지정 시 model_expression+sources 필수."
        )
        template_kwargs: dict[str, Any] = Field(default_factory=dict)

        # 직접 모드 (템플릿 없이)
        model_expression: Optional[str] = Field(None, description="Sympy parseable expression")
        sources: list[UncertaintySourceInput] = Field(default_factory=list)
        measurand_name: str = "Y"
        measurand_unit: str = ""
        confidence_level: float = Field(0.9545, ge=0.5, le=0.9999)

        @model_validator(mode="after")
        def either_template_or_direct(self) -> "CalculateUncertaintyRequest":
            if self.template is None and (not self.model_expression or not self.sources):
                raise ValueError(
                    "template 또는 (model_expression + sources) 중 하나는 필수입니다."
                )
            return self


    class PTAnalysisRequest(BaseModel):
        """프로피시언시 테스트 분석 요청 (ISO 13528·17043)."""

        lab_value: float = Field(..., description="우리 측정값")
        assigned_value: float = Field(..., description="기준값 (PT provider)")
        sigma_pt: Optional[float] = Field(None, gt=0, description="z-score 용")
        u_lab: Optional[float] = Field(None, ge=0, description="우리 확장불확도")
        u_ref: Optional[float] = Field(None, ge=0, description="기준값 확장불확도")
        units: str = ""

        @model_validator(mode="after")
        def at_least_one_metric(self) -> "PTAnalysisRequest":
            if self.sigma_pt is None and (self.u_lab is None or self.u_ref is None):
                raise ValueError(
                    "z-score(sigma_pt) 또는 En/zeta(u_lab + u_ref) 중 하나는 필수입니다."
                )
            return self


    class ReverseUncertaintyRequest(BaseModel):
        """불확도 역설계 요청."""

        model_expression: str = Field(..., min_length=1)
        symbols: list[str] = Field(..., min_length=1)
        current_values: dict[str, float] = Field(default_factory=dict)
        current_uncertainties: dict[str, Optional[float]] = Field(default_factory=dict)
        target_U: float = Field(..., gt=0)
        target_k: float = Field(2.0, gt=0)
        allocation: str = Field("equal", pattern="^(equal|weighted_by_sensitivity)$")


    class AgentRunRequest(BaseModel):
        """6-agent 단일 실행 요청."""

        agent: AgentNameEnum
        context: dict[str, Any] = Field(default_factory=dict)


    class AgentRunResponse(BaseModel):
        """에이전트 실행 응답 (FastAPI/MCP 표준 출력)."""

        agent_name: str
        status: str  # "ok" / "stale" / "error" / "disabled"
        timestamp: str
        latest_output: str
        payload: dict[str, Any] = Field(default_factory=dict)
        ai_confidence: Optional[float] = None
        powered_by_ai: bool = False

else:
    # Pydantic 미설치 시 — 빈 stub class
    class UncertaintySourceInput:  # type: ignore[no-redef]
        pass

    class CalculateUncertaintyRequest:  # type: ignore[no-redef]
        pass

    class PTAnalysisRequest:  # type: ignore[no-redef]
        pass

    class ReverseUncertaintyRequest:  # type: ignore[no-redef]
        pass

    class AgentRunRequest:  # type: ignore[no-redef]
        pass

    class AgentRunResponse:  # type: ignore[no-redef]
        pass


__all__ = [
    "DistributionEnum",
    "EvalTypeEnum",
    "TemplateEnum",
    "AgentNameEnum",
    "UncertaintySourceInput",
    "CalculateUncertaintyRequest",
    "PTAnalysisRequest",
    "ReverseUncertaintyRequest",
    "AgentRunRequest",
    "AgentRunResponse",
    "HAS_PYDANTIC",
]
