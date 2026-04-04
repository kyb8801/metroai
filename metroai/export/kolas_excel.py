"""KOLAS 양식 불확도 예산표 엑셀 출력.

KOLAS-G-002 양식에 맞는 불확도 예산표를 .xlsx 파일로 생성.
"""

from __future__ import annotations

import math
from io import BytesIO
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from ..core.gum import GUMResult


def export_budget_excel(
    result: GUMResult,
    filepath: Optional[str] = None,
) -> BytesIO:
    """불확도 예산표를 KOLAS 양식 엑셀로 출력.

    Args:
        result: GUMResult 계산 결과
        filepath: 저장 경로 (None이면 BytesIO 반환)

    Returns:
        BytesIO 객체 (Streamlit 다운로드용)
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "불확도 예산표"

    # 스타일 정의
    header_font = Font(name="맑은 고딕", bold=True, size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(name="맑은 고딕", bold=True, size=11, color="FFFFFF")
    cell_font = Font(name="맑은 고딕", size=10)
    title_font = Font(name="맑은 고딕", bold=True, size=14)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 제목
    ws.merge_cells("A1:H1")
    cell = ws["A1"]
    cell.value = "측정불확도 예산표 (Uncertainty Budget)"
    cell.font = title_font
    cell.alignment = Alignment(horizontal="center")

    # 측정 모델
    ws.merge_cells("A3:B3")
    ws["A3"].value = "측정 모델:"
    ws["A3"].font = Font(name="맑은 고딕", bold=True, size=10)
    ws.merge_cells("C3:H3")
    ws["C3"].value = f"Y = {result.model_expression}"
    ws["C3"].font = cell_font

    # 헤더 (Row 5)
    headers = [
        "불확도 성분\n(Source)",
        "기호\n(Symbol)",
        "평가 유형\n(Type)",
        "분포\n(Distribution)",
        "표준불확도\nu(xi)",
        "민감계수\nci",
        "불확도 기여\n|ci|·u(xi)",
        "기여율\n(%)",
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col)
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = center
        cell.border = thin_border

    # 열 너비 설정
    widths = [25, 10, 10, 15, 15, 15, 15, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # 데이터 행
    for row_idx, comp in enumerate(result.components, 6):
        src = comp.source
        dist_name = src.distribution.value if src.eval_type == "B" else "-"
        dof_str = "∞" if math.isinf(comp.dof) else f"{comp.dof:.0f}"

        values = [
            src.name,
            src.symbol,
            f"{src.eval_type}형 (ν={dof_str})",
            dist_name,
            f"{comp.std_uncertainty:.4e}",
            f"{comp.sensitivity_coeff:.4e}",
            f"{comp.contribution:.4e}",
            f"{comp.percent_contribution:.1f}",
        ]

        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col)
            cell.value = val
            cell.font = cell_font
            cell.alignment = center
            cell.border = thin_border

    # 결과 요약 (데이터 행 아래)
    summary_row = 6 + len(result.components) + 1

    ws.merge_cells(f"A{summary_row}:D{summary_row}")
    ws[f"A{summary_row}"].value = "합성표준불확도 uc(y)"
    ws[f"A{summary_row}"].font = header_font
    ws.merge_cells(f"E{summary_row}:H{summary_row}")
    ws[f"E{summary_row}"].value = f"{result.combined_uncertainty:.4e}"
    ws[f"E{summary_row}"].font = Font(name="맑은 고딕", bold=True, size=11, color="CC0000")
    ws[f"E{summary_row}"].alignment = center

    summary_row += 1
    ws.merge_cells(f"A{summary_row}:D{summary_row}")
    ws[f"A{summary_row}"].value = "유효자유도 νeff"
    ws[f"A{summary_row}"].font = header_font
    ws.merge_cells(f"E{summary_row}:H{summary_row}")
    dof_display = "∞" if math.isinf(result.effective_dof) else f"{result.effective_dof:.0f}"
    ws[f"E{summary_row}"].value = dof_display
    ws[f"E{summary_row}"].alignment = center

    summary_row += 1
    ws.merge_cells(f"A{summary_row}:D{summary_row}")
    ws[f"A{summary_row}"].value = f"포함인자 k (신뢰수준 {result.confidence_level*100:.0f}%)"
    ws[f"A{summary_row}"].font = header_font
    ws.merge_cells(f"E{summary_row}:H{summary_row}")
    ws[f"E{summary_row}"].value = f"{result.coverage_factor:.2f}"
    ws[f"E{summary_row}"].alignment = center

    summary_row += 1
    ws.merge_cells(f"A{summary_row}:D{summary_row}")
    ws[f"A{summary_row}"].value = "확장불확도 U = k · uc(y)"
    ws[f"A{summary_row}"].font = Font(name="맑은 고딕", bold=True, size=12)
    ws.merge_cells(f"E{summary_row}:H{summary_row}")
    ws[f"E{summary_row}"].value = f"{result.expanded_uncertainty:.4e}"
    ws[f"E{summary_row}"].font = Font(name="맑은 고딕", bold=True, size=12, color="CC0000")
    ws[f"E{summary_row}"].alignment = center

    summary_row += 2
    ws.merge_cells(f"A{summary_row}:H{summary_row}")
    ws[f"A{summary_row}"].value = result.uncertainty_statement()
    ws[f"A{summary_row}"].font = Font(name="맑은 고딕", italic=True, size=10)
    ws[f"A{summary_row}"].alignment = Alignment(horizontal="center")

    # 저장
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    if filepath:
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        buf.seek(0)

    return buf
