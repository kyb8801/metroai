"""압력계 교정 템플릿 통합 테스트."""

import math

from metroai.core.gum import GUMCalculator
from metroai.templates.pressure import create_pressure_template


class TestPressureTemplate:
    def test_template_runs_without_error(self):
        """기본 파라미터로 정상 실행."""
        model, sources, config = create_pressure_template()
        calc = GUMCalculator(
            model, sources,
            measurand_name=config["measurand_name"],
            measurand_unit=config["measurand_unit"],
        )
        result = calc.calculate()

        assert result.combined_uncertainty > 0
        assert result.expanded_uncertainty > 0
        assert result.coverage_factor >= 2.0
        assert len(result.components) == 5

    def test_effective_dof_positive(self):
        """유효자유도가 양수."""
        model, sources, config = create_pressure_template()
        calc = GUMCalculator(model, sources)
        result = calc.calculate()
        assert result.effective_dof > 0

    def test_custom_data(self):
        """사용자 데이터로 실행."""
        model, sources, config = create_pressure_template(
            cal_point_MPa=50.0,
            readings_MPa=[0.002, 0.001, -0.001, 0.003, 0.000, 0.001],
            std_cert_U_MPa=0.005,
            hysteresis_MPa=0.003,
        )
        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        assert result.combined_uncertainty > 0
        assert result.components[0].dof == 5  # 6회 반복 → ν=5
