"""교정성적서 PDF 출력 테스트."""

from metroai.core.distributions import DistributionType, UncertaintySource
from metroai.core.gum import GUMCalculator
from metroai.core.model import MeasurementModel
from metroai.export.kolas_pdf import export_calibration_certificate_pdf


def _make_result():
    model = MeasurementModel("a + b", symbol_names=["a", "b"])
    sources = [
        UncertaintySource(name="a", symbol="a", eval_type="B", value=10.0, std_uncertainty=0.3),
        UncertaintySource(name="b", symbol="b", eval_type="B", value=5.0, std_uncertainty=0.4),
    ]
    calc = GUMCalculator(model, sources, measurand_name="Y", measurand_unit="mm")
    return calc.calculate()


CERT_INFO = {
    "cert_number": "CAL-2026-001",
    "cal_org": "테스트교정기관",
    "cal_org_kolas_id": "KOLAS-0001",
    "cal_org_address": "서울시 강남구",
    "client_org": "테스트회사",
    "client_address": "경기도 수원시",
    "equipment_name": "블록게이지",
    "manufacturer": "Mitutoyo",
    "model": "BM1-50",
    "serial_number": "SN-12345",
    "cal_date": "2026-04-04",
    "cal_location": "교정실",
    "temperature": "20.0 +/- 0.5",
    "humidity": "50 +/- 10",
    "calibrator_name": "홍길동",
    "reviewer_name": "김철수",
    "approver_name": "이영희",
}


class TestKolasPDF:
    def test_returns_bytesio(self):
        """BytesIO 객체가 반환되는지."""
        result = _make_result()
        buf = export_calibration_certificate_pdf(result, CERT_INFO)
        assert buf is not None
        assert len(buf.getvalue()) > 0

    def test_valid_pdf_header(self):
        """반환된 BytesIO가 유효한 PDF인지 (%PDF- 시작)."""
        result = _make_result()
        buf = export_calibration_certificate_pdf(result, CERT_INFO)
        data = buf.getvalue()
        assert data[:5] == b"%PDF-"

    def test_has_pages(self):
        """페이지 수가 1 이상인지."""
        result = _make_result()
        buf = export_calibration_certificate_pdf(result, CERT_INFO)
        data = buf.getvalue()
        # PDF에서 /Type /Page 패턴으로 페이지 수 확인
        page_count = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
        assert page_count >= 1
