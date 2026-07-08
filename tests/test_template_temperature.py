"""온도계 교정 템플릿 통합 테스트."""

import math

from metroai.core.gum import GUMCalculator
from metroai.templates.temperature import create_temperature_template


class TestTemperatureTemplate:
    def test_template_runs_without_error(self):
        """기본 파라미터로 정상 실행."""
        model, sources, config = create_temperature_template()
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
        model, sources, config = create_temperature_template()
        calc = GUMCalculator(model, sources)
        result = calc.calculate()
        assert result.effective_dof > 0

    def test_custom_data(self):
        """사용자 데이터로 실행."""
        model, sources, config = create_temperature_template(
            cal_point_C=200.0,
            readings_C=[0.02, 0.01, -0.01, 0.03, 0.00, 0.01, 0.02, -0.02, 0.01, 0.00],
            std_cert_U_C=0.05,
            stability_C=0.03,
            uniformity_C=0.08,
        )
        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        assert result.combined_uncertainty > 0
        assert result.components[0].dof == 9
