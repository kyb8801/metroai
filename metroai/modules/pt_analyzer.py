"""숙련도시험(PT: Proficiency Testing) 통계 분석 모듈.

ISO 13528, ISO 17043에 따른 z-score, En number, ζ(제타)-score 계산 및 판정.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class PTResult:
    """숙련도시험 분석 결과."""

    lab_value: float
    assigned_value: float
    cal_point: str = ""
    z_score: Optional[float] = None
    en_number: Optional[float] = None
    zeta_score: Optional[float] = None
    z_judgment: str = ""
    en_judgment: str = ""
    zeta_judgment: str = ""


def _judge_z(value: float) -> str:
    """z-score/ζ-score 판정."""
    abs_val = abs(value)
    if abs_val <= 2.0:
        return "만족"
    elif abs_val < 3.0:
        return "주의"
    else:
        return "불만족"


def _judge_en(value: float) -> str:
    """En number 판정."""
    if abs(value) <= 1.0:
        return "만족"
    else:
        return "불만족"


def calculate_z_score(x: float, X: float, sigma_pt: float) -> tuple[float, str]:
    """z-score 계산 (ISO 13528).

    z = (x - X) / σ_pt

    Args:
        x: 참가기관 측정값
        X: 배정값 (assigned value)
        sigma_pt: 숙련도시험 표준편차

    Returns:
        (z-score, 판정) 튜플
    """
    if sigma_pt <= 0:
        raise ValueError("σ_pt는 양수여야 합니다.")
    z = (x - X) / sigma_pt
    return z, _judge_z(z)


def calculate_en_number(x: float, X_ref: float, U_lab: float, U_ref: float) -> tuple[float, str]:
    """En number 계산 (ISO 17043).

    En = (x - X_ref) / √(U_lab² + U_ref²)

    Args:
        x: 참가기관 측정값
        X_ref: 기준값
        U_lab: 참가기관 확장불확도 (k=2)
        U_ref: 기준값 확장불확도 (k=2)

    Returns:
        (En number, 판정) 튜플
    """
    denom = math.sqrt(U_lab**2 + U_ref**2)
    if denom <= 0:
        raise ValueError("U_lab과 U_ref 중 하나 이상은 양수여야 합니다.")
    en = (x - X_ref) / denom
    return en, _judge_en(en)


def calculate_zeta_score(x: float, X_ref: float, u_lab: float, u_ref: float) -> tuple[float, str]:
    """ζ(제타)-score 계산.

    ζ = (x - X_ref) / √(u_lab² + u_ref²)

    Args:
        x: 참가기관 측정값
        X_ref: 기준값
        u_lab: 참가기관 표준불확도
        u_ref: 기준값 표준불확도

    Returns:
        (ζ-score, 판정) 튜플
    """
    denom = math.sqrt(u_lab**2 + u_ref**2)
    if denom <= 0:
        raise ValueError("u_lab과 u_ref 중 하나 이상은 양수여야 합니다.")
    zeta = (x - X_ref) / denom
    return zeta, _judge_z(zeta)


def analyze_pt(
    lab_value: float,
    assigned_value: float,
    sigma_pt: Optional[float] = None,
    U_lab: Optional[float] = None,
    U_ref: Optional[float] = None,
    k: float = 2.0,
    cal_point: str = "",
) -> PTResult:
    """단건 숙련도시험 분석.

    Args:
        lab_value: 참가기관 측정값
        assigned_value: 배정값/기준값
        sigma_pt: 숙련도시험 표준편차 (z-score용)
        U_lab: 참가기관 확장불확도 (En, ζ용)
        U_ref: 기준값 확장불확도 (En, ζ용)
        k: 포함인자 (기본 2)
        cal_point: 교정점 이름

    Returns:
        PTResult 객체
    """
    result = PTResult(
        lab_value=lab_value,
        assigned_value=assigned_value,
        cal_point=cal_point,
    )

    if sigma_pt is not None and sigma_pt > 0:
        result.z_score, result.z_judgment = calculate_z_score(lab_value, assigned_value, sigma_pt)

    if U_lab is not None and U_ref is not None:
        result.en_number, result.en_judgment = calculate_en_number(
            lab_value, assigned_value, U_lab, U_ref
        )
        u_lab = U_lab / k
        u_ref = U_ref / k
        result.zeta_score, result.zeta_judgment = calculate_zeta_score(
            lab_value, assigned_value, u_lab, u_ref
        )

    return result


def analyze_pt_batch(data: list[dict]) -> list[PTResult]:
    """다건 숙련도시험 분석.

    Args:
        data: 각 항목은 {"cal_point", "lab_value", "assigned_value", "sigma_pt", "U_lab", "U_ref"} 딕셔너리

    Returns:
        PTResult 리스트
    """
    results = []
    for item in data:
        result = analyze_pt(
            lab_value=item["lab_value"],
            assigned_value=item["assigned_value"],
            sigma_pt=item.get("sigma_pt"),
            U_lab=item.get("U_lab"),
            U_ref=item.get("U_ref"),
            k=item.get("k", 2.0),
            cal_point=item.get("cal_point", ""),
        )
        results.append(result)
    return results
