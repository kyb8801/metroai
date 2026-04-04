"""블록게이지 교정 템플릿 통합 테스트."""

import math
import pytest

from metroai.core.gum import GUMCalculator
from metroai.core.mcm import MCMCalculator
from metroai.templates.length import create_gauge_block_template


class TestGaugeBlockTemplate:
    """블록게이지 교정 불확도 예산 통합 테스트."""

    def test_template_runs_without_error(self):
        """기본 파라미터로 템플릿이 정상 실행."""
        model, sources, config = create_gauge_block_template()
        calc = GUMCalculator(
            model, sources,
            measurand_name=config["measurand_name"],
            measurand_unit=config["measurand_unit"],
        )
        result = calc.calculate()

        assert result.combined_uncertainty > 0
        assert result.expanded_uncertainty > 0
        assert len(result.components) == 5
        assert result.coverage_factor >= 2.0

    def test_template_with_custom_data(self):
        """사용자 데이터로 템플릿 실행."""
        model, sources, config = create_gauge_block_template(
            nominal_length_mm=100.0,
            comparator_readings=[0.05, 0.07, 0.03, 0.06, 0.04, 0.05, 0.06, 0.04, 0.05, 0.06],
            std_cert_uncertainty_um=0.08,
            std_cert_k=2.0,
            temp_uncertainty_C=0.3,
        )
        calc = GUMCalculator(
            model, sources,
            measurand_name=config["measurand_name"],
            measurand_unit=config["measurand_unit"],
        )
        result = calc.calculate()

        # 10회 반복 → A형 ν=9
        a_type_comp = result.components[0]
        assert a_type_comp.dof == 9

        # 합성불확도 > 0
        assert result.combined_uncertainty > 0

    def test_template_mcm_validation(self):
        """블록게이지 템플릿의 GUM vs MCM 교차 검증."""
        model, sources, config = create_gauge_block_template()

        # GUM
        gum_calc = GUMCalculator(
            model, sources,
            measurand_name=config["measurand_name"],
            measurand_unit=config["measurand_unit"],
        )
        gum_result = gum_calc.calculate()

        # MCM
        mcm_calc = MCMCalculator(model, sources, n_samples=200_000, seed=42)
        mcm_result = mcm_calc.simulate(gum_uc=gum_result.combined_uncertainty)

        # 선형 모델이므로 GUM과 MCM이 잘 일치해야 함 (10% 이내)
        if gum_result.combined_uncertainty > 0:
            rel_diff = abs(mcm_result.std - gum_result.combined_uncertainty) / gum_result.combined_uncertainty
            assert rel_diff < 0.10, f"GUM uc={gum_result.combined_uncertainty:.4e}, MCM std={mcm_result.std:.4e}, diff={rel_diff:.1%}"

    def test_excel_export(self):
        """엑셀 출력이 정상 동작."""
        from metroai.export.kolas_excel import export_budget_excel

        model, sources, config = create_gauge_block_template()
        calc = GUMCalculator(
            model, sources,
            measurand_name=config["measurand_name"],
            measurand_unit=config["measurand_unit"],
        )
        result = calc.calculate()

        buf = export_budget_excel(result)
        assert buf is not None
        assert len(buf.getvalue()) > 0  # 파일이 비어있지 않음
