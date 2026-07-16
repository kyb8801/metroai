"""DCC (Digital Calibration Certificate) XML 파서.

PTB 주도의 디지털 교정성적서 XML 표준을 읽는다.

- 대상 스키마: DCC 3.x (개발 기준 3.3.0, https://ptb.de/dcc/v3.3.0/dcc.xsd).
  공식 Good Practice 예제(3.1.1)도 파싱되도록 3.1~3.3 공통 구조만 사용한다.
- 표준 라이브러리(xml.etree.ElementTree)만 사용. 정식 XSD 검증은
  선택 의존성 xmlschema 설치 시 :func:`validate_dcc` 로 수행.
- 1차 구현 범위: administrativeData(coreData·items·교정기관·책임자·고객·statements),
  measurementResults(사용 방법·장비·환경조건·결과 수치·불확도).
  si:constant, si:complex, byteData(첨부파일), ds:Signature 는 아직 해석하지 않는다.

참조:
- 스키마 저장소: https://gitlab.com/ptb/dcc/xsd-dcc (LGPL-3.0)
- 문서 위키: https://wiki.dcc.ptb.de
- D-SI 수치·불확도 표현: SI_Format.xsd v2.2.1 (https://ptb.de/si)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import IO, Any, Optional, Union

from metroai.exceptions import DCCSchemaError

# ============================================================
# 네임스페이스 / 상수
# ============================================================

DCC_NS = "https://ptb.de/dcc"
SI_NS = "https://ptb.de/si"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

#: 이 모듈이 기준으로 삼는 DCC 스키마 버전
TARGET_SCHEMA_VERSION = "3.3.0"
OFFICIAL_XSD_URL = f"https://ptb.de/dcc/v{TARGET_SCHEMA_VERSION}/dcc.xsd"


def _dcc(tag: str) -> str:
    return f"{{{DCC_NS}}}{tag}"


def _si(tag: str) -> str:
    return f"{{{SI_NS}}}{tag}"


# ============================================================
# 데이터 모델
# ============================================================


@dataclass
class DCCText:
    """다국어 텍스트 (dcc:textType — content[@lang] 목록)."""

    contents: dict[str, str] = field(default_factory=dict)  # lang("" = 무지정) → 텍스트

    def get(self, lang: Optional[str] = None) -> str:
        """지정 언어 텍스트. 없으면 무지정 → 첫 항목 순으로 폴백."""
        if lang and lang in self.contents:
            return self.contents[lang]
        if "" in self.contents:
            return self.contents[""]
        return next(iter(self.contents.values()), "")

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.get()

    def __bool__(self) -> bool:
        return bool(self.contents)


@dataclass
class DCCIdentification:
    """dcc:identification — 발행 주체별 식별번호."""

    issuer: str = ""  # manufacturer | calibrationLaboratory | customer | owner | other
    value: str = ""
    name: Optional[DCCText] = None


@dataclass
class DCCContact:
    """dcc:contactType — 이름 + 연락처 + 주소."""

    name: Optional[DCCText] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    post_code: Optional[str] = None
    street: Optional[str] = None
    street_no: Optional[str] = None
    further: Optional[str] = None


@dataclass
class DCCSoftware:
    name: Optional[DCCText] = None
    release: str = ""


@dataclass
class DCCItem:
    """dcc:item — 교정 대상 기기."""

    name: Optional[DCCText] = None
    manufacturer: Optional[DCCText] = None
    model: Optional[str] = None
    identifications: list[DCCIdentification] = field(default_factory=list)


@dataclass
class DCCCoreData:
    """dcc:coreData — 국가·언어·성적서 번호·수행일 등 핵심 관리 정보.

    날짜는 원문 보존을 위해 ISO 문자열("YYYY-MM-DD") 그대로 둔다.
    """

    country_code: str = ""
    used_languages: list[str] = field(default_factory=list)
    mandatory_languages: list[str] = field(default_factory=list)
    unique_identifier: str = ""
    identifications: list[DCCIdentification] = field(default_factory=list)
    receipt_date: Optional[str] = None
    begin_performance_date: str = ""
    end_performance_date: str = ""
    performance_location: str = ""
    issue_date: Optional[str] = None


@dataclass
class DCCRespPerson:
    name: str = ""
    role: Optional[str] = None
    main_signer: bool = False


@dataclass
class DCCCalibrationLaboratory:
    code: Optional[str] = None  # calibrationLaboratoryCode (예: KOLAS 인정번호)
    contact: Optional[DCCContact] = None


@dataclass
class DCCStatement:
    """dcc:statement (statementMetaDataType) — 소급성·적합성 등 선언문."""

    name: Optional[DCCText] = None
    declaration: Optional[DCCText] = None
    norms: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    ref_type: Optional[str] = None


@dataclass
class DCCAdministrativeData:
    software: list[DCCSoftware] = field(default_factory=list)
    core_data: DCCCoreData = field(default_factory=DCCCoreData)
    items: list[DCCItem] = field(default_factory=list)
    calibration_laboratory: DCCCalibrationLaboratory = field(
        default_factory=DCCCalibrationLaboratory
    )
    resp_persons: list[DCCRespPerson] = field(default_factory=list)
    customer: Optional[DCCContact] = None
    statements: list[DCCStatement] = field(default_factory=list)


@dataclass
class DCCUncertainty:
    """D-SI 불확도 표현 (si:expandedUnc / si:measurementUncertaintyUnivariate 등).

    kind:
        "expandedUnc"        — (3.1.x, D-SI 2.2.1에서 deprecated) 확장불확도
        "expandedMU"         — measurementUncertaintyUnivariate/expandedMU
        "standardMU"         — measurementUncertaintyUnivariate/standardMU
        "coverageInterval"   — (deprecated) 포함구간
        "expandedUncXMLList" — 리스트 수치용 확장불확도 (broadcast 가능)

    수치 필드는 스칼라 표현이면 float, XMLList 표현이면 list[float].
    """

    kind: str = "expandedMU"
    expanded: Union[float, list[float], None] = None  # U
    standard: Union[float, list[float], None] = None  # u_c
    coverage_factor: Union[float, list[float], None] = None  # k
    coverage_probability: Union[float, list[float], None] = None  # p
    distribution: Optional[str] = None


@dataclass
class DCCQuantity:
    """dcc:quantity — 수치(스칼라 또는 리스트) + 단위 + 불확도."""

    name: Optional[DCCText] = None
    values: list[float] = field(default_factory=list)
    unit: str = ""
    scalar: bool = True  # si:real이면 True, XMLList이면 False
    uncertainty: Optional[DCCUncertainty] = None
    ref_type: Optional[str] = None
    #: si:hybrid의 추가 표현 (values, unit) 튜플 목록
    alternates: list[tuple[list[float], str]] = field(default_factory=list)

    @property
    def value(self) -> Optional[float]:
        """스칼라 값 (리스트 수치면 첫 값, 값이 없으면 None)."""
        return self.values[0] if self.values else None


@dataclass
class DCCUsedMethod:
    name: Optional[DCCText] = None
    norms: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    ref_type: Optional[str] = None


@dataclass
class DCCMeasuringEquipment:
    name: Optional[DCCText] = None
    identifications: list[DCCIdentification] = field(default_factory=list)
    ref_type: Optional[str] = None


@dataclass
class DCCInfluenceCondition:
    """dcc:influenceCondition — 환경조건 (온도·습도 등)."""

    name: Optional[DCCText] = None
    quantities: list[DCCQuantity] = field(default_factory=list)
    ref_type: Optional[str] = None


@dataclass
class DCCResult:
    """dcc:result — 결과 블록 (내부 quantity를 평탄화하여 수집)."""

    name: Optional[DCCText] = None
    quantities: list[DCCQuantity] = field(default_factory=list)
    ref_type: Optional[str] = None


@dataclass
class DCCMeasurementResult:
    name: Optional[DCCText] = None
    used_methods: list[DCCUsedMethod] = field(default_factory=list)
    measuring_equipments: list[DCCMeasuringEquipment] = field(default_factory=list)
    influence_conditions: list[DCCInfluenceCondition] = field(default_factory=list)
    results: list[DCCResult] = field(default_factory=list)


@dataclass
class DCCDocument:
    """파싱된 DCC 전체."""

    schema_version: str = ""
    administrative_data: DCCAdministrativeData = field(
        default_factory=DCCAdministrativeData
    )
    measurement_results: list[DCCMeasurementResult] = field(default_factory=list)
    comment: Optional[str] = None


# ============================================================
# 하위 파서
# ============================================================


def _txt(el: Optional[ET.Element]) -> Optional[str]:
    if el is None or el.text is None:
        return None
    return el.text.strip()


def _floats(text: Optional[str]) -> list[float]:
    """xs:list (공백 구분) 수치 문자열 → float 리스트."""
    if not text:
        return []
    return [float(tok) for tok in text.split()]


def _scalar_or_list(vals: list[float]) -> Union[float, list[float], None]:
    if not vals:
        return None
    return vals[0] if len(vals) == 1 else vals


def _parse_text(el: Optional[ET.Element]) -> Optional[DCCText]:
    """dcc:textType/richContentType → DCCText (content[@lang] 수집)."""
    if el is None:
        return None
    contents: dict[str, str] = {}
    for c in el.findall(_dcc("content")):
        lang = c.get("lang", "")
        if c.text is not None:
            contents[lang] = c.text.strip()
    return DCCText(contents) if contents else None


def _parse_identifications(el: Optional[ET.Element]) -> list[DCCIdentification]:
    out: list[DCCIdentification] = []
    if el is None:
        return out
    for ident in el.findall(_dcc("identification")):
        out.append(
            DCCIdentification(
                issuer=_txt(ident.find(_dcc("issuer"))) or "",
                value=_txt(ident.find(_dcc("value"))) or "",
                name=_parse_text(ident.find(_dcc("name"))),
            )
        )
    return out


def _parse_contact(el: Optional[ET.Element]) -> Optional[DCCContact]:
    if el is None:
        return None
    loc = el.find(_dcc("location"))
    further = None
    if loc is not None:
        further_el = loc.find(_dcc("further"))
        further_text = _parse_text(further_el)
        further = further_text.get() if further_text else None
    return DCCContact(
        name=_parse_text(el.find(_dcc("name"))),
        email=_txt(el.find(_dcc("eMail"))),
        phone=_txt(el.find(_dcc("phone"))),
        city=_txt(loc.find(_dcc("city"))) if loc is not None else None,
        country_code=_txt(loc.find(_dcc("countryCode"))) if loc is not None else None,
        post_code=_txt(loc.find(_dcc("postCode"))) if loc is not None else None,
        street=_txt(loc.find(_dcc("street"))) if loc is not None else None,
        street_no=_txt(loc.find(_dcc("streetNo"))) if loc is not None else None,
        further=further,
    )


def _parse_uncertainty_from_real(real: ET.Element) -> Optional[DCCUncertainty]:
    """si:real 내부의 불확도 표현 해석 (expandedUnc | measurementUncertaintyUnivariate | coverageInterval)."""
    exp = real.find(_si("expandedUnc"))
    if exp is not None:
        return DCCUncertainty(
            kind="expandedUnc",
            expanded=_scalar_or_list(_floats(_txt(exp.find(_si("uncertainty"))))),
            coverage_factor=_scalar_or_list(_floats(_txt(exp.find(_si("coverageFactor"))))),
            coverage_probability=_scalar_or_list(
                _floats(_txt(exp.find(_si("coverageProbability"))))
            ),
            distribution=_txt(exp.find(_si("distribution"))),
        )

    muu = real.find(_si("measurementUncertaintyUnivariate"))
    if muu is not None:
        emu = muu.find(_si("expandedMU"))
        if emu is not None:
            return DCCUncertainty(
                kind="expandedMU",
                expanded=_scalar_or_list(_floats(_txt(emu.find(_si("valueExpandedMU"))))),
                coverage_factor=_scalar_or_list(
                    _floats(_txt(emu.find(_si("coverageFactor"))))
                ),
                coverage_probability=_scalar_or_list(
                    _floats(_txt(emu.find(_si("coverageProbability"))))
                ),
                distribution=_txt(emu.find(_si("distribution"))),
            )
        smu = muu.find(_si("standardMU"))
        if smu is not None:
            return DCCUncertainty(
                kind="standardMU",
                standard=_scalar_or_list(_floats(_txt(smu.find(_si("valueStandardMU"))))),
                distribution=_txt(smu.find(_si("distribution"))),
            )

    cov = real.find(_si("coverageInterval"))
    if cov is not None:
        return DCCUncertainty(
            kind="coverageInterval",
            standard=_scalar_or_list(_floats(_txt(cov.find(_si("standardUnc"))))),
            coverage_probability=_scalar_or_list(
                _floats(_txt(cov.find(_si("coverageProbability"))))
            ),
            distribution=_txt(cov.find(_si("distribution"))),
        )
    return None


def _parse_real_list(rl: ET.Element) -> tuple[list[float], str, Optional[DCCUncertainty]]:
    """si:realListXMLList → (values, unit, uncertainty)."""
    values = _floats(_txt(rl.find(_si("valueXMLList"))))
    unit = _txt(rl.find(_si("unitXMLList"))) or ""
    unc = None
    exp = rl.find(_si("expandedUncXMLList"))
    if exp is not None:
        unc = DCCUncertainty(
            kind="expandedUncXMLList",
            expanded=_scalar_or_list(
                _floats(_txt(exp.find(_si("uncertaintyXMLList"))))
            ),
            coverage_factor=_scalar_or_list(
                _floats(_txt(exp.find(_si("coverageFactorXMLList"))))
            ),
            coverage_probability=_scalar_or_list(
                _floats(_txt(exp.find(_si("coverageProbabilityXMLList"))))
            ),
            distribution=_txt(exp.find(_si("distributionXMLList"))),
        )
    return values, unit, unc


def _parse_quantity(q: ET.Element) -> DCCQuantity:
    quantity = DCCQuantity(
        name=_parse_text(q.find(_dcc("name"))),
        ref_type=q.get("refType"),
    )

    real = q.find(_si("real"))
    if real is not None:
        val = _txt(real.find(_si("value")))
        quantity.values = [float(val)] if val is not None else []
        quantity.unit = _txt(real.find(_si("unit"))) or ""
        quantity.scalar = True
        quantity.uncertainty = _parse_uncertainty_from_real(real)
        return quantity

    rl = q.find(_si("realListXMLList"))
    if rl is not None:
        quantity.values, quantity.unit, quantity.uncertainty = _parse_real_list(rl)
        quantity.scalar = False
        return quantity

    hybrid = q.find(_si("hybrid"))
    if hybrid is not None:
        lists = hybrid.findall(_si("realListXMLList"))
        if lists:
            quantity.values, quantity.unit, quantity.uncertainty = _parse_real_list(lists[0])
            quantity.scalar = False
            for extra in lists[1:]:
                vals, unit, _ = _parse_real_list(extra)
                quantity.alternates.append((vals, unit))
        return quantity

    # noQuantity / charsXMLList / si:constant 등 — 1차 범위 밖: 값 없이 이름만 유지
    return quantity


def _collect_quantities(data_el: Optional[ET.Element]) -> list[DCCQuantity]:
    """dcc:data 내부의 quantity 수집 (dcc:list는 재귀 평탄화)."""
    out: list[DCCQuantity] = []
    if data_el is None:
        return out
    for child in data_el:
        if child.tag == _dcc("quantity"):
            out.append(_parse_quantity(child))
        elif child.tag == _dcc("list"):
            out.extend(_collect_quantities(child))
    return out


def _parse_used_methods(el: Optional[ET.Element]) -> list[DCCUsedMethod]:
    out: list[DCCUsedMethod] = []
    if el is None:
        return out
    for m in el.findall(_dcc("usedMethod")):
        out.append(
            DCCUsedMethod(
                name=_parse_text(m.find(_dcc("name"))),
                norms=[t for n in m.findall(_dcc("norm")) if (t := _txt(n))],
                references=[t for r in m.findall(_dcc("reference")) if (t := _txt(r))],
                ref_type=m.get("refType"),
            )
        )
    return out


def _parse_measurement_result(mr: ET.Element) -> DCCMeasurementResult:
    result = DCCMeasurementResult(name=_parse_text(mr.find(_dcc("name"))))
    result.used_methods = _parse_used_methods(mr.find(_dcc("usedMethods")))

    me_list = mr.find(_dcc("measuringEquipments"))
    if me_list is not None:
        for me in me_list.findall(_dcc("measuringEquipment")):
            result.measuring_equipments.append(
                DCCMeasuringEquipment(
                    name=_parse_text(me.find(_dcc("name"))),
                    identifications=_parse_identifications(
                        me.find(_dcc("identifications"))
                    ),
                    ref_type=me.get("refType"),
                )
            )

    ic_list = mr.find(_dcc("influenceConditions"))
    if ic_list is not None:
        for ic in ic_list.findall(_dcc("influenceCondition")):
            result.influence_conditions.append(
                DCCInfluenceCondition(
                    name=_parse_text(ic.find(_dcc("name"))),
                    quantities=_collect_quantities(ic.find(_dcc("data"))),
                    ref_type=ic.get("refType"),
                )
            )

    results_el = mr.find(_dcc("results"))
    if results_el is not None:
        for r in results_el.findall(_dcc("result")):
            result.results.append(
                DCCResult(
                    name=_parse_text(r.find(_dcc("name"))),
                    quantities=_collect_quantities(r.find(_dcc("data"))),
                    ref_type=r.get("refType"),
                )
            )
    return result


def _parse_admin(admin: ET.Element) -> DCCAdministrativeData:
    out = DCCAdministrativeData()

    sw_list = admin.find(_dcc("dccSoftware"))
    if sw_list is not None:
        for sw in sw_list.findall(_dcc("software")):
            out.software.append(
                DCCSoftware(
                    name=_parse_text(sw.find(_dcc("name"))),
                    release=_txt(sw.find(_dcc("release"))) or "",
                )
            )

    core = admin.find(_dcc("coreData"))
    if core is not None:
        out.core_data = DCCCoreData(
            country_code=_txt(core.find(_dcc("countryCodeISO3166_1"))) or "",
            used_languages=[
                t for e in core.findall(_dcc("usedLangCodeISO639_1")) if (t := _txt(e))
            ],
            mandatory_languages=[
                t
                for e in core.findall(_dcc("mandatoryLangCodeISO639_1"))
                if (t := _txt(e))
            ],
            unique_identifier=_txt(core.find(_dcc("uniqueIdentifier"))) or "",
            identifications=_parse_identifications(core.find(_dcc("identifications"))),
            receipt_date=_txt(core.find(_dcc("receiptDate"))),
            begin_performance_date=_txt(core.find(_dcc("beginPerformanceDate"))) or "",
            end_performance_date=_txt(core.find(_dcc("endPerformanceDate"))) or "",
            performance_location=_txt(core.find(_dcc("performanceLocation"))) or "",
            issue_date=_txt(core.find(_dcc("issueDate"))),
        )

    items_el = admin.find(_dcc("items"))
    if items_el is not None:
        for item in items_el.findall(_dcc("item")):
            manufacturer = item.find(_dcc("manufacturer"))
            out.items.append(
                DCCItem(
                    name=_parse_text(item.find(_dcc("name"))),
                    manufacturer=(
                        _parse_text(manufacturer.find(_dcc("name")))
                        if manufacturer is not None
                        else None
                    ),
                    model=_txt(item.find(_dcc("model"))),
                    identifications=_parse_identifications(
                        item.find(_dcc("identifications"))
                    ),
                )
            )

    lab = admin.find(_dcc("calibrationLaboratory"))
    if lab is not None:
        out.calibration_laboratory = DCCCalibrationLaboratory(
            code=_txt(lab.find(_dcc("calibrationLaboratoryCode"))),
            contact=_parse_contact(lab.find(_dcc("contact"))),
        )

    persons = admin.find(_dcc("respPersons"))
    if persons is not None:
        for rp in persons.findall(_dcc("respPerson")):
            person = rp.find(_dcc("person"))
            name_text = (
                _parse_text(person.find(_dcc("name"))) if person is not None else None
            )
            # 3.3.0에서 role은 notEmptyStringType (단일 문자열)이지만,
            # 방어적으로 textType(content 자식) 형태도 허용한다.
            role_el = rp.find(_dcc("role"))
            role_text = _parse_text(role_el)
            role = role_text.get() if role_text else _txt(role_el)
            out.resp_persons.append(
                DCCRespPerson(
                    name=name_text.get() if name_text else "",
                    role=role,
                    main_signer=(_txt(rp.find(_dcc("mainSigner"))) or "").lower()
                    == "true",
                )
            )

    out.customer = _parse_contact(admin.find(_dcc("customer")))

    st_list = admin.find(_dcc("statements"))
    if st_list is not None:
        for st in st_list.findall(_dcc("statement")):
            out.statements.append(
                DCCStatement(
                    name=_parse_text(st.find(_dcc("name"))),
                    declaration=_parse_text(st.find(_dcc("declaration"))),
                    norms=[t for n in st.findall(_dcc("norm")) if (t := _txt(n))],
                    references=[
                        t for r in st.findall(_dcc("reference")) if (t := _txt(r))
                    ],
                    ref_type=st.get("refType"),
                )
            )
    return out


# ============================================================
# 공개 API
# ============================================================

Source = Union[str, bytes, Path, IO[Any]]


def _read_source(source: Source) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    if isinstance(source, str):
        stripped = source.lstrip()
        if stripped.startswith("<"):
            return source.encode("utf-8")
        return Path(source).read_bytes()
    if hasattr(source, "read"):
        data = source.read()
        return data.encode("utf-8") if isinstance(data, str) else data
    raise DCCSchemaError(f"Unsupported DCC source type: {type(source)!r}")


def parse_dcc(source: Source) -> DCCDocument:
    """DCC XML을 파싱하여 :class:`DCCDocument` 로 반환.

    Args:
        source: 파일 경로(str/Path), XML 문자열/바이트, 또는 파일 객체

    Raises:
        DCCSchemaError: XML이 아니거나 루트가 dcc:digitalCalibrationCertificate가 아닐 때
    """
    data = _read_source(source)
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise DCCSchemaError(f"Not well-formed XML: {exc}") from exc

    if root.tag != _dcc("digitalCalibrationCertificate"):
        raise DCCSchemaError(
            "Root element is not dcc:digitalCalibrationCertificate "
            f"(namespace {DCC_NS}); got: {root.tag}"
        )

    doc = DCCDocument(schema_version=root.get("schemaVersion", ""))

    admin = root.find(_dcc("administrativeData"))
    if admin is not None:
        doc.administrative_data = _parse_admin(admin)

    mrs = root.find(_dcc("measurementResults"))
    if mrs is not None:
        for mr in mrs.findall(_dcc("measurementResult")):
            doc.measurement_results.append(_parse_measurement_result(mr))

    comment = root.find(_dcc("comment"))
    doc.comment = _txt(comment)
    return doc


def check_required_structure(doc: DCCDocument) -> list[str]:
    """DCC 3.3.0 스키마의 필수(minOccurs≥1) 요소 관점에서 누락 항목을 나열.

    XSD 정식 검증의 대체가 아니라, xmlschema 미설치 환경에서 쓰는
    경량 구조 점검이다 (요소 순서·타입·enum 값 검증은 하지 않는다).

    Returns:
        누락 항목 설명 리스트 (비어 있으면 필수 구조 충족)
    """
    missing: list[str] = []
    admin = doc.administrative_data
    core = admin.core_data

    if not admin.software:
        missing.append("administrativeData/dccSoftware/software")
    if not core.country_code:
        missing.append("coreData/countryCodeISO3166_1")
    if not core.used_languages:
        missing.append("coreData/usedLangCodeISO639_1")
    if not core.mandatory_languages:
        missing.append("coreData/mandatoryLangCodeISO639_1")
    if not core.unique_identifier:
        missing.append("coreData/uniqueIdentifier")
    if not core.begin_performance_date:
        missing.append("coreData/beginPerformanceDate")
    if not core.end_performance_date:
        missing.append("coreData/endPerformanceDate")
    if core.performance_location not in (
        "laboratory",
        "customer",
        "laboratoryBranch",
        "customerBranch",
        "other",
    ):
        missing.append("coreData/performanceLocation (enum)")
    if not admin.items:
        missing.append("administrativeData/items/item")
    lab = admin.calibration_laboratory
    if lab.contact is None or not lab.contact.name:
        missing.append("administrativeData/calibrationLaboratory/contact/name")
    if not admin.resp_persons:
        missing.append("administrativeData/respPersons/respPerson")
    if admin.customer is None or not admin.customer.name:
        missing.append("administrativeData/customer/name")
    if not doc.measurement_results:
        missing.append("measurementResults/measurementResult")
    for i, mr in enumerate(doc.measurement_results):
        if not mr.name:
            missing.append(f"measurementResult[{i}]/name")
        if not mr.results:
            missing.append(f"measurementResult[{i}]/results/result")
    return missing


def validate_dcc(
    xml_source: Source,
    xsd_source: Optional[Union[str, Path]] = None,
) -> list[str]:
    """선택 의존성 xmlschema로 정식 XSD 검증을 수행.

    Args:
        xml_source: 검증할 DCC XML (경로/문자열/바이트)
        xsd_source: dcc.xsd 경로 또는 dcc.xsd가 들어 있는 디렉터리.
            None이면 공식 URL(:data:`OFFICIAL_XSD_URL`)에서 로드한다 (네트워크 필요).

    Returns:
        검증 오류 메시지 리스트 (비어 있으면 스키마 적합)

    Raises:
        DCCSchemaError: xmlschema 미설치, 또는 XSD 로드 실패 시
    """
    try:
        import xmlschema  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - 환경 의존
        raise DCCSchemaError(
            "XSD validation requires the optional dependency 'xmlschema' "
            "(pip install xmlschema). "
            "Without it, use check_required_structure() for a light structural check."
        ) from exc

    if xsd_source is None:
        xsd_path: Union[str, Path] = OFFICIAL_XSD_URL
    else:
        xsd_path = Path(xsd_source)
        if xsd_path.is_dir():
            xsd_path = xsd_path / "dcc.xsd"

    try:
        schema = xmlschema.XMLSchema(str(xsd_path))
    except Exception as exc:
        raise DCCSchemaError(f"Failed to load DCC XSD from {xsd_path}: {exc}") from exc

    data = _read_source(xml_source)
    return [str(err) for err in schema.iter_errors(BytesIO(data))]
