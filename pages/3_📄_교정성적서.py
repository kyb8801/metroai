"""교정성적서 페이지 — 3탭 구조 (v0.5.0).

Tab 1: 교정성적서 PDF 생성 (기존)
Tab 2: KOLAS 심사 서류 체크리스트 (NEW)
Tab 3: 예시 다운로드 (NEW)
"""

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
from metroai.ui.org_profile import load_profile, render_profile_form, get_profile_value

st.set_page_config(
    page_title="MetroAI — 교정성적서",
    page_icon="📄",
    layout="wide",
)

st.header("📄 교정성적서 · 심사 서류")
st.caption("교정성적서 PDF 생성, KOLAS 심사 서류 체크리스트, 예시 다운로드를 한 곳에서.")

# ──────────────────────────────────────────
# 3탭 구조
# ──────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📄 성적서 생성", "📋 심사 서류 체크리스트", "📥 예시 다운로드"])

# ──────────────────────────────────────────
# Tab 1: 교정성적서 PDF 생성 (기존 기능)
# ──────────────────────────────────────────
with tab1:
    st.subheader("KOLAS 교정성적서 PDF 생성")
    st.markdown("불확도 계산 결과를 입력하고, KOLAS 양식 교정성적서 PDF를 생성합니다.")

    # 프로필 자동 로드
    _profile = load_profile()
    _has_profile = bool(_profile.get("org_name", ""))

    if _has_profile:
        st.success(f"✅ 기관 프로필 자동 적용: **{_profile['org_name']}** ({_profile.get('kolas_id', '')})")
    else:
        with st.expander("💡 기관 프로필을 설정하면 매번 입력할 필요가 없습니다", expanded=False):
            render_profile_form(location="main")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**1. 교정기관 정보**")
        cert_number = st.text_input("성적서 번호", value="CAL-2026-001")
        cal_org = st.text_input("교정기관명", value=get_profile_value("org_name"))
        cal_org_kolas = st.text_input("KOLAS 인정번호", value=get_profile_value("kolas_id", "KOLAS-"))
        cal_org_addr = st.text_input("교정기관 소재지", value=get_profile_value("org_address"))

        st.markdown("**2. 의뢰자 정보**")
        client_org = st.text_input("의뢰기관명")
        client_addr = st.text_input("의뢰기관 소재지")

    with col_right:
        st.markdown("**3. 교정 대상**")
        equip_name = st.text_input("교정 대상 기기")
        manufacturer = st.text_input("제조사")
        model_name = st.text_input("모델")
        serial = st.text_input("일련번호")
        cal_date = st.text_input("교정일", value="2026-04-14")
        cal_location = st.text_input("교정 장소", value=get_profile_value("cal_location"))
        temperature = st.text_input("온도 조건", value=get_profile_value("default_temp", "20.0 ± 0.5 °C"))
        humidity = st.text_input("습도 조건", value=get_profile_value("default_humidity", "50 ± 10 %RH"))

    st.divider()
    st.markdown("**4. 불확도 결과 (간단 입력)**")
    st.caption("*불확도 계산 페이지에서 계산한 결과가 있다면, 여기에 직접 2개 성분을 입력하세요.*")

    c1, c2 = st.columns(2)
    with c1:
        src1_name = st.text_input("성분1 이름", value="반복성")
        src1_u = st.number_input("성분1 표준불확도 u", value=0.01, format="%.4e")
    with c2:
        src2_name = st.text_input("성분2 이름", value="표준기 교정")
        src2_u = st.number_input("성분2 표준불확도 u", value=0.02, format="%.4e")

    st.divider()
    st.markdown("**5. 서명**")
    c_s1, c_s2, c_s3 = st.columns(3)
    with c_s1:
        calibrator = st.text_input("교정원", value=get_profile_value("calibrator_name"))
    with c_s2:
        reviewer = st.text_input("검토자", value=get_profile_value("reviewer_name"))
    with c_s3:
        approver = st.text_input("책임자", value=get_profile_value("approver_name"))

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

# ──────────────────────────────────────────
# Tab 2: KOLAS 심사 서류 체크리스트 (NEW)
# ──────────────────────────────────────────
with tab2:
    st.subheader("📋 KOLAS 현장평가 심사 서류 체크리스트")
    st.markdown(
        """
        KOLAS 인정 신청·갱신 시 현장평가에서 제출해야 하는 주요 서류입니다.
        MetroAI가 자동 생성 가능한 서류는 **✅** 표시, 로드맵에 있는 것은 **🔄** 표시입니다.
        """
    )

    st.divider()

    # 체크리스트 데이터
    checklist = [
        {
            "name": "품질매뉴얼 (Quality Manual)",
            "desc": "기관의 품질경영시스템 전체를 서술하는 최상위 문서. ISO/IEC 17025 요구사항을 기관에 맞게 기술.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "측정불확도 예산표",
            "desc": "교정 품목별 불확도 성분 분석, 합성불확도, 확장불확도를 GUM에 따라 산출한 표. KOLAS-G-002 양식.",
            "metroai": "MetroAI 자동 생성",
            "status": "auto",
        },
        {
            "name": "교정성적서",
            "desc": "교정 결과를 의뢰자에게 보고하는 공식 문서. 측정값, 불확도, 소급성, 교정 조건 등 기재.",
            "metroai": "MetroAI 자동 생성",
            "status": "auto",
        },
        {
            "name": "교정 절차서 (SOP)",
            "desc": "교정 품목별 구체적 절차, 사용 장비, 환경 조건, 계산 방법을 기술한 표준운영절차서.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "소급성 체계도",
            "desc": "표준기의 교정 경로를 국가표준(KRISS)까지 추적할 수 있는 체계도.",
            "metroai": "로드맵",
            "status": "roadmap",
        },
        {
            "name": "장비 교정 이력 관리대장",
            "desc": "보유 장비의 교정 주기, 교정일, 교정기관, 교정 결과를 추적하는 대장.",
            "metroai": "로드맵",
            "status": "roadmap",
        },
        {
            "name": "내부심사 보고서",
            "desc": "기관 자체적으로 품질시스템을 점검한 결과 보고서. 연 1회 이상 실시.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "경영검토 보고서",
            "desc": "경영진이 품질시스템의 적절성·유효성을 검토한 결과. 연 1회 이상.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "교육훈련 기록부",
            "desc": "교정원·시험원의 교육 이수 현황, 자격 인정 기록.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "숙련도시험(PT) 참가 기록",
            "desc": "정기 숙련도시험 참가 결과 및 시정조치 기록. z-score, En number 등 판정 포함.",
            "metroai": "MetroAI PT 분석 활용 가능",
            "status": "partial",
        },
        {
            "name": "시정조치 보고서",
            "desc": "PT 불만족, 내부심사 부적합 등 발견 시 원인 분석 및 시정조치 이행 기록.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "측정 데이터 기록 (원본)",
            "desc": "실제 교정 시 기록한 측정값 원본. 수정 시 이력 관리 필수.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "환경 조건 기록부",
            "desc": "교정실 온도, 습도 등 환경 조건의 일일 기록. 허용 범위 이탈 시 조치 기록 포함.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "장비 유지보수 기록",
            "desc": "표준기·측정 장비의 정비, 고장, 수리 이력.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "고객 불만 처리 기록",
            "desc": "의뢰자 불만 접수, 처리 과정, 시정조치 이행 기록.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "문서 관리 목록",
            "desc": "기관 내 모든 관리 문서의 제·개정 현황, 배부 이력.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "기록 관리 절차서",
            "desc": "기록의 식별, 수집, 색인, 보관, 유지, 폐기에 대한 절차.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "부적합 업무 관리 절차서",
            "desc": "시험·교정 부적합 발생 시 처리 절차 및 위험도 평가.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "공정성·기밀성 서약서",
            "desc": "교정원·시험원이 공정성·기밀유지를 서약한 문서.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "조직도",
            "desc": "기관의 조직 구조, 책임과 권한, 기술 관리자·품질 관리자 지정.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "인정범위 신청서",
            "desc": "교정·시험 분야, 품목, CMC(교정측정능력) 등을 명시한 신청 문서.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "위험·기회 관리 대장",
            "desc": "ISO/IEC 17025:2017 신설 요구사항. 기관 운영 리스크 식별·대응 계획.",
            "metroai": "직접 작성",
            "status": "manual",
        },
        {
            "name": "의뢰서·접수서",
            "desc": "교정 의뢰 접수 시 의뢰 내용, 교정 조건 등을 기록하는 양식.",
            "metroai": "직접 작성",
            "status": "manual",
        },
    ]

    # 상태별 아이콘
    status_icons = {
        "auto": "✅ MetroAI 자동 생성",
        "partial": "🔶 MetroAI 부분 활용",
        "roadmap": "🔄 로드맵",
        "manual": "📝 직접 작성",
    }

    # 통계
    auto_count = sum(1 for c in checklist if c["status"] == "auto")
    partial_count = sum(1 for c in checklist if c["status"] == "partial")
    roadmap_count = sum(1 for c in checklist if c["status"] == "roadmap")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전체 서류", f"{len(checklist)}종")
    m2.metric("자동 생성", f"{auto_count}종", help="MetroAI가 현재 자동 생성 가능")
    m3.metric("부분 활용", f"{partial_count}종", help="MetroAI 기능 활용 가능")
    m4.metric("로드맵", f"{roadmap_count}종", help="향후 추가 예정")

    st.divider()

    for i, item in enumerate(checklist):
        icon = status_icons[item["status"]]
        with st.expander(f"**{i+1}. {item['name']}** — {icon}"):
            st.markdown(f"**설명:** {item['desc']}")
            st.markdown(f"**MetroAI 지원:** {item['metroai']}")
            if item["status"] == "auto":
                st.success("이 서류는 MetroAI에서 바로 생성할 수 있습니다.")
            elif item["status"] == "partial":
                st.info("MetroAI의 관련 기능을 활용하여 일부 내용을 준비할 수 있습니다.")
            elif item["status"] == "roadmap":
                st.warning("향후 MetroAI에서 자동 생성 기능이 추가될 예정입니다.")

# ──────────────────────────────────────────
# Tab 3: 예시 다운로드 (NEW)
# ──────────────────────────────────────────
with tab3:
    st.subheader("📥 예시 다운로드")
    st.markdown(
        """
        KOLAS 심사 관련 예시 파일을 다운로드하여 참고하세요.
        "이렇게 생긴 겁니다" — 처음 준비하는 기관을 위한 참고 자료입니다.
        """
    )

    st.divider()

    st.markdown("**현재 제공 중:**")

    # 예시 불확도 예산표 생성 (메모리에서 동적 생성)
    from metroai.templates.length import create_gauge_block_template
    from metroai.export.kolas_excel import export_budget_excel

    st.markdown("**📏 블록게이지 불확도 예산표 예시 (엑셀)**")
    st.caption("블록게이지 50 mm 비교교정의 KOLAS-G-002 양식 불확도 예산표 예시입니다.")

    if st.button("📥 예시 예산표 생성 & 다운로드", key="example_excel"):
        with st.spinner("예시 예산표 생성 중..."):
            model, sources, config = create_gauge_block_template(
                nominal_length_mm=50.0,
                comparator_readings=[0.10, 0.12, 0.08, 0.11, 0.09],
                std_cert_uncertainty_um=0.05,
                std_cert_k=2.0,
            )
            from metroai.core.gum import GUMCalculator

            calc = GUMCalculator(
                model, sources,
                measurand_name=config["measurand_name"],
                measurand_unit=config["measurand_unit"],
            )
            result = calc.calculate()
            excel_buf = export_budget_excel(result, config)

        st.download_button(
            "📥 블록게이지_불확도예산표_예시.xlsx",
            data=excel_buf,
            file_name="블록게이지_불확도예산표_예시.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.markdown("---")

    st.markdown("**📄 교정성적서 예시 (PDF)**")
    st.caption("예시 데이터로 채워진 KOLAS 양식 교정성적서 PDF입니다.")

    if st.button("📥 예시 교정성적서 생성 & 다운로드", key="example_pdf"):
        with st.spinner("예시 교정성적서 생성 중..."):
            ex_model = MeasurementModel("a + b", symbol_names=["a", "b"])
            ex_sources = [
                UncertaintySource(name="반복성", symbol="a", eval_type="A", value=0.0, std_uncertainty=0.01),
                UncertaintySource(name="표준기 교정", symbol="b", eval_type="B", value=0.0, std_uncertainty=0.025),
            ]
            ex_calc = GUMCalculator(ex_model, ex_sources, measurand_name="길이 편차")
            ex_result = ex_calc.calculate()

            ex_cert_info = {
                "cert_number": "CAL-2026-SAMPLE",
                "cal_org": "(예시) 한국계측교정원",
                "cal_org_kolas_id": "KOLAS-XXXX",
                "cal_org_address": "서울특별시 강남구 역삼동 123-45",
                "client_org": "(예시) ABC 제조",
                "client_address": "경기도 수원시 팔달구 56-78",
                "equipment_name": "블록게이지 세트",
                "manufacturer": "Mitutoyo",
                "model": "Grade 0",
                "serial_number": "SN-2024-0001",
                "cal_date": "2026-04-14",
                "cal_location": "표준실 1 (항온항습)",
                "temperature": "20.0 ± 0.5 °C",
                "humidity": "50 ± 10 %RH",
                "calibrator_name": "김교정",
                "reviewer_name": "이검토",
                "approver_name": "박책임",
            }

            pdf_buf = export_calibration_certificate_pdf(ex_result, ex_cert_info)

        st.download_button(
            "📥 교정성적서_예시.pdf",
            data=pdf_buf,
            file_name="교정성적서_예시.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("---")

    st.markdown("**🔜 추가 예정:**")
    st.markdown(
        """
        - 품질매뉴얼 목차 예시 (Phase 2)
        - 소급성 체계도 예시 (Phase 2)
        - PT 결과 보고서 예시 (Phase 2)
        """
    )
