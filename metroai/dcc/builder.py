"""GUM 불확도 계산 결과 → DCC XML 초안 생성기.

MetroAI의 :class:`~metroai.core.gum.GUMResult` 와 성적서 관리 정보(cert_info)로
PTB DCC 3.3.0 스키마의 필수 요소를 갖춘 XML 초안을 만든다.

정직성 원칙 (1차 구현):
- 이 출력은 "DCC 초안"이다. 전자서명(ds:Signature)·첨부(byteData)·
  refType 국제 등록어휘 정합·다품목(item 2개 이상)은 미구현 (로드맵).
- 필수 필드가 입력되지 않으면 자리표시자를 넣고 ``warnings`` 에 기록한다 —
  경고가 남아 있는 초안을 공식 성적서로 쓰면 안 된다.
- 불확도는 D-SI 2.2.1의 비(非)deprecated 표현인
  measurementUncertaintyUnivariate/expandedMU 로 기록한다.

cert_info 주요 키 (모두 선택; :mod:`metroai.export.kolas_pdf` 의 cert_info와 호환):
    cert_number             성적서 번호 → coreData/uniqueIdentifier
    cal_org                 교정기관명
    cal_org_kolas_id        KOLAS 인정번호 → calibrationLaboratoryCode
    cal_org_address / cal_org_city / cal_org_email / cal_org_phone
    cal_date                교정일 "YYYY-MM-DD" (begin=end). 기간이면
    cal_date_begin / cal_date_end 로 각각 지정
    receipt_date, issue_date
    performance_location    laboratory|customer|... 또는 한국어("교정실","현장" 등)
    client_org / client_address / client_city
    equipment_name / manufacturer / model / serial_number / equipment_id
    calibrator_name / approver_name
    method_name / method_norm / method_reference
    ambient_temperature(℃) / ambient_humidity(%rh)
    traceability_statement  소급성 진술문
    country_code(기본 "KR"), lang(기본 "ko"), extra_lang(기본 "en")
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from datetime import date
from typing import Optional

from metroai import __version__ as METROAI_VERSION
from metroai.core.gum import GUMResult
from metroai.exceptions import DCCSchemaError

from .parser import DCC_NS, SI_NS, TARGET_SCHEMA_VERSION, XSI_NS
from .units import to_dsi_unit

ET.register_namespace("dcc", DCC_NS)
ET.register_namespace("si", SI_NS)
ET.register_namespace("xsi", XSI_NS)

_SCHEMA_LOCATION = f"{DCC_NS} https://ptb.de/dcc/v{TARGET_SCHEMA_VERSION}/dcc.xsd"

_PERFORMANCE_LOCATIONS = (
    "laboratory",
    "customer",
    "laboratoryBranch",
    "customerBranch",
    "other",
)
# 한국어 관용 표현 → enum
_LOCATION_ALIASES = {
    "교정실": "laboratory",
    "실험실": "laboratory",
    "자체교정실": "laboratory",
    "고정표준실": "laboratory",
    "현장": "customer",
    "현장교정": "customer",
    "고객사": "customer",
}


def _fmt(v: float) -> str:
    """수치 → XML 텍스트 (유효숫자 12자리, 지수표기 허용)."""
    return f"{v:.12g}"


def _dcc(parent: ET.Element, tag: str, text: Optional[str] = None) -> ET.Element:
    el = ET.SubElement(parent, f"{{{DCC_NS}}}{tag}")
    if text is not None:
        el.text = text
    return el


def _si_el(parent: ET.Element, tag: str, text: Optional[str] = None) -> ET.Element:
    el = ET.SubElement(parent, f"{{{SI_NS}}}{tag}")
    if text is not None:
        el.text = text
    return el


class DCCBuilder:
    """GUMResult + cert_info → DCC 3.3.0 XML 초안."""

    def __init__(
        self,
        result: GUMResult,
        cert_info: Optional[dict] = None,
        include_budget: bool = True,
    ):
        self.result = result
        self.cert_info = dict(cert_info or {})
        self.include_budget = include_budget
        #: 빌드 중 발견된 문제(자리표시자 사용·단위 미변환 등). 초안 검수 시 반드시 확인.
        self.warnings: list[str] = []

    # ------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------

    def _warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def _get(self, key: str, fallback: str, warn_label: str) -> str:
        val = str(self.cert_info.get(key, "") or "").strip()
        if not val:
            self._warn(f"{warn_label}({key}) 미입력 — 자리표시자 '{fallback}' 사용")
            return fallback
        return val

    def _text(
        self,
        parent: ET.Element,
        tag: str,
        content: str,
        lang: Optional[str] = None,
        content_en: Optional[str] = None,
    ) -> ET.Element:
        """dcc:textType 요소 생성 (선택적으로 영문 병기)."""
        el = _dcc(parent, tag)
        c = _dcc(el, "content", content)
        if lang:
            c.set("lang", lang)
        if content_en is not None:
            c2 = _dcc(el, "content", content_en)
            c2.set("lang", "en")
        return el

    def _unit(self, raw_unit: str) -> str:
        dsi = to_dsi_unit(raw_unit)
        if dsi is None:
            self._warn(
                f"단위 '{raw_unit}' 의 D-SI 변환 규칙이 없어 원문 그대로 기록 "
                "(D-SI 관례 위반 가능 — units.DSI_UNIT_MAP 참조)"
            )
            return raw_unit
        return dsi

    def _real_with_expanded_mu(
        self,
        parent: ET.Element,
        value: float,
        unit: str,
        expanded: Optional[float] = None,
        k: Optional[float] = None,
        probability: Optional[float] = None,
        distribution: Optional[str] = None,
    ) -> ET.Element:
        """si:real (+ measurementUncertaintyUnivariate/expandedMU) 생성."""
        real = _si_el(parent, "real")
        _si_el(real, "value", _fmt(value))
        _si_el(real, "unit", unit)
        if expanded is not None:
            muu = _si_el(real, "measurementUncertaintyUnivariate")
            emu = _si_el(muu, "expandedMU")
            _si_el(emu, "valueExpandedMU", _fmt(expanded))
            _si_el(emu, "coverageFactor", _fmt(k if k is not None else 2.0))
            _si_el(
                emu,
                "coverageProbability",
                _fmt(probability if probability is not None else 0.95),
            )
            if distribution:
                _si_el(emu, "distribution", distribution)
        return real

    # ------------------------------------------------------------
    # administrativeData
    # ------------------------------------------------------------

    def _build_admin(self, root: ET.Element) -> None:
        info = self.cert_info
        lang = info.get("lang", "ko")
        admin = _dcc(root, "administrativeData")

        # -- dccSoftware (필수)
        sw_list = _dcc(admin, "dccSoftware")
        sw = _dcc(sw_list, "software")
        self._text(sw, "name", "MetroAI")
        _dcc(sw, "release", METROAI_VERSION)

        # -- coreData (필수)
        core = _dcc(admin, "coreData")
        _dcc(core, "countryCodeISO3166_1", info.get("country_code", "KR"))
        _dcc(core, "usedLangCodeISO639_1", lang)
        extra_lang = info.get("extra_lang", "en")
        if extra_lang and extra_lang != lang:
            _dcc(core, "usedLangCodeISO639_1", extra_lang)
        _dcc(core, "mandatoryLangCodeISO639_1", lang)

        today = date.today().isoformat()
        cert_number = self._get(
            "cert_number", f"METROAI-DRAFT-{today}", "성적서 번호"
        )
        _dcc(core, "uniqueIdentifier", cert_number)

        if info.get("receipt_date"):
            _dcc(core, "receiptDate", str(info["receipt_date"]))

        cal_date = str(info.get("cal_date", "") or "").strip()
        begin = str(info.get("cal_date_begin", "") or "").strip() or cal_date
        end = str(info.get("cal_date_end", "") or "").strip() or cal_date
        if not begin:
            self._warn(f"교정일(cal_date) 미입력 — 오늘 날짜 {today} 사용")
            begin = end = today
        _dcc(core, "beginPerformanceDate", begin)
        _dcc(core, "endPerformanceDate", end or begin)

        loc_raw = str(info.get("performance_location", "laboratory")).strip()
        loc = _LOCATION_ALIASES.get(loc_raw, loc_raw)
        if loc not in _PERFORMANCE_LOCATIONS:
            self._warn(
                f"performance_location '{loc_raw}' 은 DCC enum이 아님 — 'other' 로 기록"
            )
            loc = "other"
        _dcc(core, "performanceLocation", loc)

        if info.get("issue_date"):
            _dcc(core, "issueDate", str(info["issue_date"]))

        # -- items (필수)
        items = _dcc(admin, "items")
        item = _dcc(items, "item")
        equipment_name = self._get("equipment_name", "UNSPECIFIED ITEM", "교정대상명")
        self._text(item, "name", equipment_name, lang=lang)
        if info.get("manufacturer"):
            manu = _dcc(item, "manufacturer")
            self._text(manu, "name", str(info["manufacturer"]))
        if info.get("model"):
            _dcc(item, "model", str(info["model"]))
        idents = []
        if info.get("serial_number"):
            idents.append(("manufacturer", str(info["serial_number"]), "기기번호", "Serial number"))
        if info.get("equipment_id"):
            idents.append(("customer", str(info["equipment_id"]), "관리번호", "Equipment ID"))
        if idents:
            ident_list = _dcc(item, "identifications")
            for issuer, value, name_ko, name_en in idents:
                ident = _dcc(ident_list, "identification")
                _dcc(ident, "issuer", issuer)
                _dcc(ident, "value", value)
                self._text(ident, "name", name_ko, lang=lang, content_en=name_en)

        # -- calibrationLaboratory (필수)
        lab = _dcc(admin, "calibrationLaboratory")
        if info.get("cal_org_kolas_id"):
            _dcc(lab, "calibrationLaboratoryCode", str(info["cal_org_kolas_id"]))
        lab_contact = _dcc(lab, "contact")
        cal_org = self._get("cal_org", "UNSPECIFIED LABORATORY", "교정기관명")
        self._text(lab_contact, "name", cal_org, lang=lang)
        if info.get("cal_org_email"):
            _dcc(lab_contact, "eMail", str(info["cal_org_email"]))
        if info.get("cal_org_phone"):
            _dcc(lab_contact, "phone", str(info["cal_org_phone"]))
        self._location(
            lab_contact,
            city=info.get("cal_org_city"),
            address=info.get("cal_org_address"),
            country=info.get("country_code", "KR"),
        )

        # -- respPersons (필수)
        persons = _dcc(admin, "respPersons")
        wrote_person = False
        if info.get("calibrator_name"):
            rp = _dcc(persons, "respPerson")
            p = _dcc(rp, "person")
            self._text(p, "name", str(info["calibrator_name"]))
            # role은 dcc:notEmptyStringType (textType 아님 — 단일 문자열)
            _dcc(rp, "role", "교정담당자")
            wrote_person = True
        if info.get("approver_name"):
            rp = _dcc(persons, "respPerson")
            p = _dcc(rp, "person")
            self._text(p, "name", str(info["approver_name"]))
            _dcc(rp, "role", "기술책임자")
            _dcc(rp, "mainSigner", "true")
            wrote_person = True
        if not wrote_person:
            self._warn(
                "책임자(calibrator_name/approver_name) 미입력 — 자리표시자 사용"
            )
            rp = _dcc(persons, "respPerson")
            p = _dcc(rp, "person")
            self._text(p, "name", "UNSPECIFIED")

        # -- customer (필수)
        customer = _dcc(admin, "customer")
        client_org = self._get("client_org", "UNSPECIFIED CUSTOMER", "고객명")
        self._text(customer, "name", client_org, lang=lang)
        self._location(
            customer,
            city=info.get("client_city"),
            address=info.get("client_address"),
            country=info.get("country_code", "KR"),
        )

        # -- statements (선택): 소급성 진술
        statement_text = info.get("traceability_statement")
        if statement_text:
            statements = _dcc(admin, "statements")
            st = _dcc(statements, "statement")
            self._text(st, "name", "소급성", lang=lang, content_en="Metrological traceability")
            decl = _dcc(st, "declaration")
            c = _dcc(decl, "content", str(statement_text))
            c.set("lang", lang)

    def _location(
        self,
        contact_el: ET.Element,
        city: Optional[str],
        address: Optional[str],
        country: str,
    ) -> None:
        """dcc:location — locationType은 자식 1개 이상 필수라 countryCode를 항상 기록."""
        loc = _dcc(contact_el, "location")
        if city:
            _dcc(loc, "city", str(city))
        _dcc(loc, "countryCode", country)
        if address:
            further = _dcc(loc, "further")
            _dcc(further, "content", str(address))

    # ------------------------------------------------------------
    # measurementResults
    # ------------------------------------------------------------

    def _build_measurement_results(self, root: ET.Element) -> None:
        info = self.cert_info
        lang = info.get("lang", "ko")
        r = self.result

        mrs = _dcc(root, "measurementResults")
        mr = _dcc(mrs, "measurementResult")
        self._text(mr, "name", "교정 결과", lang=lang, content_en="Calibration result")

        # usedMethods (선택)
        if info.get("method_name") or info.get("method_norm"):
            methods = _dcc(mr, "usedMethods")
            method = _dcc(methods, "usedMethod")
            self._text(
                method,
                "name",
                str(info.get("method_name") or "교정 방법"),
                lang=lang,
            )
            if info.get("method_norm"):
                _dcc(method, "norm", str(info["method_norm"]))
            if info.get("method_reference"):
                _dcc(method, "reference", str(info["method_reference"]))

        # influenceConditions (선택): 환경조건
        temp = info.get("ambient_temperature")
        humid = info.get("ambient_humidity")
        if temp is not None or humid is not None:
            ics = _dcc(mr, "influenceConditions")
            if temp is not None:
                ic = _dcc(ics, "influenceCondition")
                ic.set("refType", "basic_temperature")
                self._text(ic, "name", "주위 온도", lang=lang, content_en="Ambient temperature")
                data = _dcc(ic, "data")
                q = _dcc(data, "quantity")
                self._text(q, "name", "온도", lang=lang, content_en="Temperature")
                self._real_with_expanded_mu(q, float(temp), r"\degreecelsius")
            if humid is not None:
                ic = _dcc(ics, "influenceCondition")
                ic.set("refType", "basic_humidityRelative")
                self._text(ic, "name", "상대 습도", lang=lang, content_en="Relative humidity")
                data = _dcc(ic, "data")
                q = _dcc(data, "quantity")
                self._text(q, "name", "상대 습도", lang=lang, content_en="Relative humidity")
                self._real_with_expanded_mu(q, float(humid), r"\percent")

        # results (필수)
        results = _dcc(mr, "results")

        # ① 측정결과 + 확장불확도
        res = _dcc(results, "result")
        res.set("refType", "metroai_measurand")
        measurand = r.measurand_name or "Y"
        self._text(res, "name", measurand, lang=lang)
        data = _dcc(res, "data")
        q = _dcc(data, "quantity")
        self._text(q, "name", measurand, lang=lang)
        unit = self._unit(r.measurand_unit)
        self._real_with_expanded_mu(
            q,
            r.measurand_value,
            unit,
            expanded=r.expanded_uncertainty,
            k=r.coverage_factor,
            probability=r.confidence_level,
            distribution="normal",
        )

        # ② 불확도 예산 (선택, 기본 포함) — 기여량 |ci|·u(xi)는 측정량 단위
        if self.include_budget and r.components:
            budget = _dcc(results, "result")
            budget.set("refType", "metroai_uncertaintyBudget")
            self._text(
                budget, "name", "불확도 예산", lang=lang, content_en="Uncertainty budget"
            )
            bdata = _dcc(budget, "data")
            blist = _dcc(bdata, "list")
            blist.set("refType", "metroai_budgetTable")

            for comp in r.components:
                cq = _dcc(blist, "quantity")
                cq.set("refType", "metroai_budgetContribution")
                self._text(cq, "name", f"{comp.source.name} ({comp.source.symbol})", lang=lang)
                self._real_with_expanded_mu(cq, comp.contribution, unit)

            uq = _dcc(blist, "quantity")
            uq.set("refType", "metroai_combinedStandardUncertainty")
            self._text(
                uq, "name", "합성표준불확도 u_c", lang=lang,
                content_en="Combined standard uncertainty",
            )
            self._real_with_expanded_mu(uq, r.combined_uncertainty, unit)

            if math.isfinite(r.effective_dof):
                dq = _dcc(blist, "quantity")
                dq.set("refType", "metroai_effectiveDegreesOfFreedom")
                self._text(
                    dq, "name", "유효자유도 ν_eff", lang=lang,
                    content_en="Effective degrees of freedom",
                )
                self._real_with_expanded_mu(dq, r.effective_dof, r"\one")
            # ν_eff = ∞ (B형만 있는 경우)는 xs 수치로 표현하지 않고 생략한다.

    # ------------------------------------------------------------
    # 빌드
    # ------------------------------------------------------------

    def build(self) -> str:
        """DCC XML 문자열 생성 (XML 선언 포함, UTF-8 기준)."""
        if self.result is None:  # 방어
            raise DCCSchemaError("GUMResult가 없습니다 — build() 전에 계산을 수행하세요.")

        root = ET.Element(f"{{{DCC_NS}}}digitalCalibrationCertificate")
        root.set("schemaVersion", TARGET_SCHEMA_VERSION)
        root.set(f"{{{XSI_NS}}}schemaLocation", _SCHEMA_LOCATION)

        self._build_admin(root)
        self._build_measurement_results(root)

        comment = self.cert_info.get("dcc_comment")
        if comment:
            _dcc(root, "comment", str(comment))

        ET.indent(root, space="  ")
        body = ET.tostring(root, encoding="unicode")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"


def export_dcc_xml(
    result: GUMResult,
    cert_info: Optional[dict] = None,
    filepath: Optional[str] = None,
    include_budget: bool = True,
) -> str:
    """GUM 결과를 DCC XML 초안으로 내보내기 (편의 함수).

    Args:
        result: GUM 불확도 계산 결과
        cert_info: 성적서 관리 정보 (모듈 docstring의 키 참조)
        filepath: 지정 시 UTF-8 파일로 저장
        include_budget: 불확도 예산표 포함 여부

    Returns:
        XML 문자열. 빌드 경고는 :class:`DCCBuilder` 를 직접 써서 확인할 수 있다.
    """
    builder = DCCBuilder(result, cert_info, include_budget=include_budget)
    xml_text = builder.build()
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml_text)
    return xml_text
