"""KOLAS 심사 대비 셀프체크 페이지 (v0.5.0).

DeepTutor "Quiz Generation" 컨셉 적용:
- KOLAS 심사에서 자주 나오는 질문을 카테고리별로 제시
- 사용자가 자기 기관 상태를 체크하며 준비도를 확인
- 미비 항목에 대해 MetroAI 연결 또는 가이드 제공

원본 아이디어: kolas-audit-predictor 백엔드 (이미 구축됨)
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

st.set_page_config(
    page_title="MetroAI — KOLAS 심사 셀프체크",
    page_icon="✅",
    layout="wide",
)

st.header("✅ KOLAS 심사 대비 셀프체크")
st.caption("현장평가 전에 우리 기관의 준비 상태를 스스로 점검하세요. (DeepTutor Guided Learning 컨셉 적용)")

st.markdown(
    """
    > **사용법:** 각 항목을 읽고, 우리 기관이 준비되었으면 체크하세요.
    > 마지막에 **준비도 점수**와 **미비 항목 대응 가이드**를 보여드립니다.
    """
)

st.divider()

# ──────────────────────────────────────────
# 체크리스트 데이터 (KOLAS 심사관 관점)
# ──────────────────────────────────────────

categories = [
    {
        "name": "📋 품질시스템 (경영 요구사항)",
        "icon": "📋",
        "items": [
            {
                "id": "q01",
                "question": "품질매뉴얼이 ISO/IEC 17025:2017 요구사항을 모두 반영하고 있나요?",
                "tip": "2017년 개정판 기준으로 작성되어야 합니다. 2005년 버전 기반이면 전면 개정 필요.",
                "metroai": None,
                "weight": 3,
            },
            {
                "id": "q02",
                "question": "기술 관리자와 품질 관리자가 공식적으로 지정되어 있나요?",
                "tip": "조직도에 명시 + 직무기술서 + 임명장이 있어야 합니다.",
                "metroai": None,
                "weight": 2,
            },
            {
                "id": "q03",
                "question": "공정성·기밀성 서약서를 전 직원에게 받았나요?",
                "tip": "매년 갱신하는 것이 좋습니다.",
                "metroai": None,
                "weight": 1,
            },
            {
                "id": "q04",
                "question": "내부심사를 지난 12개월 이내에 1회 이상 실시했나요?",
                "tip": "내부심사 보고서 + 부적합 시정조치 기록이 있어야 합니다.",
                "metroai": None,
                "weight": 3,
            },
            {
                "id": "q05",
                "question": "경영검토를 지난 12개월 이내에 실시했나요?",
                "tip": "경영진이 참여한 기록 + 검토 결과 보고서 필요.",
                "metroai": None,
                "weight": 2,
            },
            {
                "id": "q06",
                "question": "위험·기회 관리 대장이 있나요? (2017년 신규 요구사항)",
                "tip": "ISO/IEC 17025:2017에서 새로 추가된 요구사항. 누락하기 쉬운 항목.",
                "metroai": None,
                "weight": 2,
            },
        ],
    },
    {
        "name": "📐 기술 요구사항 — 불확도 / 소급성",
        "icon": "📐",
        "items": [
            {
                "id": "q07",
                "question": "모든 교정 품목에 대해 불확도 예산표가 작성되어 있나요?",
                "tip": "GUM 기반, KOLAS-G-002 양식. 심사관이 가장 집중적으로 검토하는 서류.",
                "metroai": "📐 불확도 계산 페이지에서 자동 생성 가능!",
                "weight": 5,
            },
            {
                "id": "q08",
                "question": "불확도 예산표의 각 성분에 대한 근거가 명확한가요?",
                "tip": "A형은 반복 측정 데이터, B형은 교정성적서/사양서 출처가 있어야 합니다.",
                "metroai": "📐 불확도 계산의 성분별 해설 기능 활용",
                "weight": 4,
            },
            {
                "id": "q09",
                "question": "MCM(몬테카를로)으로 GUM 결과를 검증했나요?",
                "tip": "필수는 아니지만, 심사관에게 매우 좋은 인상을 줍니다.",
                "metroai": "📐 불확도 계산의 MCM 검증 기능 (원클릭)",
                "weight": 2,
            },
            {
                "id": "q10",
                "question": "모든 표준기의 소급성 체계도가 최신 상태인가요?",
                "tip": "KRISS → 기관까지 끊김 없는 교정 경로. 표준기 교정성적서 유효기간 확인.",
                "metroai": None,
                "weight": 5,
            },
            {
                "id": "q11",
                "question": "표준기 교정성적서가 모두 유효기간 내인가요?",
                "tip": "만료된 성적서로 교정하면 결과 전체가 무효. 가장 치명적인 부적합.",
                "metroai": None,
                "weight": 5,
            },
            {
                "id": "q12",
                "question": "교정측정능력(CMC)이 합리적으로 결정되어 있나요?",
                "tip": "불확도 예산표의 최소 불확도와 CMC가 일치해야 합니다.",
                "metroai": "🔄 불확도 역설계로 CMC 달성 가능성 검증",
                "weight": 4,
            },
        ],
    },
    {
        "name": "📊 숙련도시험 (PT)",
        "icon": "📊",
        "items": [
            {
                "id": "q13",
                "question": "인정 분야에 대해 숙련도시험에 정기적으로 참가하고 있나요?",
                "tip": "KASTO 또는 국제 PT 프로그램에 참가한 기록이 필요합니다.",
                "metroai": None,
                "weight": 4,
            },
            {
                "id": "q14",
                "question": "최근 PT 결과에서 불만족(|z|>3 또는 |En|>1)이 없나요?",
                "tip": "불만족 결과가 있다면 시정조치 보고서가 반드시 있어야 합니다.",
                "metroai": "📊 PT 분석 페이지에서 z-score/En 자동 판정",
                "weight": 4,
            },
            {
                "id": "q15",
                "question": "PT 불만족 시 시정조치를 문서화했나요?",
                "tip": "원인 분석 → 조치 이행 → 효과 확인까지 기록해야 합니다.",
                "metroai": None,
                "weight": 3,
            },
        ],
    },
    {
        "name": "📄 문서 / 기록 관리",
        "icon": "📄",
        "items": [
            {
                "id": "q16",
                "question": "교정 절차서(SOP)가 모든 품목에 대해 작성되어 있나요?",
                "tip": "절차서 없이 교정하면 부적합. 절차서 버전 관리도 중요.",
                "metroai": None,
                "weight": 4,
            },
            {
                "id": "q17",
                "question": "교정성적서 양식이 KOLAS-G-004 요구사항을 충족하나요?",
                "tip": "필수 기재사항 누락 여부를 교정성적서 페이지에서 확인하세요.",
                "metroai": "📄 교정성적서 PDF 자동 생성 (KOLAS-G-004 양식)",
                "weight": 3,
            },
            {
                "id": "q18",
                "question": "측정 데이터 원본이 수정 불가능한 형태로 보관되고 있나요?",
                "tip": "엑셀 파일은 수정 가능 → 볼펜 기록 원본 또는 잠금된 전자 기록 필요.",
                "metroai": None,
                "weight": 3,
            },
            {
                "id": "q19",
                "question": "장비 교정 이력 관리대장이 최신 상태인가요?",
                "tip": "보유 장비 목록 + 교정 주기 + 최근 교정일 + 다음 교정 예정일.",
                "metroai": None,
                "weight": 3,
            },
            {
                "id": "q20",
                "question": "교육훈련 기록이 모든 교정원에 대해 있나요?",
                "tip": "교육 이수 현황, 자격 인정 기록, 역량 평가 기록.",
                "metroai": None,
                "weight": 2,
            },
        ],
    },
    {
        "name": "🏭 환경 / 장비",
        "icon": "🏭",
        "items": [
            {
                "id": "q21",
                "question": "교정실의 온도·습도 조건이 기록되고 허용 범위 내인가요?",
                "tip": "환경 조건 기록부가 매일 작성되어야 합니다. 이탈 시 조치 기록 포함.",
                "metroai": None,
                "weight": 3,
            },
            {
                "id": "q22",
                "question": "장비 유지보수 기록이 관리되고 있나요?",
                "tip": "정비, 수리, 고장 이력. 수리 후 재교정 기록 포함.",
                "metroai": None,
                "weight": 2,
            },
            {
                "id": "q23",
                "question": "교정 환경(진동, 먼지, 전자기 간섭 등)이 적절히 관리되고 있나요?",
                "tip": "분야에 따라 클린룸 등급, 전자파 차폐 등이 요구될 수 있음.",
                "metroai": None,
                "weight": 2,
            },
        ],
    },
]

# ──────────────────────────────────────────
# 렌더링
# ──────────────────────────────────────────

# 세션 초기화
if "selfcheck_answers" not in st.session_state:
    st.session_state.selfcheck_answers = {}

total_items = sum(len(c["items"]) for c in categories)
total_weight = sum(item["weight"] for c in categories for item in c["items"])

for cat in categories:
    st.subheader(cat["name"])

    for item in cat["items"]:
        col_check, col_content = st.columns([0.06, 0.94])

        with col_check:
            checked = st.checkbox(
                "OK",
                value=st.session_state.selfcheck_answers.get(item["id"], False),
                key=f"check_{item['id']}",
                label_visibility="collapsed",
            )
            st.session_state.selfcheck_answers[item["id"]] = checked

        with col_content:
            # 질문
            if checked:
                st.markdown(f"~~{item['question']}~~ ✅")
            else:
                st.markdown(f"**{item['question']}**")

            # 도움말
            with st.expander("💡 팁 + 가이드", expanded=False):
                st.markdown(f"**심사관 관점:** {item['tip']}")
                if item["metroai"]:
                    st.success(f"🤖 **MetroAI 도움:** {item['metroai']}")
                else:
                    st.info("📝 이 항목은 기관에서 직접 준비해야 합니다.")

    st.divider()

# ──────────────────────────────────────────
# 결과 계산
# ──────────────────────────────────────────
st.subheader("📊 셀프체크 결과")

checked_weight = sum(
    item["weight"]
    for cat in categories
    for item in cat["items"]
    if st.session_state.selfcheck_answers.get(item["id"], False)
)
checked_count = sum(1 for v in st.session_state.selfcheck_answers.values() if v)
score = (checked_weight / total_weight * 100) if total_weight > 0 else 0

# 점수 표시
col_score, col_detail = st.columns([1, 2])

with col_score:
    st.metric("준비도 점수", f"{score:.0f}점 / 100점")
    st.progress(score / 100)

    if score >= 90:
        st.success("🎉 **우수** — 현장평가 준비가 잘 되어 있습니다!")
    elif score >= 70:
        st.warning("⚠️ **양호** — 몇 가지 미비 항목을 보완하면 됩니다.")
    elif score >= 50:
        st.warning("🟡 **보통** — 상당한 준비가 더 필요합니다.")
    else:
        st.error("🔴 **미흡** — 심사 전에 체계적인 준비가 필요합니다.")

with col_detail:
    st.markdown(f"**체크 현황:** {checked_count} / {total_items} 항목 완료")

    # 미비 항목 중 가중치 높은 순으로 표시
    unchecked = [
        (item, cat["name"])
        for cat in categories
        for item in cat["items"]
        if not st.session_state.selfcheck_answers.get(item["id"], False)
    ]
    unchecked.sort(key=lambda x: x[0]["weight"], reverse=True)

    if unchecked:
        st.markdown("**🔴 우선 보완 항목 (가중치 순):**")
        for item, cat_name in unchecked[:5]:
            priority = "🔴" if item["weight"] >= 4 else "🟡" if item["weight"] >= 3 else "⚪"
            metroai_tag = " → MetroAI 활용 가능" if item["metroai"] else ""
            st.markdown(f"{priority} **[가중치 {item['weight']}]** {item['question']}{metroai_tag}")

        if len(unchecked) > 5:
            st.caption(f"... 외 {len(unchecked) - 5}개 항목")
    else:
        st.balloons()
        st.success("🎊 모든 항목이 준비되었습니다! 현장평가에 자신감을 가지세요.")

# ──────────────────────────────────────────
# CTA
# ──────────────────────────────────────────
st.divider()
st.markdown("### 🚀 미비 항목 바로 해결하기")

cta1, cta2, cta3, cta4 = st.columns(4)
with cta1:
    if st.button("📐 불확도 계산", use_container_width=True):
        st.switch_page("pages/1_📐_불확도_계산.py")
with cta2:
    if st.button("📊 PT 분석", use_container_width=True):
        st.switch_page("pages/2_📊_PT_분석.py")
with cta3:
    if st.button("📄 교정성적서", use_container_width=True):
        st.switch_page("pages/3_📄_교정성적서.py")
with cta4:
    if st.button("🔄 역설계", use_container_width=True):
        st.switch_page("pages/4_🔄_불확도_역설계.py")
