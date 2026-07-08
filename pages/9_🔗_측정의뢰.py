"""MeasureLink Phase 1 — 측정 의뢰 폼 (v0.5.0).

MeasureLink 컨셉: 발명가/스타트업이 측정 니즈를 등록하면
용범이 수동으로 적합한 KOLAS 기관을 매칭.
Phase 1은 코드 없이 폼 + 이메일 알림만.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="MetroAI — 측정 의뢰 (MeasureLink)",
    page_icon="🔗",
    layout="wide",
)

st.header("🔗 측정 의뢰 — MeasureLink")
st.caption("KOLAS 인정기관에 측정·교정·시험을 의뢰하세요. MetroAI가 적합한 기관을 매칭해드립니다.")

st.markdown(
    """
    > **MeasureLink는 MetroAI의 새로운 서비스입니다.**
    >
    > 아이디어 검증, 시제품 측정, 품질 인증 등 — 어떤 측정이 필요한지 알려주시면
    > KOLAS 인정기관 중 적합한 곳을 찾아 연결해드립니다.
    >
    > 현재 **베타 서비스**로, 전문가가 직접 매칭합니다.
    """
)

st.divider()

# ──────────────────────────────────────────
# 의뢰 폼
# ──────────────────────────────────────────
with st.form("measure_request", clear_on_submit=True):
    st.subheader("📝 측정 의뢰서")

    st.markdown("**1. 의뢰자 정보**")
    c1, c2 = st.columns(2)
    with c1:
        req_name = st.text_input("이름/기관명 *", placeholder="홍길동 / ABC 스타트업")
        req_email = st.text_input("이메일 *", placeholder="example@email.com")
    with c2:
        req_phone = st.text_input("연락처", placeholder="010-1234-5678")
        req_type = st.selectbox("의뢰자 유형", [
            "1인 발명가 / 개인",
            "스타트업 / 중소기업",
            "대기업 / 연구소",
            "대학 / 교육기관",
            "기타",
        ])

    st.divider()

    st.markdown("**2. 측정 내용**")
    req_category = st.selectbox("측정 분야", [
        "길이 / 치수 (블록게이지, 마이크로미터, 3차원 측정 등)",
        "질량 (분동, 저울, 무게 등)",
        "온도 (온도계, 써모커플, 항온조 등)",
        "압력 (압력계, 진공 등)",
        "전기 (전압, 전류, 저항, 캐패시턴스 등)",
        "화학 / 가스 (성분 분석, 농도, pH 등)",
        "금속 / 재료 (SEM, TEM, AFM, 인장시험 등)",
        "환경 (수질, 대기, 소음, 진동 등)",
        "기타",
    ])

    req_detail = st.text_area(
        "측정하고 싶은 것을 자유롭게 설명해주세요 *",
        placeholder="예:\n- 개발 중인 신소재의 나노입자 크기 분포를 측정하고 싶습니다\n- SEM-EDS로 조성 분석이 필요합니다\n- 블록게이지 세트를 교정받고 싶습니다\n- 아이디어 단계인데 어떤 측정이 필요한지 모르겠습니다 (상담 요청)",
        height=150,
    )

    st.divider()

    st.markdown("**3. 추가 정보 (선택)**")
    c3, c4 = st.columns(2)
    with c3:
        req_kolas = st.radio("KOLAS 공인 성적서 필요?", ["필요", "불필요", "잘 모름"], horizontal=True)
        req_urgency = st.selectbox("긴급도", ["보통 (1~2주)", "급함 (1주 이내)", "매우 급함 (3일 이내)", "여유 있음 (1개월+)"])
    with c4:
        req_budget = st.selectbox("예산 범위", ["10만원 이하", "10~50만원", "50~100만원", "100만원 이상", "미정 (견적 받고 결정)"])
        req_samples = st.text_input("시료 정보 (개수, 크기, 재질 등)", placeholder="예: 실리콘 웨이퍼 5장, 2인치")

    req_note = st.text_area("기타 요청사항", placeholder="예: 영문 성적서 필요, 특정 기관 선호 등", height=80)

    submitted = st.form_submit_button("📨 측정 의뢰 제출", type="primary", use_container_width=True)

    if submitted:
        if not req_name or not req_email or not req_detail:
            st.error("이름, 이메일, 측정 내용은 필수 항목입니다.")
        else:
            # Phase 1: 세션 저장 + 알림 (실제로는 이메일/슬랙 연동 필요)
            st.session_state.setdefault("measure_requests", []).append({
                "name": req_name,
                "email": req_email,
                "phone": req_phone,
                "type": req_type,
                "category": req_category,
                "detail": req_detail,
                "kolas": req_kolas,
                "urgency": req_urgency,
                "budget": req_budget,
                "samples": req_samples,
                "note": req_note,
            })
            st.success(
                f"✅ **측정 의뢰가 접수되었습니다!**\n\n"
                f"의뢰 번호: ML-{len(st.session_state.get('measure_requests', [])): 04d}\n\n"
                f"24시간 이내에 **{req_email}** 으로 적합한 기관 매칭 결과를 보내드리겠습니다.\n\n"
                f"급한 문의: **kyb8801@gmail.com**"
            )
            st.balloons()

st.divider()

# ──────────────────────────────────────────
# 설명
# ──────────────────────────────────────────
st.markdown("### 🤔 MeasureLink는 어떻게 동작하나요?")

step_cols = st.columns(4)
with step_cols[0]:
    st.markdown("**1️⃣ 의뢰 등록**")
    st.caption("위 폼으로 측정 니즈를 알려주세요.")
with step_cols[1]:
    st.markdown("**2️⃣ 전문가 매칭**")
    st.caption("MetroAI 전문가가 KOLAS 인정기관 중 최적 기관을 선별합니다.")
with step_cols[2]:
    st.markdown("**3️⃣ 견적 비교**")
    st.caption("1~3개 기관의 견적을 비교하여 안내합니다.")
with step_cols[3]:
    st.markdown("**4️⃣ 결과 해석**")
    st.caption("측정 결과를 MetroAI로 불확도 분석하여 전달합니다.")

st.info(
    "💡 **왜 MeasureLink를 이용하나요?**\n\n"
    "- KOLAS 인정기관 1,100개 중 어디가 우리 측정에 적합한지 찾기 어려움\n"
    "- 기관별 인정 범위, 장비 상태, 가격이 공개되어 있지 않음\n"
    "- MetroAI는 기관의 교정 상태·인정 범위를 데이터로 관리 → 최적 매칭"
)
