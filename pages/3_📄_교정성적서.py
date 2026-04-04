"""교정성적서 PDF 생성 페이지."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.core.distributions import DistributionType, UncertaintySource
from metroai.core.gum import GUMCalculator
from metroai.core.model import MeasurementModel
from metroai.export.kolas_pdf import export_calibration_certificate_pdf

st.set_page_config(
    page_title="MetroAI — 교정성적서",
    page_icon="📄",
    layout="wide",
)

st.header("📄 KOLAS 교정성적서 PDF 생성")
st.markdown("불확도 계산 결과를 입력하고, KOLAS 양식 교정성적서 PDF를 생성합니다.")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("1. 교정기관 정보")
    cert_number = st.text_input("성적서 번호", value="CAL-2026-001")
    cal_org = st.text_input("교정기관명")
    cal_org_kolas = st.text_input("KOLAS 인정번호", value="KOLAS-")
    cal_org_addr = st.text_input("교정기관 소재지")

    st.subheader("2. 의뢰자 정보")
    client_org = st.text_input("의뢰기관명")
    client_addr = st.text_input("의뢰기관 소재지")

with col_right:
    st.subheader("3. 교정 대상")
    equip_name = st.text_input("교정 대상 기기")
    manufacturer = st.text_input("제조사")
    model_name = st.text_input("모델")
    serial = st.text_input("일련번호")
    cal_date = st.text_input("교정일", value="2026-04-04")
    cal_location = st.text_input("교정 장소")
    temperature = st.text_input("온도 조건", value="20.0 +/- 0.5")
    humidity = st.text_input("습도 조건", value="50 +/- 10")

st.divider()
st.subheader("4. 불확도 결과 (간단 입력)")
st.markdown("*불확도 계산 페이지에서 계산한 결과가 있다면, 여기에 직접 2개 성분을 입력하여 테스트 PDF를 생성할 수 있습니다.*")

c1, c2 = st.columns(2)
with c1:
    src1_name = st.text_input("성분1 이름", value="반복성")
    src1_u = st.number_input("성분1 표준불확도 u", value=0.01, format="%.4e")
with c2:
    src2_name = st.text_input("성분2 이름", value="표준기 교정")
    src2_u = st.number_input("성분2 표준불확도 u", value=0.02, format="%.4e")

st.divider()
st.subheader("5. 서명")
c_s1, c_s2, c_s3 = st.columns(3)
with c_s1:
    calibrator = st.text_input("교정원")
with c_s2:
    reviewer = st.text_input("검토자")
with c_s3:
    approver = st.text_input("책임자")

if st.button("📄 교정성적서 PDF 생성", type="primary", use_container_width=True):
    model = MeasurementModel("a + b", symbol_names=["a", "b"])
    sources = [
        UncertaintySource(name=src1_name, symbol="a", eval_type="B", value=0.0, std_uncertainty=src1_u),
        UncertaintySource(name=src2_name, symbol="b", eval_type="B", value=0.0, std_uncertainty=src2_u),
    ]
    calc = GUMCalculator(model, sources, measurand_name="Y")
    result = calc.calculate()

    cert_info = {
        "cert_number": cert_number,
        "cal_org": cal_org,
        "cal_org_kolas_id": cal_org_kolas,
        "cal_org_address": cal_org_addr,
        "client_org": client_org,
        "client_address": client_addr,
        "equipment_name": equip_name,
        "manufacturer": manufacturer,
        "model": model_name,
        "serial_number": serial,
        "cal_date": cal_date,
        "cal_location": cal_location,
        "temperature": temperature,
        "humidity": humidity,
        "calibrator_name": calibrator,
        "reviewer_name": reviewer,
        "approver_name": approver,
    }

    pdf_buf = export_calibration_certificate_pdf(result, cert_info)

    st.success("PDF 생성 완료!")
    st.download_button(
        "📥 PDF 다운로드",
        data=pdf_buf,
        file_name=f"교정성적서_{cert_number}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
