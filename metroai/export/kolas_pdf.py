"""KOLAS 교정성적서 PDF 자동 생성.

KOLAS-G-004 교정성적서 양식에 맞는 PDF를 reportlab으로 생성.
"""

from __future__ import annotations

import math
from io import BytesIO
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..core.gum import GUMResult


def _get_korean_font_name() -> str:
    """사용 가능한 한글 폰트 이름을 반환."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        return "HYSMyeongJo-Medium"
    except Exception:
        pass

    try:
        from reportlab.pdfbase.ttfonts import TTFont
        import os

        # Windows 기본 한글 폰트 시도
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            os.path.join(os.path.dirname(__file__), "../../fonts/NanumGothic.ttf"),
        ]
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont("KoreanFont", path))
                return "KoreanFont"
    except Exception:
        pass

    return "Helvetica"


def export_calibration_certificate_pdf(
    result: GUMResult,
    cert_info: dict,
    filepath: Optional[str] = None,
) -> BytesIO:
    """KOLAS 교정성적서 PDF 생성.

    Args:
        result: GUMResult 계산 결과
        cert_info: 성적서 정보 딕셔너리
        filepath: 저장 경로 (None이면 BytesIO 반환)

    Returns:
        BytesIO 객체
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    font_name = _get_korean_font_name()
    elements = []

    # 스타일 정의
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=10 * mm,
    )
    heading_style = ParagraphStyle(
        "CertHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=12,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )
    normal_style = ParagraphStyle(
        "CertNormal",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
    )
    center_style = ParagraphStyle(
        "CertCenter",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        alignment=TA_CENTER,
    )
    footer_style = ParagraphStyle(
        "CertFooter",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey,
    )

    table_style = TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.267, 0.447, 0.769, 0.15)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])

    header_table_style = TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.267, 0.447, 0.769)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), font_name),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ])

    # ─── 1. 제목 ───
    cert_number = cert_info.get("cert_number", "")
    elements.append(Paragraph("교 정 성 적 서", title_style))
    if cert_number:
        elements.append(Paragraph(f"성적서 번호: {cert_number}", center_style))
    elements.append(Spacer(1, 5 * mm))

    # ─── 2. 교정기관 정보 ───
    elements.append(Paragraph("1. 교정기관", heading_style))
    org_data = [
        ["교정기관", cert_info.get("cal_org", "")],
        ["인정번호", cert_info.get("cal_org_kolas_id", "")],
        ["소재지", cert_info.get("cal_org_address", "")],
    ]
    col_widths = [40 * mm, 130 * mm]
    t = Table(org_data, colWidths=col_widths)
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 3 * mm))

    # ─── 3. 의뢰자 정보 ───
    elements.append(Paragraph("2. 의뢰자", heading_style))
    client_data = [
        ["의뢰기관명", cert_info.get("client_org", "")],
        ["소재지", cert_info.get("client_address", "")],
    ]
    t = Table(client_data, colWidths=col_widths)
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 3 * mm))

    # ─── 4. 교정 대상 정보 ───
    elements.append(Paragraph("3. 교정 대상", heading_style))
    equip_data = [
        ["교정 대상 기기", cert_info.get("equipment_name", "")],
        ["제조사 / 모델", f"{cert_info.get('manufacturer', '')} / {cert_info.get('model', '')}"],
        ["일련번호", cert_info.get("serial_number", "")],
        ["교정일", cert_info.get("cal_date", "")],
        ["교정 장소", cert_info.get("cal_location", "")],
        [
            "환경 조건",
            f"온도: {cert_info.get('temperature', '')} C, "
            f"습도: {cert_info.get('humidity', '')} %",
        ],
    ]
    t = Table(equip_data, colWidths=col_widths)
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 5 * mm))

    # ─── 5. 불확도 예산표 ───
    elements.append(Paragraph("4. 불확도 예산표", heading_style))

    budget_headers = [
        "불확도 성분", "기호", "평가유형", "분포",
        "u(xi)", "ci", "|ci|u(xi)", "기여율(%)",
    ]
    budget_data = [budget_headers]

    for comp in result.components:
        dof_str = "inf" if math.isinf(comp.dof) else f"{comp.dof:.0f}"
        dist_name = comp.source.distribution.value if comp.source.eval_type == "B" else "-"
        budget_data.append([
            comp.source.name,
            comp.source.symbol,
            f"{comp.source.eval_type} (v={dof_str})",
            dist_name,
            f"{comp.std_uncertainty:.4e}",
            f"{comp.sensitivity_coeff:.4e}",
            f"{comp.contribution:.4e}",
            f"{comp.percent_contribution:.1f}",
        ])

    budget_col_widths = [30 * mm, 18 * mm, 20 * mm, 20 * mm, 22 * mm, 22 * mm, 22 * mm, 18 * mm]
    t = Table(budget_data, colWidths=budget_col_widths)
    t.setStyle(header_table_style)
    elements.append(t)
    elements.append(Spacer(1, 3 * mm))

    # ─── 6. 결과 요약 ───
    elements.append(Paragraph("5. 측정불확도 결과", heading_style))

    dof_display = "inf" if math.isinf(result.effective_dof) else f"{result.effective_dof:.0f}"
    summary_data = [
        ["합성표준불확도 uc(y)", f"{result.combined_uncertainty:.4e}"],
        ["유효자유도 veff", dof_display],
        [
            f"포함인자 k (신뢰수준 {result.confidence_level * 100:.0f}%)",
            f"{result.coverage_factor:.2f}",
        ],
        ["확장불확도 U = k * uc(y)", f"{result.expanded_uncertainty:.4e}"],
    ]
    t = Table(summary_data, colWidths=[80 * mm, 90 * mm])
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 3 * mm))

    elements.append(Paragraph(
        f"<b>{result.uncertainty_statement()}</b>",
        center_style,
    ))
    elements.append(Spacer(1, 8 * mm))

    # ─── 7. 푸터 ───
    elements.append(Paragraph(
        "본 성적서는 교정 당시의 상태에 대한 것입니다.",
        footer_style,
    ))
    elements.append(Paragraph(
        "KOLAS 인정마크가 있는 교정성적서는 ILAC MRA 적용을 받습니다.",
        footer_style,
    ))
    elements.append(Spacer(1, 8 * mm))

    # 서명란
    sig_data = [
        ["교정원", "검토자", "책임자"],
        [
            cert_info.get("calibrator_name", ""),
            cert_info.get("reviewer_name", ""),
            cert_info.get("approver_name", ""),
        ],
        ["(서명)", "(서명)", "(서명)"],
    ]
    t = Table(sig_data, colWidths=[55 * mm, 55 * mm, 55 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.267, 0.447, 0.769, 0.15)),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)

    # PDF 빌드
    doc.build(elements)
    buf.seek(0)

    if filepath:
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        buf.seek(0)

    return buf
