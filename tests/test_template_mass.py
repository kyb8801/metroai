"""분동 교정 템플릿 통합 테스트."""

import math

from metroai.core.gum import GUMCalculator
from metroai.templates.mass import create_mass_template


class TestMassTemplate:
    def test_template_runs_without_error(self):
        """기본 파라미터로 정상 실행."""
        model, sources, config = create_mass_template()
        calc = GUMCalculator(
            model, sources,
            measurand_name=config["measurand_name"],
            measurand_unit=config["measurand_unit"],
        )
        result = calc.calculate()

        assert result.combined_uncertainty > 0
        assert result.expanded_uncertainty > 0
        assert result.coverage_factor >= 2.0
        assert len(result.components) == 4

    def test_effective_dof_positive(self):
        """유효자유도가 양수."""
        model, sources, config = create_mass_template()
        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        assert result.effective_dof > 0

    def test_custom_data(self):
        """사용자 데이터로 실행."""
        model, sources, config = create_mass_template(
            nominal_mass_g=1000.0,
            readings_mg=[0.05, 0.07, 0.03, 0.06, 0.04, 0.05, 0.06, 0.04, 0.05, 0.06],
            std_cert_U=0.1,
        )
        calc = GUMCalculator(model, sources)
        result = calc.calculate()

        assert result.combined_uncertainty > 0
        assert result.components[0].dof == 9  # 10회 반복 → ν=9
