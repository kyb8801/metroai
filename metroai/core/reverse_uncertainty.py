"""불확도 역설계 엔진 (Reverse Uncertainty Engineering).

목표 확장불확도(U_target)를 달성하기 위해
각 불확도 성분이 만족해야 하는 최대 허용 표준불확도를 산출한다.

세계 최초 기능 — GUM Workbench 등 기존 소프트웨어에 없음.

활용 시나리오:
    - KOLAS 신규 인정 신청: "CMC를 X로 주장하려면 어떤 조건이 필요한가?"
    - 장비 교체 의사결정: "이 표준기로 목표 CMC를 달성할 수 있는가?"
    - 불확도 예산 최적화: "어떤 성분을 줄여야 가장 효과적인가?"
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.stats import t as t_dist


@dataclass
class ComponentBudget:
    """역설계 결과의 개별 성분."""

    name: str
    symbol: str
    sensitivity_coeff: float  # ci = ∂f/∂xi
    current_std_uncertainty: Optional[float]  # 현재 u(xi), 없으면 None
    max_allowed_std_uncertainty: float  # 허용 최대 u(xi)
    max_allowed_half_width_rect: float  # 균일분포 가정 시 허용 반폭 a
    max_allowed_expanded_U: float  # k=2 기준 허용 확장불확도
    contribution_ratio: float  # 배분 비율 (%)
    is_feasible: bool = True  # 현재값이 허용범위 내인지


@dataclass
class ReverseResult:
    """역설계 전체 결과."""

    target_expanded_uncertainty: float  # U_target
    target_coverage_factor: float  # k
    target_combined_uncertainty: float  # uc_target = U/k
    target_confidence_level: float

    allocation_method: str  # "equal", "weighted", "custom"
    components: list[ComponentBudget] = field(default_factory=list)

    overall_feasible: bool = True  # 모든 성분이 feasible한지
    bottleneck_component: Optional[str] = None  # 가장 빡빡한 성분

    model_expression: str = ""
    measurand_name: str = "Y"
    measurand_unit: str = ""

    def summary(self) -> str:
        """결과 요약 문구."""
        status = "✅ 달성 가능" if self.overall_feasible else "⚠️ 일부 성분 초과"
        return (
            f"목표 U = {self.target_expanded_uncertainty:.4g} {self.measurand_unit} "
            f"(k={self.target_coverage_factor:.2f}) → "
            f"uc ≤ {self.target_combined_uncertainty:.4g} {self.measurand_unit} — {status}"
        )


class ReverseUncertaintyEngine:
    """불확도 역설계 계산기.

    GUM 순방향 공식:
        U = k * sqrt(Σ (ci * u(xi))²)

    역방향: U_target과 k가 주어졌을 때, 각 u(xi)의 허용 최대값을 산출.

    배분 방법:
    1. 균등 배분 (equal): uc² / n 을 각 성분에 동일 배분
       → u(xi)_max = uc_target / (|ci| * sqrt(n))
    2. 가중 배분 (weighted): 현재 기여율 비례 배분
       → 기여율이 높은 성분에 더 많은 예산 할당
    3. 단일 성분 고정 (fix_others): 나머지 고정, 한 성분만 역산
    """

    def __init__(
        self,
        model_expression: str,
        symbol_names: list[str],
        sensitivity_coefficients: dict[str, float],
        measurand_name: str = "Y",
        measurand_unit: str = "",
    ):
        """
        Args:
            model_expression: 측정 모델 수학식 (표시용)
            symbol_names: 입력량 기호 목록
            sensitivity_coefficients: {기호: 민감계수 ci} 딕셔너리
            measurand_name: 측정량 이름
            measurand_unit: 단위
        """
        self.model_expression = model_expression
        self.symbol_names = symbol_names
        self.sensitivities = sensitivity_coefficients
        self.measurand_name = measurand_name
        self.measurand_unit = measurand_unit

    def reverse_equal(
        self,
        target_U: float,
        k: float = 2.0,
        confidence_level: float = 0.9545,
        current_uncertainties: Optional[dict[str, float]] = None,
    ) -> ReverseResult:
        """균등 배분 역설계.

        각 성분에 동일한 분산 예산을 배분:
            u(xi)_max = uc_target / (|ci| * sqrt(n))

        Args:
            target_U: 목표 확장불확도
            k: 포함인자
            confidence_level: 신뢰수준
            current_uncertainties: {기호: 현재 u(xi)} (선택, 비교용)

        Returns:
            ReverseResult
        """
        uc_target = target_U / k
        n = len(self.symbol_names)

        components = []
        all_feasible = True
        worst_margin = float("inf")
        bottleneck = None

        for sym in self.symbol_names:
            ci = self.sensitivities.get(sym, 1.0)
            abs_ci = abs(ci) if abs(ci) > 1e-15 else 1e-15

            # 균등 배분: 각 성분의 허용 분산 = uc² / n
            u_max = uc_target / (abs_ci * math.sqrt(n))

            # 균일분포 반폭 환산: a = u * sqrt(3)
            a_max = u_max * math.sqrt(3)

            # 확장불확도 환산: U = k * u
            U_max = k * u_max

            # 현재값 비교
            current_u = None
            feasible = True
            if current_uncertainties and sym in current_uncertainties:
                current_u = current_uncertainties[sym]
                if current_u > u_max:
                    feasible = False
                    all_feasible = False

                margin = u_max - current_u
                if margin < worst_margin:
                    worst_margin = margin
                    bottleneck = sym

            components.append(ComponentBudget(
                name=sym,
                symbol=sym,
                sensitivity_coeff=ci,
                current_std_uncertainty=current_u,
                max_allowed_std_uncertainty=u_max,
                max_allowed_half_width_rect=a_max,
                max_allowed_expanded_U=U_max,
                contribution_ratio=100.0 / n,
                is_feasible=feasible,
            ))

        return ReverseResult(
            target_expanded_uncertainty=target_U,
            target_coverage_factor=k,
            target_combined_uncertainty=uc_target,
            target_confidence_level=confidence_level,
            allocation_method="equal",
            components=components,
            overall_feasible=all_feasible,
            bottleneck_component=bottleneck,
            model_expression=self.model_expression,
            measurand_name=self.measurand_name,
            measurand_unit=self.measurand_unit,
        )

    def reverse_weighted(
        self,
        target_U: float,
        k: float = 2.0,
        confidence_level: float = 0.9545,
        current_uncertainties: dict[str, float] = None,
        weights: Optional[dict[str, float]] = None,
    ) -> ReverseResult:
        """가중 배분 역설계.

        현재 기여율 비례로 배분하거나, 사용자 지정 가중치 사용.
        기여율이 큰 성분에 더 많은 예산을 배분하여 현실적인 결과를 도출.

        Args:
            target_U: 목표 확장불확도
            k: 포함인자
            confidence_level: 신뢰수준
            current_uncertainties: {기호: 현재 u(xi)} — 가중치 계산용
            weights: {기호: 가중치(0~1)} — 지정 시 current_uncertainties 대신 사용

        Returns:
            ReverseResult
        """
        uc_target = target_U / k
        n = len(self.symbol_names)

        # 가중치 결정
        if weights is None and current_uncertainties:
            # 현재 기여도(ci² * u²) 기반 가중치
            total_var = 0.0
            var_contributions = {}
            for sym in self.symbol_names:
                ci = self.sensitivities.get(sym, 1.0)
                u_i = current_uncertainties.get(sym, 0.0)
                var_i = (ci * u_i) ** 2
                var_contributions[sym] = var_i
                total_var += var_i

            if total_var > 0:
                weights = {sym: var_contributions[sym] / total_var for sym in self.symbol_names}
            else:
                weights = {sym: 1.0 / n for sym in self.symbol_names}
        elif weights is None:
            weights = {sym: 1.0 / n for sym in self.symbol_names}

        # 가중치 정규화
        w_sum = sum(weights.values())
        if w_sum > 0:
            weights = {sym: w / w_sum for sym, w in weights.items()}

        components = []
        all_feasible = True
        worst_margin = float("inf")
        bottleneck = None

        for sym in self.symbol_names:
            ci = self.sensitivities.get(sym, 1.0)
            abs_ci = abs(ci) if abs(ci) > 1e-15 else 1e-15
            w_i = weights.get(sym, 1.0 / n)

            # 가중 배분: 성분 i의 허용 분산 = w_i * uc²
            # (ci * u_max_i)² = w_i * uc²
            # u_max_i = sqrt(w_i) * uc / |ci|
            u_max = math.sqrt(w_i) * uc_target / abs_ci

            a_max = u_max * math.sqrt(3)
            U_max = k * u_max

            current_u = None
            feasible = True
            if current_uncertainties and sym in current_uncertainties:
                current_u = current_uncertainties[sym]
                if current_u > u_max:
                    feasible = False
                    all_feasible = False

                margin = u_max - current_u
                if margin < worst_margin:
                    worst_margin = margin
                    bottleneck = sym

            components.append(ComponentBudget(
                name=sym,
                symbol=sym,
                sensitivity_coeff=ci,
                current_std_uncertainty=current_u,
                max_allowed_std_uncertainty=u_max,
                max_allowed_half_width_rect=a_max,
                max_allowed_expanded_U=U_max,
                contribution_ratio=w_i * 100.0,
                is_feasible=feasible,
            ))

        return ReverseResult(
            target_expanded_uncertainty=target_U,
            target_coverage_factor=k,
            target_combined_uncertainty=uc_target,
            target_confidence_level=confidence_level,
            allocation_method="weighted",
            components=components,
            overall_feasible=all_feasible,
            bottleneck_component=bottleneck,
            model_expression=self.model_expression,
            measurand_name=self.measurand_name,
            measurand_unit=self.measurand_unit,
        )

    def reverse_single_component(
        self,
        target_U: float,
        target_symbol: str,
        fixed_uncertainties: dict[str, float],
        k: float = 2.0,
        confidence_level: float = 0.9545,
    ) -> ReverseResult:
        """단일 성분 역산.

        다른 모든 성분을 고정하고, 특정 성분만의 허용 최대값을 산출.

        활용: "표준기 불확도가 X인 상태에서, 반복성은 얼마까지 허용되는가?"

        Args:
            target_U: 목표 확장불확도
            target_symbol: 역산할 성분 기호
            fixed_uncertainties: {기호: 고정된 u(xi)} — target_symbol 제외
            k: 포함인자
            confidence_level: 신뢰수준

        Returns:
            ReverseResult
        """
        uc_target = target_U / k

        # 고정 성분의 총 분산
        fixed_variance = 0.0
        for sym in self.symbol_names:
            if sym == target_symbol:
                continue
            ci = self.sensitivities.get(sym, 1.0)
            u_i = fixed_uncertainties.get(sym, 0.0)
            fixed_variance += (ci * u_i) ** 2

        # 목표 성분의 허용 분산
        target_variance = uc_target ** 2 - fixed_variance

        if target_variance <= 0:
            # 고정 성분만으로 이미 목표 초과 — 불가능
            ci_target = self.sensitivities.get(target_symbol, 1.0)
            components = []
            for sym in self.symbol_names:
                ci = self.sensitivities.get(sym, 1.0)
                current_u = fixed_uncertainties.get(sym, 0.0)
                components.append(ComponentBudget(
                    name=sym,
                    symbol=sym,
                    sensitivity_coeff=ci,
                    current_std_uncertainty=current_u,
                    max_allowed_std_uncertainty=0.0 if sym == target_symbol else current_u,
                    max_allowed_half_width_rect=0.0,
                    max_allowed_expanded_U=0.0,
                    contribution_ratio=0.0,
                    is_feasible=False if sym == target_symbol else True,
                ))

            return ReverseResult(
                target_expanded_uncertainty=target_U,
                target_coverage_factor=k,
                target_combined_uncertainty=uc_target,
                target_confidence_level=confidence_level,
                allocation_method="single_component",
                components=components,
                overall_feasible=False,
                bottleneck_component=target_symbol,
                model_expression=self.model_expression,
                measurand_name=self.measurand_name,
                measurand_unit=self.measurand_unit,
            )

        ci_target = self.sensitivities.get(target_symbol, 1.0)
        abs_ci = abs(ci_target) if abs(ci_target) > 1e-15 else 1e-15

        u_max_target = math.sqrt(target_variance) / abs_ci
        a_max_target = u_max_target * math.sqrt(3)
        U_max_target = k * u_max_target

        components = []
        for sym in self.symbol_names:
            ci = self.sensitivities.get(sym, 1.0)
            if sym == target_symbol:
                components.append(ComponentBudget(
                    name=sym,
                    symbol=sym,
                    sensitivity_coeff=ci,
                    current_std_uncertainty=fixed_uncertainties.get(sym),
                    max_allowed_std_uncertainty=u_max_target,
                    max_allowed_half_width_rect=a_max_target,
                    max_allowed_expanded_U=U_max_target,
                    contribution_ratio=(target_variance / uc_target ** 2) * 100,
                    is_feasible=True,
                ))
            else:
                current_u = fixed_uncertainties.get(sym, 0.0)
                var_i = (ci * current_u) ** 2
                components.append(ComponentBudget(
                    name=sym,
                    symbol=sym,
                    sensitivity_coeff=ci,
                    current_std_uncertainty=current_u,
                    max_allowed_std_uncertainty=current_u,
                    max_allowed_half_width_rect=current_u * math.sqrt(3),
                    max_allowed_expanded_U=k * current_u,
                    contribution_ratio=(var_i / uc_target ** 2) * 100 if uc_target > 0 else 0,
                    is_feasible=True,
                ))

        return ReverseResult(
            target_expanded_uncertainty=target_U,
            target_coverage_factor=k,
            target_combined_uncertainty=uc_target,
            target_confidence_level=confidence_level,
            allocation_method="single_component",
            components=components,
            overall_feasible=True,
            bottleneck_component=None,
            model_expression=self.model_expression,
            measurand_name=self.measurand_name,
            measurand_unit=self.measurand_unit,
        )
