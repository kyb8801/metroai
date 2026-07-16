"""DCC (Digital Calibration Certificate) 모듈 테스트.

픽스처: tests/data/dcc/dcc_gp_temperature_simplified_v12.xml
    PTB 공식 Good Practice 예제 (DCC schemaVersion 3.1.1, LGPL-3.0,
    파일 머리말에 원 저작권 고지 포함).
    출처: https://github.com/PTB-M4D/pyDCC (data/dcc/), 원 배포처 PTB.

검증 축:
1. 공식 예제 파싱 — 관리 정보·측정결과·불확도 필드
2. GUMResult → DCC XML 빌드 — 필수 구조 + 수치 보존
3. 왕복(파싱→재생성→재파싱) — 지원 필드 보존
4. (선택) xmlschema + 로컬 XSD 존재 시 정식 스키마 검증
"""

import os
from pathlib import Path

import pytest

from metroai.core.distributions import UncertaintySource
from metroai.core.gum import GUMCalculator
from metroai.core.model import MeasurementModel
from metroai.dcc import (
    DCCBuilder,
    check_required_structure,
    export_dcc_xml,
    parse_dcc,
    to_dsi_unit,
)
from metroai.exceptions import DCCSchemaError

FIXTURE = Path(__file__).parent / "data" / "dcc" / "dcc_gp_temperature_simplified_v12.xml"

FULL_CERT_INFO = {
    "cert_number": "KOLAS-2026-0716-001",
    "cal_org": "한국측정기술연구소",
    "cal_org_kolas_id": "KC-0000",
    "cal_org_address": "대전광역시 유성구 측정로 1",
    "cal_org_city": "대전",
    "cal_date": "2026-07-01",
    "issue_date": "2026-07-10",
    "performance_location": "laboratory",
    "client_org": "고객사 주식회사",
    "client_address": "서울특별시 강남구 고객로 2",
    "equipment_name": "외측 마이크로미터",
    "manufacturer": "Mitutoyo",
    "model": "MDC-25PX",
    "serial_number": "SN-12345",
    "equipment_id": "EQ-001",
    "calibrator_name": "홍길동",
    "approver_name": "김책임",
    "method_name": "게이지블록 비교 측정",
    "method_norm": "KOLAS 교정절차서 C-001",
    "ambient_temperature": 20.1,
    "ambient_humidity": 45.0,
    "traceability_statement": "본 교정 결과는 국가측정표준(KRISS)에 소급됩니다.",
}


@pytest.fixture
def gum_result():
    """간단한 2-성분 선형 모델의 GUM 결과 (test_gum.py와 동일 구성)."""
    model = MeasurementModel("a + b", symbol_names=["a", "b"])
    sources = [
        UncertaintySource(
            name="표준기 교정", symbol="a", eval_type="B",
            value=10.0, std_uncertainty=0.3,
        ),
        UncertaintySource(
            name="반복성", symbol="b", eval_type="B",
            value=5.0, std_uncertainty=0.4,
        ),
    ]
    calc = GUMCalculator(model, sources, measurand_name="길이 L", measurand_unit="mm")
    return calc.calculate()


# ============================================================
# D-SI 단위 변환
# ============================================================


class TestDSIUnits:
    def test_common_units(self):
        assert to_dsi_unit("mm") == r"\milli\metre"
        assert to_dsi_unit("°C") == r"\degreecelsius"
        assert to_dsi_unit("℃") == r"\degreecelsius"
        assert to_dsi_unit("K") == r"\kelvin"
        assert to_dsi_unit("%") == r"\percent"

    def test_dimensionless_and_passthrough(self):
        assert to_dsi_unit("") == r"\one"
        assert to_dsi_unit("1") == r"\one"
        # 이미 D-SI 표기면 그대로 통과
        assert to_dsi_unit(r"\milli\metre") == r"\milli\metre"

    def test_simple_quotient(self):
        assert to_dsi_unit("m/s") == r"\metre\second\tothe{-1}"
        assert to_dsi_unit("µm/m") == r"\micro\metre\metre\tothe{-1}"

    def test_unknown_returns_none(self):
        assert to_dsi_unit("furlong") is None
        assert to_dsi_unit("mm/furlong") is None


# ============================================================
# 공식 예제 파싱
# ============================================================


@pytest.fixture(scope="module")
def doc():
    """공식 GP 예제 파싱 결과 (모듈 단위 캐시)."""
    return parse_dcc(FIXTURE)


class TestParseOfficialExample:
    def test_schema_version(self, doc):
        # GP 예제는 3.1.1 (파서는 3.1~3.3 공통 구조를 읽음)
        assert doc.schema_version == "3.1.1"

    def test_core_data(self, doc):
        core = doc.administrative_data.core_data
        assert core.unique_identifier == "GP_DCC_temperature_minimal_1.2"
        assert core.country_code == "DE"
        assert core.used_languages == ["de", "en"]
        assert core.mandatory_languages == ["de"]
        assert core.begin_performance_date == "1957-08-13"
        assert core.end_performance_date == "1957-08-13"
        assert core.performance_location == "laboratory"

    def test_calibration_laboratory(self, doc):
        lab = doc.administrative_data.calibration_laboratory
        assert lab.contact is not None
        assert lab.contact.name.get() == "Kalibrierfirma GmbH"
        assert lab.contact.email == "info@kalibrierfirma.xx"
        assert lab.contact.city == "Musterstadt"

    def test_customer(self, doc):
        customer = doc.administrative_data.customer
        assert customer is not None
        assert customer.name.get() == "Kunde GmbH"

    def test_item_and_identifications(self, doc):
        items = doc.administrative_data.items
        assert len(items) == 1
        item = items[0]
        assert item.name.get("en") == "Temperature sensor"
        assert item.name.get("de") == "Temperatur-Fühler"
        issuers = {i.issuer for i in item.identifications}
        assert issuers == {"manufacturer", "customer", "calibrationLaboratory"}

    def test_resp_persons(self, doc):
        persons = doc.administrative_data.resp_persons
        assert len(persons) == 2
        assert persons[0].name == "Michaela Musterfrau"
        assert persons[0].main_signer is True
        assert persons[1].main_signer is False

    def test_measurement_error_quantity_with_uncertainty(self, doc):
        assert len(doc.measurement_results) == 1
        mr = doc.measurement_results[0]
        assert len(mr.results) == 1
        quantities = mr.results[0].quantities
        err = next(q for q in quantities if q.ref_type == "basic_measurementError")
        assert err.scalar is False
        assert err.values == [0.072, 0.089, 0.107, -0.009, -0.084]
        assert err.unit == r"\kelvin"
        unc = err.uncertainty
        assert unc is not None
        assert unc.kind == "expandedUncXMLList"
        # 리스트 전체에 broadcast되는 단일 값
        assert unc.expanded == 0.061
        assert unc.coverage_factor == 2.0
        assert unc.coverage_probability == 0.95
        assert unc.distribution == "normal"

    def test_hybrid_quantity_alternate_representation(self, doc):
        quantities = doc.measurement_results[0].results[0].quantities
        ref = next(q for q in quantities if q.ref_type == "basic_referenceValue")
        # si:hybrid: 1차 표현 K, 2차 표현 °C
        assert ref.unit == r"\kelvin"
        assert len(ref.values) == 5
        assert len(ref.alternates) == 1
        alt_values, alt_unit = ref.alternates[0]
        assert alt_unit == r"\degreecelsius"
        assert alt_values[0] == pytest.approx(33.098)

    def test_influence_conditions(self, doc):
        ics = doc.measurement_results[0].influence_conditions
        assert len(ics) >= 2
        temp_ic = next(ic for ic in ics if ic.ref_type == "basic_temperature")
        assert any(q.unit == r"\kelvin" for q in temp_ic.quantities)

    def test_required_structure_satisfied(self, doc):
        assert check_required_structure(doc) == []


# ============================================================
# 파서 오류 처리
# ============================================================


class TestParserErrors:
    def test_not_xml_raises(self):
        with pytest.raises(DCCSchemaError):
            parse_dcc("<not-closed")

    def test_wrong_root_raises(self):
        with pytest.raises(DCCSchemaError, match="digitalCalibrationCertificate"):
            parse_dcc("<foo><bar/></foo>")

    def test_missing_required_reported(self):
        # 루트만 있는 빈 DCC → 필수 요소 전부 누락으로 보고
        xml = (
            '<dcc:digitalCalibrationCertificate xmlns:dcc="https://ptb.de/dcc" '
            'schemaVersion="3.3.0"/>'
        )
        doc = parse_dcc(xml)
        missing = check_required_structure(doc)
        assert any("uniqueIdentifier" in m for m in missing)
        assert any("items/item" in m for m in missing)
        assert any("measurementResult" in m for m in missing)


# ============================================================
# 빌더
# ============================================================


class TestBuilder:
    def test_full_build_admin_fields(self, gum_result):
        builder = DCCBuilder(gum_result, FULL_CERT_INFO)
        doc = parse_dcc(builder.build())

        core = doc.administrative_data.core_data
        assert core.unique_identifier == "KOLAS-2026-0716-001"
        assert core.country_code == "KR"
        assert core.begin_performance_date == "2026-07-01"
        assert core.end_performance_date == "2026-07-01"
        assert core.issue_date == "2026-07-10"
        assert core.performance_location == "laboratory"
        assert core.used_languages == ["ko", "en"]
        assert core.mandatory_languages == ["ko"]

        lab = doc.administrative_data.calibration_laboratory
        assert lab.code == "KC-0000"
        assert lab.contact.name.get() == "한국측정기술연구소"

        assert doc.administrative_data.customer.name.get() == "고객사 주식회사"

        item = doc.administrative_data.items[0]
        assert item.name.get() == "외측 마이크로미터"
        assert item.model == "MDC-25PX"
        serial = next(
            i for i in item.identifications if i.issuer == "manufacturer"
        )
        assert serial.value == "SN-12345"

        persons = doc.administrative_data.resp_persons
        assert [p.name for p in persons] == ["홍길동", "김책임"]
        assert persons[1].main_signer is True

        # 소급성 진술
        assert len(doc.administrative_data.statements) == 1
        decl = doc.administrative_data.statements[0].declaration
        assert "소급" in decl.get()

        # dccSoftware = MetroAI + 버전
        sw = doc.administrative_data.software[0]
        assert sw.name.get() == "MetroAI"

        # 완전 입력 → 자리표시자 경고 없음
        assert builder.warnings == []

    def test_measurand_value_and_uncertainty_roundtrip(self, gum_result):
        xml = export_dcc_xml(gum_result, FULL_CERT_INFO)
        doc = parse_dcc(xml)

        mr = doc.measurement_results[0]
        measurand_result = next(
            r for r in mr.results if r.ref_type == "metroai_measurand"
        )
        q = measurand_result.quantities[0]
        assert q.scalar is True
        assert q.value == pytest.approx(15.0, abs=1e-12)
        assert q.unit == r"\milli\metre"
        unc = q.uncertainty
        assert unc.kind == "expandedMU"  # deprecated 아닌 D-SI 2.2.1 표현
        assert unc.expanded == pytest.approx(gum_result.expanded_uncertainty, rel=1e-10)
        assert unc.coverage_factor == pytest.approx(gum_result.coverage_factor, rel=1e-10)
        assert unc.coverage_probability == pytest.approx(0.9545, rel=1e-10)
        assert unc.distribution == "normal"

    def test_budget_included(self, gum_result):
        doc = parse_dcc(export_dcc_xml(gum_result, FULL_CERT_INFO))
        budget = next(
            r
            for r in doc.measurement_results[0].results
            if r.ref_type == "metroai_uncertaintyBudget"
        )
        contribs = [
            q for q in budget.quantities if q.ref_type == "metroai_budgetContribution"
        ]
        assert len(contribs) == len(gum_result.components)
        assert contribs[0].value == pytest.approx(0.3, abs=1e-12)
        assert contribs[1].value == pytest.approx(0.4, abs=1e-12)
        uc = next(
            q
            for q in budget.quantities
            if q.ref_type == "metroai_combinedStandardUncertainty"
        )
        assert uc.value == pytest.approx(0.5, abs=1e-12)
        # 이 예제는 νeff=∞ (B형만) → 유효자유도 quantity는 생략됨
        assert not any(
            q.ref_type == "metroai_effectiveDegreesOfFreedom"
            for q in budget.quantities
        )

    def test_budget_excluded(self, gum_result):
        doc = parse_dcc(export_dcc_xml(gum_result, FULL_CERT_INFO, include_budget=False))
        refs = [r.ref_type for r in doc.measurement_results[0].results]
        assert refs == ["metroai_measurand"]

    def test_influence_conditions_written(self, gum_result):
        doc = parse_dcc(export_dcc_xml(gum_result, FULL_CERT_INFO))
        ics = doc.measurement_results[0].influence_conditions
        temp = next(ic for ic in ics if ic.ref_type == "basic_temperature")
        assert temp.quantities[0].value == pytest.approx(20.1)
        assert temp.quantities[0].unit == r"\degreecelsius"
        humid = next(ic for ic in ics if ic.ref_type == "basic_humidityRelative")
        assert humid.quantities[0].unit == r"\percent"

    def test_empty_cert_info_uses_placeholders_with_warnings(self, gum_result):
        builder = DCCBuilder(gum_result, {})
        doc = parse_dcc(builder.build())
        # 필수 구조는 자리표시자로 채워짐
        assert check_required_structure(doc) == []
        # 그러나 경고로 정직하게 알림
        joined = " ".join(builder.warnings)
        assert "cert_number" in joined
        assert "cal_org" in joined
        assert "client_org" in joined

    def test_unknown_unit_kept_raw_with_warning(self, gum_result):
        gum_result.measurand_unit = "furlong"
        builder = DCCBuilder(gum_result, FULL_CERT_INFO)
        doc = parse_dcc(builder.build())
        q = doc.measurement_results[0].results[0].quantities[0]
        assert q.unit == "furlong"  # 원문 보존
        assert any("furlong" in w for w in builder.warnings)

    def test_korean_location_alias(self, gum_result):
        info = dict(FULL_CERT_INFO, performance_location="현장")
        doc = parse_dcc(export_dcc_xml(gum_result, info))
        assert (
            doc.administrative_data.core_data.performance_location == "customer"
        )

    def test_built_structure_complete(self, gum_result):
        doc = parse_dcc(export_dcc_xml(gum_result, FULL_CERT_INFO))
        assert check_required_structure(doc) == []

    def test_file_export(self, gum_result, tmp_path):
        out = tmp_path / "dcc_draft.xml"
        export_dcc_xml(gum_result, FULL_CERT_INFO, filepath=str(out))
        assert out.exists()
        doc = parse_dcc(out)
        assert doc.schema_version == "3.3.0"


# ============================================================
# 왕복 (공식 예제 → 빌더 → 재파싱)
# ============================================================


class TestRoundTrip:
    def test_official_example_fields_survive_rebuild(self, gum_result):
        """공식 예제의 관리 정보 + 대표 수치를 빌더 입력으로 재구성 → 재파싱 비교.

        빌더는 GUMResult 기반이므로 예제의 첫 measurementError 점
        (0.072 K, U=0.061, k=2)을 GUMResult 필드에 실어 왕복한다.
        """
        src = parse_dcc(FIXTURE)
        core = src.administrative_data.core_data
        lab = src.administrative_data.calibration_laboratory

        err = next(
            q
            for q in src.measurement_results[0].results[0].quantities
            if q.ref_type == "basic_measurementError"
        )

        gum_result.measurand_name = "Measurement error"
        gum_result.measurand_unit = r"\kelvin"  # D-SI 표기 그대로 통과
        gum_result.measurand_value = err.values[0]
        gum_result.expanded_uncertainty = err.uncertainty.expanded
        gum_result.coverage_factor = err.uncertainty.coverage_factor
        gum_result.confidence_level = err.uncertainty.coverage_probability

        cert_info = {
            "cert_number": core.unique_identifier,
            "country_code": core.country_code,
            "lang": "en",
            "cal_date_begin": core.begin_performance_date,
            "cal_date_end": core.end_performance_date,
            "performance_location": core.performance_location,
            "cal_org": lab.contact.name.get(),
            "cal_org_city": lab.contact.city,
            "client_org": src.administrative_data.customer.name.get(),
            "equipment_name": src.administrative_data.items[0].name.get("en"),
            "serial_number": src.administrative_data.items[0].identifications[0].value,
            "calibrator_name": src.administrative_data.resp_persons[0].name,
        }

        rebuilt = parse_dcc(export_dcc_xml(gum_result, cert_info))

        r_core = rebuilt.administrative_data.core_data
        assert r_core.unique_identifier == "GP_DCC_temperature_minimal_1.2"
        assert r_core.country_code == "DE"
        assert r_core.begin_performance_date == "1957-08-13"
        assert r_core.performance_location == "laboratory"
        assert (
            rebuilt.administrative_data.calibration_laboratory.contact.name.get()
            == "Kalibrierfirma GmbH"
        )
        assert rebuilt.administrative_data.customer.name.get() == "Kunde GmbH"
        assert (
            rebuilt.administrative_data.items[0].name.get() == "Temperature sensor"
        )

        q = rebuilt.measurement_results[0].results[0].quantities[0]
        assert q.value == pytest.approx(0.072)
        assert q.unit == r"\kelvin"
        assert q.uncertainty.expanded == pytest.approx(0.061)
        assert q.uncertainty.coverage_factor == pytest.approx(2.0)
        assert q.uncertainty.coverage_probability == pytest.approx(0.95)

    def test_build_is_deterministic(self, gum_result):
        xml1 = export_dcc_xml(gum_result, FULL_CERT_INFO)
        xml2 = export_dcc_xml(gum_result, FULL_CERT_INFO)
        assert xml1 == xml2


# ============================================================
# (선택) 정식 XSD 검증 — xmlschema + 로컬 XSD 사본 필요
# ============================================================

_XSD_DIR = os.environ.get("METROAI_DCC_XSD_DIR", "")


def _xmlschema_available() -> bool:
    try:
        import xmlschema  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not (_XSD_DIR and Path(_XSD_DIR, "dcc.xsd").exists() and _xmlschema_available()),
    reason="xmlschema 미설치 또는 METROAI_DCC_XSD_DIR (dcc.xsd 위치) 미설정",
)
class TestXSDValidation:
    def test_builder_output_validates_against_official_xsd(self, gum_result):
        from metroai.dcc import validate_dcc

        xml = export_dcc_xml(gum_result, FULL_CERT_INFO)
        errors = validate_dcc(xml, xsd_source=_XSD_DIR)
        assert errors == [], "\n".join(errors)
