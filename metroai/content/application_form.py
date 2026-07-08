"""KOLAS 인정 신청서 자동 작성 — v0.7.0 P0-3.

KAB-F-21 양식의 정확한 사본을 보유하지 않으므로, ISO/IEC 17025 기반
**generic 인정 신청 양식** 을 ReportLab 으로 PDF 생성. 실제 신청 시 KAB
공식 양식과 비교하여 보강 필수.

⚠️ 본 PDF 는 generic 양식입니다. 실제 KAB-F-21 (또는 최신 양식) 과 다를
   수 있으니 KAB (knab.go.kr) 에서 최신 양식 확인 후 본 PDF 의 내용을
   참고용으로 사용하세요.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO


@dataclass
class OrganizationProfile:
    """조직 프로필 — 인정 신청서의 모든 필드 source."""

    org_name_ko: str = ""
    org_name_en: str = ""
    representative_name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    business_registration_no: str = ""

    # 인정 신청 정보
    accreditation_type: str = "시험"  # 시험 / 교정 / RMP / 검사
    accreditation_domain: str = "general"  # sem / tem / afm / ocd / general
    accreditation_scope_summary: str = ""  # e.g. "SEM-EDS 정량 조성 분석, 측정 범위 0.1-100 wt%"
    iso_standards_applied: list[str] = field(default_factory=list)

    # 측정 범위
    measurement_range: str = ""
    typical_uncertainty: str = ""  # CMC 형식

    # 인력
    quality_manager_name: str = ""
    quality_manager_cert: str = ""
    technical_manager_name: str = ""
    technical_manager_cert: str = ""
    n_calibration_engineers: int = 0
    n_test_engineers: int = 0

    # 장비
    main_equipment_list: list[dict] = field(default_factory=list)
    # 각 entry: {model, manufacturer, year, calibration_date, traceability}

    # 환경
    environmental_control: str = ""  # e.g. "20 ± 1°C, 50 ± 10% RH"

    # 표준기
    reference_standards: list[dict] = field(default_factory=list)
    # 각 entry: {name, source, certificate_no, certified_value, certified_uncertainty}

    # 신청자 의견
    quality_system_implementation_date: str = ""  # YYYY-MM-DD
    internal_audit_completed: bool = False
    pt_participation_history: str = ""


def generate_application_pdf(profile: OrganizationProfile) -> bytes:
    """OrganizationProfile 데이터로 ISO 17025 generic 인정 신청서 PDF 생성.

    Returns: PDF bytes
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    # Font registration (Korean support)
    # ReportLab default Helvetica won't render Korean. Try to use Pretendard or fallback.
    korean_font = "Helvetica"  # fallback
    try:
        # Streamlit Cloud / Linux 에서 흔히 보이는 path
        for f in [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/malgun.ttf",
        ]:
            try:
                pdfmetrics.registerFont(TTFont("KoreanFont", f))
                korean_font = "KoreanFont"
                break
            except Exception:
                continue
    except Exception:
        pass

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title-K",
        parent=styles["Heading1"],
        fontName=korean_font,
        fontSize=18,
        alignment=1,  # center
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        "H2-K",
        parent=styles["Heading2"],
        fontName=korean_font,
        fontSize=13,
        textColor=colors.HexColor("#1E40AF"),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body-K",
        parent=styles["BodyText"],
        fontName=korean_font,
        fontSize=10,
        leading=14,
    )
    small_style = ParagraphStyle(
        "Small-K",
        parent=styles["BodyText"],
        fontName=korean_font,
        fontSize=8,
        textColor=colors.HexColor("#475569"),
        leading=10,
    )

    story = []

    # ── 제목
    story.append(Paragraph("시험·교정 기관 인정 신청서", title_style))
    story.append(
        Paragraph(
            "(ISO/IEC 17025:2017 기반 — KAB-F-21 양식 참고용 generic 양식)",
            small_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            f"작성일: {datetime.now().strftime('%Y-%m-%d')} · "
            f"MetroAI v0.7.0 P0-3 generated",
            small_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # ── 1. 신청 기관 정보
    story.append(Paragraph("1. 신청 기관 정보", h2_style))
    table1_data = [
        ["기관명 (국문)", profile.org_name_ko or "-"],
        ["기관명 (영문)", profile.org_name_en or "-"],
        ["대표자", profile.representative_name or "-"],
        ["사업자등록번호", profile.business_registration_no or "-"],
        ["주소", profile.address or "-"],
        ["연락처", profile.phone or "-"],
        ["이메일", profile.email or "-"],
        ["웹사이트", profile.website or "-"],
    ]
    table1 = Table(table1_data, colWidths=[4.5 * cm, 12 * cm])
    table1.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), korean_font),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1E40AF")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table1)

    # ── 2. 인정 신청 범위
    story.append(Paragraph("2. 인정 신청 범위", h2_style))
    table2_data = [
        ["인정 분야", profile.accreditation_type or "-"],
        ["측정 분야", profile.accreditation_domain.upper() if profile.accreditation_domain else "-"],
        ["신청 범위 요약", profile.accreditation_scope_summary or "-"],
        ["적용 ISO 표준", ", ".join(profile.iso_standards_applied) if profile.iso_standards_applied else "-"],
        ["측정 범위", profile.measurement_range or "-"],
        ["측정 불확도 (CMC)", profile.typical_uncertainty or "-"],
    ]
    table2 = Table(table2_data, colWidths=[4.5 * cm, 12 * cm])
    table2.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), korean_font),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1E40AF")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table2)

    # ── 3. 인력
    story.append(Paragraph("3. 인력 정보 (ISO/IEC 17025 6.2)", h2_style))
    table3_data = [
        ["구분", "이름", "자격"],
        ["품질책임자", profile.quality_manager_name or "-", profile.quality_manager_cert or "-"],
        ["기술책임자", profile.technical_manager_name or "-", profile.technical_manager_cert or "-"],
        ["교정 엔지니어", f"{profile.n_calibration_engineers} 명", "ISO/IEC 17025 training"],
        ["시험 엔지니어", f"{profile.n_test_engineers} 명", "ISO/IEC 17025 training"],
    ]
    table3 = Table(table3_data, colWidths=[4.5 * cm, 5 * cm, 7 * cm])
    table3.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), korean_font),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table3)

    # ── 4. 주요 장비
    story.append(Paragraph("4. 주요 측정 장비 (ISO/IEC 17025 6.4)", h2_style))
    if profile.main_equipment_list:
        eq_data = [["모델", "제조사", "도입년도", "교정 일자", "Traceability"]]
        for eq in profile.main_equipment_list:
            eq_data.append([
                eq.get("model", "-"),
                eq.get("manufacturer", "-"),
                str(eq.get("year", "-")),
                eq.get("calibration_date", "-"),
                eq.get("traceability", "-"),
            ])
        eq_table = Table(eq_data, colWidths=[4 * cm, 3 * cm, 2 * cm, 3 * cm, 4.5 * cm])
        eq_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), korean_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#06B6D4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(eq_table)
    else:
        story.append(Paragraph("(장비 정보 미입력)", small_style))

    # ── 5. 표준기 / 기준 시료
    story.append(Paragraph("5. 표준기 / 기준 시료 (ISO/IEC 17025 6.5)", h2_style))
    if profile.reference_standards:
        ref_data = [["표준명", "출처", "인증서 번호", "인증값", "인증 불확도 (k=2)"]]
        for r in profile.reference_standards:
            ref_data.append([
                r.get("name", "-"),
                r.get("source", "-"),
                r.get("certificate_no", "-"),
                str(r.get("certified_value", "-")),
                str(r.get("certified_uncertainty", "-")),
            ])
        ref_table = Table(ref_data, colWidths=[3.5 * cm, 3 * cm, 3.5 * cm, 3 * cm, 3.5 * cm])
        ref_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), korean_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10B981")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(ref_table)
    else:
        story.append(Paragraph("(표준기 정보 미입력)", small_style))

    # ── 6. 환경 조건
    story.append(Paragraph("6. 환경 조건 (ISO/IEC 17025 6.3)", h2_style))
    story.append(Paragraph(profile.environmental_control or "-", body_style))

    # ── 7. 품질 시스템
    story.append(Paragraph("7. 품질 시스템 (ISO/IEC 17025 8장)", h2_style))
    qs_data = [
        ["품질 시스템 도입 일자", profile.quality_system_implementation_date or "-"],
        ["내부 audit 완료 여부", "예 ✓" if profile.internal_audit_completed else "아니오 ✗"],
        ["PT 참가 이력 (ISO 17043)", profile.pt_participation_history or "-"],
    ]
    qs_table = Table(qs_data, colWidths=[6 * cm, 10.5 * cm])
    qs_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), korean_font),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1E40AF")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(qs_table)

    # ── 푸터 + 면책
    story.append(Spacer(1, 0.8 * cm))
    story.append(
        Paragraph(
            "⚠️ <b>면책 고지:</b> 본 PDF 는 ISO/IEC 17025 기반 <b>generic 인정 신청 양식</b>입니다. "
            "실제 KAB-F-21 또는 최신 KAB 양식과 다를 수 있으니, KAB (knab.go.kr) 의 최신 양식을 "
            "확인 후 본 양식의 내용을 참고로 사용하세요. MetroAI v0.7.0 P0-3 자동 생성.",
            small_style,
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def get_default_profile_for_domain(domain: str) -> OrganizationProfile:
    """분야별 기본 프로필 — 사용자가 처음 폼 열 때 예시 값으로 입력됨."""
    profile = OrganizationProfile()
    profile.org_name_ko = "(주)예시 측정 기관"
    profile.org_name_en = "Example Measurement Lab Inc."
    profile.representative_name = "홍길동"
    profile.address = "서울특별시 강남구 테헤란로 123"
    profile.phone = "031-XXX-XXXX"
    profile.email = "contact@example.kr"
    profile.website = "https://example.kr"
    profile.business_registration_no = "XXX-XX-XXXXX"
    profile.environmental_control = "온도 20 ± 1°C, 상대습도 50 ± 10% RH (chamber 1대)"
    profile.quality_manager_name = "(미정)"
    profile.quality_manager_cert = "ISO/IEC 17025 internal auditor training 수료 예정"
    profile.technical_manager_name = "(미정)"
    profile.technical_manager_cert = "(미정)"

    # 분야별 기본값
    if domain == "sem":
        profile.accreditation_type = "시험"
        profile.accreditation_domain = "sem"
        profile.accreditation_scope_summary = (
            "SEM-EDS quantitative composition analysis, "
            "SEM magnification calibration, particle size analysis"
        )
        profile.iso_standards_applied = ["ISO/IEC 17025:2017", "ISO 22489:2016", "ISO 16700:2016"]
        profile.measurement_range = "EDS 정량 분석: 0.1-100 wt% / Magnification: 10x-300,000x"
        profile.typical_uncertainty = "EDS 정량: 2-5% (k=2) / Magnification: 0.5-1% (k=2)"
        profile.main_equipment_list = [
            {
                "model": "Thermo Scientific Quanta 250 FEG",
                "manufacturer": "Thermo Fisher",
                "year": 2020,
                "calibration_date": "2025-06-01",
                "traceability": "Thermo internal + NIST SRM-485 비교",
            },
            {
                "model": "Oxford X-Max 80 EDS",
                "manufacturer": "Oxford Instruments",
                "year": 2020,
                "calibration_date": "2025-06-15",
                "traceability": "NIST SRM-485 Au-Cu",
            },
        ]
        profile.reference_standards = [
            {
                "name": "NIST SRM-485 Au-Cu 50:50",
                "source": "NIST",
                "certificate_no": "SRM-485",
                "certified_value": "Au 50.31 wt%, Cu 49.69 wt%",
                "certified_uncertainty": "0.15 wt% (k=2)",
            },
            {
                "name": "463 nm pitch Si grating",
                "source": "NIST",
                "certificate_no": "SRM-2090",
                "certified_value": "463.0 nm",
                "certified_uncertainty": "0.3 nm (k=2)",
            },
        ]
    elif domain == "tem":
        profile.accreditation_type = "시험"
        profile.accreditation_domain = "tem"
        profile.accreditation_scope_summary = (
            "TEM lattice constant measurement, thin film composition (EDS/EELS)"
        )
        profile.iso_standards_applied = ["ISO/IEC 17025:2017", "ISO 29301:2017", "ISO 14709-1:2002"]
        profile.measurement_range = "격자상수 1-10 Å / 박막 두께 1-1000 nm"
        profile.typical_uncertainty = "격자상수: 0.5-1% (k=2) / 박막 두께: 2-3% (k=2)"
        profile.main_equipment_list = [
            {
                "model": "JEOL JEM-ARM200F (Cs-corrected)",
                "manufacturer": "JEOL",
                "year": 2018,
                "calibration_date": "2025-04-01",
                "traceability": "Si SRM 격자상수 5.4310 Å",
            },
        ]
        profile.reference_standards = [
            {
                "name": "Si single crystal (lattice ref)",
                "source": "NIST",
                "certificate_no": "SRM-640e",
                "certified_value": "a = 5.43102 Å",
                "certified_uncertainty": "0.00008 Å (k=2)",
            },
        ]
    elif domain == "afm":
        profile.accreditation_type = "시험"
        profile.accreditation_domain = "afm"
        profile.accreditation_scope_summary = (
            "AFM surface roughness (Sa, Sq, Sz per ISO 25178-2), step height measurement"
        )
        profile.iso_standards_applied = ["ISO/IEC 17025:2017", "ISO 25178-2:2012", "ISO 11952:2019"]
        profile.measurement_range = "Sa: 0.1 nm-1 μm / Scan area: 1×1 μm-100×100 μm"
        profile.typical_uncertainty = "Sa: 0.5-2 nm (k=2) / Step height: 0.5-1 nm (k=2)"
        profile.main_equipment_list = [
            {
                "model": "Bruker Dimension Icon",
                "manufacturer": "Bruker",
                "year": 2019,
                "calibration_date": "2025-05-15",
                "traceability": "NIST step height standard (18 nm)",
            },
        ]
        profile.reference_standards = [
            {
                "name": "Step height standard 18 nm",
                "source": "NIST",
                "certificate_no": "SRM-2079",
                "certified_value": "17.99 nm",
                "certified_uncertainty": "0.5 nm (k=2)",
            },
        ]
    elif domain == "ocd":
        profile.accreditation_type = "시험"
        profile.accreditation_domain = "ocd"
        profile.accreditation_scope_summary = (
            "OCD (Optical Critical Dimension) measurement for patterned wafers, "
            "CD/sidewall angle/height via RCWA library matching"
        )
        profile.iso_standards_applied = ["ISO/IEC 17025:2017", "SEMI MF-1789-1112", "ISO 17078-2:2014"]
        profile.measurement_range = "CD: 10-100 nm / Sidewall angle: 80-90° / Wavelength: 200-800 nm"
        profile.typical_uncertainty = "CD: 1-2 nm (k=2) / Sidewall angle: 0.5° (k=2)"
        profile.main_equipment_list = [
            {
                "model": "KLA SpectraFilm F5",
                "manufacturer": "KLA Corporation",
                "year": 2021,
                "calibration_date": "2025-05-01",
                "traceability": "KLA in-house + CD-SEM cross-check",
            },
        ]
        profile.reference_standards = [
            {
                "name": "Line/space patterned wafer (45 nm)",
                "source": "VLSI Standards (Bruker)",
                "certificate_no": "VLSI-OCD-2024-005",
                "certified_value": "CD 45.2 nm",
                "certified_uncertainty": "0.5 nm (k=2)",
            },
        ]
    else:  # general
        profile.accreditation_type = "교정"
        profile.accreditation_domain = "general"
        profile.accreditation_scope_summary = (
            "Block gauge calibration (5-100 mm), micrometer calibration, electrical calibration, mass"
        )
        profile.iso_standards_applied = [
            "ISO/IEC 17025:2017",
            "ISO/IEC Guide 98-3:2008 (GUM)",
            "ISO 13528:2022",
        ]
        profile.measurement_range = "블록게이지: 0.5-1000 mm / 마이크로미터: 0-300 mm"
        profile.typical_uncertainty = "블록게이지 100mm: 0.05 μm (k=2) / 마이크로미터: 1-5 μm (k=2)"
        profile.main_equipment_list = [
            {
                "model": "Mahr 828 CIM (block gauge comparator)",
                "manufacturer": "Mahr",
                "year": 2015,
                "calibration_date": "2025-03-15",
                "traceability": "KRISS 경유",
            },
        ]
        profile.reference_standards = [
            {
                "name": "Grade K block gauge set",
                "source": "KRISS",
                "certificate_no": "KRISS-2024-CL-001",
                "certified_value": "100 mm",
                "certified_uncertainty": "0.05 μm (k=2)",
            },
        ]

    return profile
