"""MetroAI MCP Server — 측정 불확도 계산 MCP 도구.

MCPize/AgenticMarket/ClawHub 배포용.
세계 최초 측정 불확도 MCP 서버.

사용법:
    pip install mcp
    python -m metroai.mcp_server

Tools:
    1. calculate_uncertainty — GUM 기반 불확도 계산
    2. reverse_uncertainty — 목표 CMC에서 허용 불확도 역산 (세계 최초)
    3. pt_analysis — 숙련도시험 z-score/En/ζ 판정
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def calculate_uncertainty(
    template: str = "gauge_block",
    readings: list[float] | None = None,
    std_cert_U: float = 0.05,
    std_cert_k: float = 2.0,
    **kwargs,
) -> dict:
    """GUM 기반 불확도 계산.

    Args:
        template: 교정 분야 (gauge_block, mass, temperature, pressure, dc_voltage)
        readings: 반복 측정 데이터
        std_cert_U: 표준기 확장불확도
        std_cert_k: 표준기 포함인자

    Returns:
        불확도 예산표 결과 (JSON-serializable dict)
    """
    from metroai.core.gum import GUMCalculator

    if readings is None:
        readings = [0.10, 0.12, 0.08, 0.11, 0.09]

    # 템플릿 로드
    if template == "gauge_block":
        from metroai.templates.length import create_gauge_block_template
        model, sources, config = create_gauge_block_template(
            comparator_readings=readings,
            std_cert_uncertainty_um=std_cert_U,
            std_cert_k=std_cert_k,
            **kwargs,
        )
    elif template == "mass":
        from metroai.templates.mass import create_mass_template
        model, sources, config = create_mass_template(
            readings_mg=readings,
            std_cert_U=std_cert_U,
            std_cert_k=std_cert_k,
            **kwargs,
        )
    elif template == "temperature":
        from metroai.templates.temperature import create_temperature_template
        model, sources, config = create_temperature_template(
            readings_deviation=readings,
            std_cert_U=std_cert_U,
            std_cert_k=std_cert_k,
            **kwargs,
        )
    elif template == "pressure":
        from metroai.templates.pressure import create_pressure_template
        model, sources, config = create_pressure_template(
            readings_deviation=readings,
            std_cert_U=std_cert_U,
            std_cert_k=std_cert_k,
            **kwargs,
        )
    elif template == "dc_voltage":
        from metroai.templates.electrical import create_dc_voltage_template
        model, sources, config = create_dc_voltage_template(
            readings_deviation=readings,
            std_cert_U=std_cert_U,
            std_cert_k=std_cert_k,
            **kwargs,
        )
    else:
        return {"error": f"Unknown template: {template}. Available: gauge_block, mass, temperature, pressure, dc_voltage"}

    calc = GUMCalculator(
        model, sources,
        measurand_name=config.get("measurand_name", "Y"),
        measurand_unit=config.get("measurand_unit", ""),
    )
    result = calc.calculate()

    return {
        "combined_uncertainty": result.combined_uncertainty,
        "expanded_uncertainty": result.expanded_uncertainty,
        "coverage_factor": result.coverage_factor,
        "effective_dof": result.effective_dof if not (result.effective_dof == float("inf")) else "infinity",
        "uncertainty_statement": result.uncertainty_statement(),
        "components": [
            {
                "name": c.source.name,
                "symbol": c.source.symbol,
                "eval_type": c.source.eval_type,
                "std_uncertainty": c.std_uncertainty,
                "sensitivity_coeff": c.sensitivity_coeff,
                "contribution": c.contribution,
                "percent_contribution": c.percent_contribution,
            }
            for c in result.components
        ],
        "template": template,
        "measurand_name": config.get("measurand_name"),
        "measurand_unit": config.get("measurand_unit"),
    }


def pt_analysis(
    lab_value: float,
    assigned_value: float,
    sigma_pt: float | None = None,
    U_lab: float | None = None,
    U_ref: float | None = None,
    k: float = 2.0,
) -> dict:
    """숙련도시험(PT) 분석 — z-score, En, ζ-score 자동 판정.

    Args:
        lab_value: 참가기관 측정값
        assigned_value: 배정값
        sigma_pt: 숙련도 평가용 표준편차 (z-score용)
        U_lab: 참가기관 확장불확도
        U_ref: 기준값 확장불확도
        k: 포함인자

    Returns:
        판정 결과 dict
    """
    from metroai.modules.pt_analyzer import analyze_pt

    result = analyze_pt(
        lab_value=lab_value,
        assigned_value=assigned_value,
        sigma_pt=sigma_pt,
        U_lab=U_lab,
        U_ref=U_ref,
        k=k,
    )

    return {
        "z_score": result.z_score,
        "z_judgment": result.z_judgment,
        "en_number": result.en_number,
        "en_judgment": result.en_judgment,
        "zeta_score": result.zeta_score,
        "zeta_judgment": result.zeta_judgment,
    }


# ──────────────────────────────────────────
# CLI / 테스트 진입점
# ──────────────────────────────────────────
if __name__ == "__main__":
    # 간단 테스트
    print("=== MetroAI MCP Server - Test ===")

    result = calculate_uncertainty(
        template="gauge_block",
        readings=[0.10, 0.12, 0.08, 0.11, 0.09],
    )
    print(f"\nGauge Block: U = {result['expanded_uncertainty']:.4e} {result['measurand_unit']}")
    print(f"Statement: {result['uncertainty_statement']}")

    pt = pt_analysis(lab_value=50.012, assigned_value=50.000, sigma_pt=0.015)
    print(f"\nPT z-score: {pt['z_score']:.3f} → {pt['z_judgment']}")

    print("\n✅ MCP Server ready for deployment to MCPize/AgenticMarket")
