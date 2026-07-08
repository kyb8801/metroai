"""GUM 불확도 전파 엔진.

ISO GUM (Guide to the Expression of Uncertainty in Measurement)에 따른
합성불확도, Welch-Satterthwaite 유효자유도, 확장불확도 계산.

KOLAS-G-002 "측정결과의 불확도 추정 및 표현을 위한 지침" 준거.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from scipy.stats import t as t_dist

from .distributions import UncertaintySource
from .model import MeasurementModel


@dataclass
class UncertaintyComponent:
    """불확도 예산표의 한 행 (계산 결과)."""

    source: UncertaintySource
    std_uncertainty: float  # u(xi)
    sensitivity_coeff: float  # ci = ∂f/∂xi
    contribution: float  # |ci| * u(xi)
    contribution_sq: float  # ci² * u(xi)²
    dof: float  # νi
    percent_contribution: float = 0.0  # 기여율 (%)


@dataclass
class GUMResult:
    """GUM 불확도 계산 전체 결과."""

    # 측정 결과
    measurand_value: float  # y = f(x1, x2, ..., xn)
    measurand_name: str = "Y"
    measurand_unit: str = ""

    # 합성불확도
    combined_uncertainty: float = 0.0  # uc(y)

    # Welch-Satterthwaite
    effective_dof: float = float("inf")  # νeff

    # 포함인자 & 확장불확도
    confidence_level: float = 0.9545  # 신뢰수준 (기본 95.45%)
    coverage_factor: float = 2.0  # k
    expanded_uncertainty: float = 0.0  # U = k * uc

    # 불확도 예산표
    components: list[UncertaintyComponent] = field(default_factory=list)

    # 모델 정보
    model_expression: str = ""
    model_latex: str = ""

    def uncertainty_statement(self) -> str:
        """KOLAS 양식 불확도 표현 문구 생성.

        Returns:
            예: "Y = 100.0023 mm ± 0.0012 mm (k = 2.00, 신뢰수준 약 95 %)"
        """
        conf_pct = self.confidence_level * 100
        unit_str = f" {self.measurand_unit}" if self.measurand_unit else ""
        return (
            f"{self.measurand_name} = {self.measurand_value:.6g}{unit_str}"
            f" ± {self.expanded_uncertainty:.4g}{unit_str}"
            f" (k = {self.coverage_factor:.2f}, 신뢰수준 약 {conf_pct:.0f} %)"
        )


class GUMCalculator:
    """GUM 불확도 전파 계산기.

    사용법:
        model = MeasurementModel("L0 + dL + alpha * L0 * dT", ["L0", "dL", "alpha", "dT"])
        sources = [UncertaintySource(...), ...]
        calc = GUMCalculator(model, sources)
        result = calc.calculate()
    """

    def __init__(
        self,
        model: MeasurementModel,
        sources: list[UncertaintySource],
        confidence_level: float = 0.9545,
        measurand_name: str = "Y",
        measurand_unit: str = "",
    ):
        self.model = model
        self.sources = sources
        self.confidence_level = confidence_level
        self.measurand_name = measurand_name
        self.measurand_unit = measurand_unit

    def calculate(self) -> GUMResult:
        """GUM 불확도 계산 전체 실행.

        순서:
        1. 측정 모델 파싱 + 편미분 계산
        2. 각 불확도 성분의 표준불확도 계산
        3. 민감계수 수치 평가
        4. 합성불확도 uc 계산
        5. Welch-Satterthwaite 유효자유도 계산
        6. 포함인자 k 결정 (t-분포)
        7. 확장불확도 U 계산

        Returns:
            GUMResult 객체
        """
        # Step 1: 모델 파싱 + 편미분
        self.model.parse()
        self.model.compute_sensitivities()

        # 입력값 딕셔너리 구성
        input_values = {src.symbol: src.value for src in self.sources}

        # Step 2-3: 각 성분 계산
        components: list[UncertaintyComponent] = []
        variance_sum = 0.0

        for src in self.sources:
            # 표준불확도 계산
            u_i, nu_i = src.compute()

            # 민감계수 계산
            c_i = self.model.evaluate_sensitivity(src.symbol, input_values)

            # 기여도
            contribution = abs(c_i) * u_i
            contribution_sq = (c_i * u_i) ** 2
            variance_sum += contribution_sq

            components.append(
                UncertaintyComponent(
                    source=src,
                    std_uncertainty=u_i,
                    sensitivity_coeff=c_i,
                    contribution=contribution,
                    contribution_sq=contribution_sq,
                    dof=nu_i,
                )
            )

        # Step 4: 합성불확도
        uc = math.sqrt(variance_sum) if variance_sum > 0 else 0.0

        # 기여율 계산
        for comp in components:
            if variance_sum > 0:
                comp.percent_contribution = (comp.contribution_sq / variance_sum) * 100

        # Step 5: Welch-Satterthwaite 유효자유도
        nu_eff = self._welch_satterthwaite(components, uc)

        # Step 6: 포함인자 k
        k = self._coverage_factor(nu_eff, self.confidence_level)

        # Step 7: 확장불확도
        U = k * uc

        # 측정값
        y = self.model.evaluate(input_values)

        return GUMResult(
            measurand_value=y,
            measurand_name=self.measurand_name,
            measurand_unit=self.measurand_unit,
            combined_uncertainty=uc,
            effective_dof=nu_eff,
            confidence_level=self.confidence_level,
            coverage_factor=k,
            expanded_uncertainty=U,
            components=components,
            model_expression=self.model.expression_str,
            model_latex=self.model.get_latex(),
        )

    @staticmethod
    def _welch_satterthwaite(
        components: list[UncertaintyComponent], uc: float
    ) -> float:
        """Welch-Satterthwaite 유효자유도 계산.

        ν_eff = uc⁴(y) / Σ[(ci · u(xi))⁴ / νi]

        무한 자유도(B형, ν=∞)인 성분은 분모에 기여하지 않음.

        Args:
            components: 불확도 성분 목록
            uc: 합성불확도

        Returns:
            유효자유도 νeff (최소 1, 최대 inf)
        """
        if uc == 0:
            return float("inf")

        uc4 = uc**4
        denominator = 0.0

        for comp in components:
            if math.isinf(comp.dof):
                # B형 성분 (ν=∞)은 분모에 기여하지 않음
                continue
            if comp.dof <= 0:
                continue

            ci_ui_4 = comp.contribution_sq**2  # (ci * u(xi))^4 = ((ci*u(xi))^2)^2
            denominator += ci_ui_4 / comp.dof

        if denominator == 0:
            return float("inf")

        nu_eff = uc4 / denominator

        # GUM에 따라 νeff를 정수로 내림 (보수적)
        nu_eff = math.floor(nu_eff)

        # 최소 1
        return max(1.0, float(nu_eff))

    @staticmethod
    def _coverage_factor(nu_eff: float, confidence_level: float = 0.9545) -> float:
        """포함인자 k 결정.

        유효자유도가 유한하면 t-분포, 무한이면 정규분포 사용.

        Args:
            nu_eff: 유효자유도
            confidence_level: 신뢰수준 (기본 0.9545 ≈ 95.45%)

        Returns:
            포함인자 k
        """
        # 신뢰수준을 양측 확률로 변환
        p = (1 + confidence_level) / 2

        if math.isinf(nu_eff) or nu_eff > 1000:
            # 정규분포 근사 (ν > 1000이면 사실상 정규분포)
            from scipy.stats import norm

            return float(norm.ppf(p))
        else:
            # t-분포
            return float(t_dist.ppf(p, df=nu_eff))
