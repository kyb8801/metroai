"""숙련도시험(PT) 분석 모듈 테스트."""

import math
import pytest

from metroai.modules.pt_analyzer import (
    PTResult,
    analyze_pt,
    analyze_pt_batch,
    calculate_en_number,
    calculate_z_score,
    calculate_zeta_score,
)


class TestZScore:
    """z-score 계산 테스트."""

    def test_z_score_calculation(self):
        """z = (x - X) / sigma_pt 정확도."""
        z, judgment = calculate_z_score(x=50.001, X=50.000, sigma_pt=0.001)
        assert abs(z - 1.0) < 1e-10
        assert judgment == "만족"

    def test_z_satisfactory(self):
        """|z| <= 2.0 -> 만족."""
        z, j = calculate_z_score(10.0, 10.0, 1.0)
        assert j == "만족"

    def test_z_questionable(self):
        """2.0 < |z| < 3.0 -> 주의."""
        z, j = calculate_z_score(12.5, 10.0, 1.0)
        assert j == "주의"

    def test_z_unsatisfactory(self):
        """|z| >= 3.0 -> 불만족."""
        z, j = calculate_z_score(13.0, 10.0, 1.0)
        assert j == "불만족"

    def test_z_boundary_2(self):
        """경계값 |z| = 2.0 -> 만족."""
        z, j = calculate_z_score(12.0, 10.0, 1.0)
        assert abs(z - 2.0) < 1e-10
        assert j == "만족"

    def test_z_boundary_3(self):
        """경계값 |z| = 3.0 -> 불만족."""
        z, j = calculate_z_score(13.0, 10.0, 1.0)
        assert abs(z - 3.0) < 1e-10
        assert j == "불만족"

    def test_z_negative_sigma_raises(self):
        with pytest.raises(ValueError):
            calculate_z_score(10.0, 10.0, -1.0)


class TestEnNumber:
    """En number 계산 테스트."""

    def test_en_calculation(self):
        """En = (x - X_ref) / sqrt(U_lab^2 + U_ref^2) 정확도."""
        en, j = calculate_en_number(10.002, 10.000, 0.002, 0.001)
        expected = 0.002 / math.sqrt(0.002**2 + 0.001**2)
        assert abs(en - expected) < 1e-10

    def test_en_satisfactory(self):
        """|En| <= 1.0 -> 만족."""
        en, j = calculate_en_number(10.001, 10.000, 0.002, 0.001)
        assert j == "만족"

    def test_en_unsatisfactory(self):
        """|En| > 1.0 -> 불만족."""
        en, j = calculate_en_number(10.010, 10.000, 0.002, 0.001)
        assert j == "불만족"

    def test_en_boundary_1(self):
        """경계값 |En| < 1.0 -> 만족."""
        en, j = calculate_en_number(10.001, 10.000, 0.002, 0.001)
        assert abs(en) < 1.0
        assert j == "만족"


class TestZetaScore:
    """ζ-score 계산 테스트."""

    def test_zeta_calculation(self):
        """zeta = (x - X_ref) / sqrt(u_lab^2 + u_ref^2) 정확도."""
        zeta, j = calculate_zeta_score(10.001, 10.000, 0.001, 0.0005)
        expected = 0.001 / math.sqrt(0.001**2 + 0.0005**2)
        assert abs(zeta - expected) < 1e-10

    def test_zeta_satisfactory(self):
        """|zeta| <= 2.0 -> 만족."""
        zeta, j = calculate_zeta_score(10.001, 10.000, 0.001, 0.001)
        assert j == "만족"

    def test_zeta_unsatisfactory(self):
        """|zeta| >= 3.0 -> 불만족."""
        zeta, j = calculate_zeta_score(10.01, 10.000, 0.001, 0.001)
        assert j == "불만족"


class TestAnalyzePT:
    """통합 분석 테스트."""

    def test_analyze_with_all_scores(self):
        result = analyze_pt(
            lab_value=50.001,
            assigned_value=50.000,
            sigma_pt=0.002,
            U_lab=0.003,
            U_ref=0.002,
            k=2.0,
        )
        assert result.z_score is not None
        assert result.en_number is not None
        assert result.zeta_score is not None

    def test_analyze_z_only(self):
        result = analyze_pt(lab_value=50.001, assigned_value=50.000, sigma_pt=0.002)
        assert result.z_score is not None
        assert result.en_number is None


class TestBatchAnalysis:
    """배치 분석 테스트."""

    def test_batch_returns_list(self):
        data = [
            {"cal_point": "50mm", "lab_value": 50.001, "assigned_value": 50.000, "sigma_pt": 0.002},
            {"cal_point": "100mm", "lab_value": 100.003, "assigned_value": 100.000, "sigma_pt": 0.005},
        ]
        results = analyze_pt_batch(data)
        assert len(results) == 2
        assert all(isinstance(r, PTResult) for r in results)
        assert results[0].cal_point == "50mm"
        assert results[1].cal_point == "100mm"
