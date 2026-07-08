"""KOLAS 인정 신청서 자동 작성기 — v0.7.0 P0-3.

ISO/IEC 17025 기반 generic 인정 신청 양식 PDF 자동 생성.
실제 KAB-F-21 과 다를 수 있으니 참고용.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.content.application_form import (
    OrganizationProfile,
    generate_application_pdf,
    get_default_profile_for_domain,
)
from metroai.content.kolas_guides import list_domains

st.set_page_config(
    page_title="KOLAS 인정 신청서 작성 — MetroAI",
    page_icon="📝",
    layout="wide",
)

st.markdown(
    """
    <style>
    .v2-brand-h1 {
        font-size: 1.75rem; font-weight: 600; color: #1E40AF;
        margin-bottom: 0.2rem; letter-spacing: -0.01em;
    }
    .v2-subtle {
        color: #475569; font-size: 0.95rem; margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='v2-brand-h1'>📝 KOLAS 인정 신청서 자동 작성</div>"
    "<div class='v2-subtle'>ISO/IEC 17025 기반 generic 양식. 조직 프로필 1회 입력 → PDF 즉시 출력.</div>",
    unsafe_allow_html=True,
)

st.warning(
    "⚠️ 본 PDF 는 ISO/IEC 17025 기반 **generic 양식** 입니다. 실제 KAB-F-21 또는 최신 KAB 양식과 "
    "다를 수 있습니다. 본 양식 출력 후 KAB (knab.go.kr) 의 최신 양식과 비교하여 보강하세요."
)

# ──────────────────────────────────────────────
# 분야 선택 (session_state 활용)
# ──────────────────────────────────────────────
default_domain = st.session_state.get("current_domain", "general")
domain_options = {g.key: f"{g.icon} {g.label_ko}" for g in list_domains()}
domain_keys = list(domain_options.keys())
selected_domain = st.selectbox(
    "측정 분야",
    options=domain_keys,
    format_func=lambda k: domain_options[k],
    index=domain_keys.index(default_domain) if default_domain in domain_keys else 4,
    help="분야를 변경하면 분야별 기본값으로 폼이 다시 채워집니다.",
)

# 분야 변경 감지
if "_last_domain" not in st.session_state:
    st.session_state["_last_domain"] = selected_domain
if st.session_state["_last_domain"] != selected_domain:
    # 분야 변경되었을 때 default profile 다시 로드
    st.session_state["_profile"] = get_default_profile_for_domain(selected_domain)
    st.session_state["_last_domain"] = selected_domain

# 초기 프로필
if "_profile" not in st.session_state:
    st.session_state["_profile"] = get_default_profile_for_domain(selected_domain)

profile: OrganizationProfile = st.session_state["_profile"]

# ──────────────────────────────────────────────
# 입력 폼
# ──────────────────────────────────────────────
with st.form("application_form"):
    st.subheader("1. 신청 기관 정보")
    c1, c2 = st.columns(2)
    with c1:
        profile.org_name_ko = st.text_input("기관명 (국문)", profile.org_name_ko)
        profile.representative_name = st.text_input("대표자", profile.representative_name)
        profile.business_registration_no = st.text_input("사업자등록번호", profile.business_registration_no)
        profile.phone = st.text_input("연락처", profile.phone)
    with c2:
        profile.org_name_en = st.text_input("기관명 (영문)", profile.org_name_en)
        profile.email = st.text_input("이메일", profile.email)
        profile.website = st.text_input("웹사이트", profile.website)
    profile.address = st.text_area("주소", profile.address, height=68)

    st.subheader("2. 인정 신청 범위")
    c3, c4 = st.columns(2)
    with c3:
        profile.accreditation_type = st.selectbox(
            "인정 분야 유형",
            options=["시험", "교정", "RMP", "검사"],
            index=["시험", "교정", "RMP", "검사"].index(profile.accreditation_type)
            if profile.accreditation_type in ["시험", "교정", "RMP", "검사"] else 0,
        )
    with c4:
        st.text_input("측정 분야 (영문)", selected_domain.upper(), disabled=True)
    profile.accreditation_scope_summary = st.text_area(
        "신청 범위 요약 (1-2 문장)", profile.accreditation_scope_summary, height=70,
    )
    profile.iso_standards_applied = st.multiselect(
        "적용 ISO 표준",
        options=[
            "ISO/IEC 17025:2017", "ISO/IEC 17034:2016", "ISO 13528:2022", "ISO 17043:2010",
            "ISO/IEC Guide 98-3:2008 (GUM)", "ISO 22489:2016", "ISO 25178-2:2012",
            "ISO 16700:2016", "ISO 29301:2017", "ISO 14709-1:2002", "ISO 11952:2019",
            "ISO 18516:2019", "SEMI MF-1789-1112", "ISO 17078-2:2014", "ASTM E1508:2012a",
            "VDI/VDE 2656-1:2008", "ISO 5725 series",
        ],
        default=profile.iso_standards_applied,
    )
    profile.measurement_range = st.text_input("측정 범위", profile.measurement_range)
    profile.typical_uncertainty = st.text_input("측정 불확도 (CMC, k=2)", profile.typical_uncertainty)

    st.subheader("3. 인력 정보 (ISO/IEC 17025 6.2)")
    c5, c6 = st.columns(2)
    with c5:
        profile.quality_manager_name = st.text_input("품질책임자 이름", profile.quality_manager_name)
        profile.quality_manager_cert = st.text_input("품질책임자 자격", profile.quality_manager_cert)
    with c6:
        profile.technical_manager_name = st.text_input("기술책임자 이름", profile.technical_manager_name)
        profile.technical_manager_cert = st.text_input("기술책임자 자격", profile.technical_manager_cert)
    c7, c8 = st.columns(2)
    with c7:
        profile.n_calibration_engineers = st.number_input(
            "교정 엔지니어 수", min_value=0, max_value=100, value=profile.n_calibration_engineers,
        )
    with c8:
        profile.n_test_engineers = st.number_input(
            "시험 엔지니어 수", min_value=0, max_value=100, value=profile.n_test_engineers,
        )

    st.subheader("4. 환경 조건")
    profile.environmental_control = st.text_input(
        "환경 chamber 제어 사양",
        profile.environmental_control,
        help="예: 20 ± 1°C, 50 ± 10% RH (chamber 1대, 매 시간 기록)",
    )

    st.subheader("5. 품질 시스템 (ISO/IEC 17025 8장)")
    c9, c10 = st.columns(2)
    with c9:
        qsdate_str = profile.quality_system_implementation_date or date.today().isoformat()
        profile.quality_system_implementation_date = st.text_input(
            "품질 시스템 도입 일자 (YYYY-MM-DD)", qsdate_str,
        )
    with c10:
        profile.internal_audit_completed = st.checkbox(
            "내부 audit 완료", profile.internal_audit_completed,
        )
    profile.pt_participation_history = st.text_area(
        "PT 참가 이력 (ISO 17043)",
        profile.pt_participation_history,
        height=68,
        placeholder="예: 2024년 1회 (KOLAS PT, z'-score 1.2), 2025년 1회 예정",
    )

    submitted = st.form_submit_button("📝 신청서 PDF 생성", type="primary", use_container_width=True)

# ──────────────────────────────────────────────
# PDF 생성 & 다운로드
# ──────────────────────────────────────────────
if submitted:
    st.session_state["_profile"] = profile

    with st.spinner("PDF 생성 중..."):
        try:
            pdf_bytes = generate_application_pdf(profile)
            st.success(f"PDF 생성 완료. {len(pdf_bytes)/1024:.1f} KB")

            st.download_button(
                label="📥 신청서 PDF 다운로드",
                data=pdf_bytes,
                file_name=f"KOLAS_application_{profile.accreditation_domain}_{date.today().isoformat()}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF 생성 실패: {e}")
            st.exception(e)

# ──────────────────────────────────────────────
# 보조 정보
# ──────────────────────────────────────────────
with st.expander("💡 본 양식 vs 실제 KAB-F-21 차이"):
    st.markdown(
        """
        **본 양식의 한계 (정직):**

        - KAB-F-21 정확한 사본을 보유하지 않음. ISO/IEC 17025 7장·8장 기반 generic 양식.
        - 실제 KAB-F-21 은 추가 부속서 (별표 1: 인정 범위 상세, 별표 2: 인력 자격 검증서 등) 보유.
        - 본 양식 출력 후 **knab.go.kr 의 최신 KAB-F-21 양식** 다운로드 → 본 양식의 내용을 그대로 옮겨 적기 + 누락 항목 보강 권장.

        **본 양식의 가치:**

        - 신청서 작성에 필요한 ISO/IEC 17025 항목 전수 점검 가능 (6.2, 6.3, 6.4, 6.5, 7.6, 8장).
        - 분야별 (SEM/TEM/AFM/OCD/general) 기본값으로 빠른 first draft.
        - PDF 자동 생성으로 손 작성 오류 제거.
        """,
    )

with st.expander("📚 분야별 적용 표준 자세히 보기"):
    from metroai.content.kolas_guides import get_domain_guide

    g = get_domain_guide(selected_domain)
    if g:
        st.markdown(f"### {g.icon} {g.label_ko} 표준 ({len(g.iso_standards)} 종)")
        for s in g.iso_standards:
            st.markdown(f"- **{s['code']}** — {s['title']}")
            st.caption(s["scope"])

st.markdown("---")
st.caption(
    "v0.7.0 P0-3 자동 작성. 본 양식은 generic 참고용 — 실제 신청 시 KAB 최신 양식과 비교 필수."
)
