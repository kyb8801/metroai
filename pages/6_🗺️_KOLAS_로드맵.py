"""KOLAS 인정 로드맵 페이지 (v0.5.0).

"KOLAS 인정을 받으려면 어떤 순서로 준비해야 하나요?"
1~7개월 타임라인 + 각 단계에서 MetroAI가 도와줄 수 있는 것 표시.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

st.set_page_config(
    page_title="MetroAI — KOLAS 인정 로드맵",
    page_icon="🗺️",
    layout="wide",
)

st.header("🗺️ KOLAS 인정 준비 로드맵")
st.caption("KOLAS 인정을 처음 받아보려는 기관을 위한 맞춤형 안내서 (Guided Learning 적용)")

# ──────────────────────────────────────────
# Guided Learning: 내 상황 선택 (DeepTutor 컨셉)
# ──────────────────────────────────────────
st.markdown("### 🎯 먼저 우리 기관 상황을 알려주세요")
st.caption("상황에 따라 강조되는 단계가 달라집니다.")

gl_col1, gl_col2 = st.columns(2)
with gl_col1:
    situation = st.radio(
        "현재 상황",
        [
            "🆕 처음부터 시작 (KOLAS 인정 신규 신청)",
            "🔄 갱신 준비 (4년 주기 재평가)",
            "📌 분야 추가 (기존 인정 + 새 품목 추가)",
            "⚠️ 부적합 시정 (이전 심사에서 지적사항 있음)",
        ],
        key="gl_situation",
    )
with gl_col2:
    field = st.selectbox(
        "교정/시험 분야",
        ["길이 (블록게이지 등)", "질량 (분동 등)", "온도 (온도계 등)", "압력 (압력계 등)",
         "전기 (전압/전류/저항)", "화학 (가스/수질 분석)", "금속·재료 (SEM/TEM 시험)",
         "기타 / 아직 모름"],
        key="gl_field",
    )

# 상황별 가이드 메시지
if "처음" in situation:
    st.info("🆕 **신규 신청:** 아래 7단계를 순서대로 따라가세요. 보통 6~12개월 소요됩니다.")
    highlight_steps = [1, 2, 3, 4, 5, 6, 7]
elif "갱신" in situation:
    st.info("🔄 **갱신 준비:** 품질매뉴얼·절차서 최신화, 내부심사/경영검토 실시, PT 참가 기록 확인에 집중하세요. 3~4단계가 핵심.")
    highlight_steps = [3, 4, 5]
elif "분야 추가" in situation:
    st.info("📌 **분야 추가:** 새 품목의 불확도 예산표·교정절차서·소급성 체계가 핵심. 2~4단계에 집중.")
    highlight_steps = [2, 3, 4]
else:
    st.info("⚠️ **부적합 시정:** 지적받은 항목의 원인 분석 → 시정조치 → 효과 확인 기록이 최우선. 셀프체크 페이지도 활용하세요.")
    highlight_steps = [5]

if "SEM" in field or "TEM" in field or "금속" in field:
    st.warning("🔬 **금속·재료(SEM/TEM) 분야:** 이 분야는 \"시험기관\" 인정에 해당합니다 (교정기관이 아님). 불확도 모델이 교정과 다르며, 나노입자 크기·피막 두께·조성 분석 등의 시험방법 표준이 필요합니다.")
elif "화학" in field or "가스" in field:
    st.warning("🧪 **화학/가스 분야:** 화학 분석 불확도는 Eurachem 가이드 기반으로, GUM과 접근법이 약간 다릅니다. MetroAI 시험기관 확장(Phase 2)에서 지원 예정.")

st.divider()

st.markdown(
    """
    > **"KOLAS 인정을 받으려면 어떤 순서로, 무엇을 준비해야 하나요?"**
    >
    > 일반적으로 6~12개월이 소요됩니다. 아래는 대표적인 준비 흐름을 7단계로 나눈 것입니다.
    > 기관 규모·분야에 따라 기간은 조정될 수 있습니다.
    """
)

st.divider()

# ──────────────────────────────────────────
# 타임라인
# ──────────────────────────────────────────
roadmap = [
    {
        "month": "1개월차",
        "icon": "📋",
        "title": "품질매뉴얼 작성 + 조직 구성",
        "tasks": [
            "품질매뉴얼 초안 작성 (ISO/IEC 17025 요구사항에 맞게)",
            "기술 관리자 · 품질 관리자 지정",
            "조직도 · 직무 기술서 작성",
            "공정성 · 기밀성 서약서 수집",
        ],
        "metroai_help": None,
        "tip": "품질매뉴얼은 기관의 '헌법'입니다. 표준 목차를 참고하되, 우리 기관 실정에 맞게 작성하세요.",
    },
    {
        "month": "2개월차",
        "icon": "🔗",
        "title": "소급성 체계 설정 + 교정 절차서",
        "tasks": [
            "보유 표준기의 소급성 체계도 작성 (KRISS → 기관)",
            "교정 품목별 절차서(SOP) 작성",
            "장비 교정 이력 관리대장 초기화",
            "환경 조건 모니터링 체계 구축 (온·습도 기록부)",
        ],
        "metroai_help": "🔄 소급성 체계도 자동 생성 (로드맵)",
        "tip": "소급성 체계도는 심사관이 가장 먼저 보는 서류 중 하나입니다.",
    },
    {
        "month": "3개월차",
        "icon": "📐",
        "title": "불확도 예산표 작성 ⭐",
        "tasks": [
            "교정 품목별 불확도 예산표 작성 (GUM 기반)",
            "MCM(몬테카를로) 검증 실시",
            "KOLAS-G-002 양식으로 정리",
            "교정측정능력(CMC) 결정",
        ],
        "metroai_help": "✅ **MetroAI 핵심 기능**: 불확도 자동 계산 + MCM 검증 + KOLAS-G-002 엑셀 출력",
        "tip": "이 단계가 가장 기술적으로 어렵습니다. MetroAI를 사용하면 1~2시간 걸리는 작업을 5분에 끝낼 수 있습니다.",
    },
    {
        "month": "4개월차",
        "icon": "📄",
        "title": "교정성적서 체계 확립 + 교육",
        "tasks": [
            "교정성적서 양식 확정 (KOLAS-G-004 참고)",
            "교정원 · 시험원 교육 계획 수립 및 시행",
            "교육훈련 기록부 관리 시작",
            "실제 교정 수행 + 성적서 발행 연습",
        ],
        "metroai_help": "✅ **MetroAI**: 교정성적서 PDF 자동 생성",
        "tip": "심사 전에 최소 수 건의 교정 실적이 있어야 합니다.",
    },
    {
        "month": "5개월차",
        "icon": "🔍",
        "title": "내부심사 + 경영검토",
        "tasks": [
            "내부심사 계획 수립 및 실시",
            "부적합 사항 시정조치",
            "경영검토 실시 (경영진 참여)",
            "시정조치 보고서 · 경영검토 보고서 작성",
        ],
        "metroai_help": None,
        "tip": "내부심사는 연 1회 이상 실시. KOLAS 신청 전 반드시 1회 이상 완료해야 합니다.",
    },
    {
        "month": "6개월차",
        "icon": "📨",
        "title": "KOLAS 인정 신청 + 서류심사",
        "tasks": [
            "KOLAS 인정 신청서 작성 · 제출",
            "인정범위(교정 분야, 품목, CMC) 명시",
            "전체 서류 최종 점검 (23종 체크리스트)",
            "서류심사 대응 (보완 요청 시 수정·재제출)",
        ],
        "metroai_help": "✅ **MetroAI**: 심사 서류 23종 체크리스트 + 예시 다운로드",
        "tip": "서류심사에서 보완 요청이 오면 당황하지 마세요. 거의 모든 기관이 1~2회 보완을 거칩니다.",
    },
    {
        "month": "7개월차+",
        "icon": "🏆",
        "title": "현장평가 + 인정서 발급",
        "tasks": [
            "KOLAS 심사관 현장 방문",
            "실제 교정 시연 · 장비 점검 · 서류 확인",
            "부적합 사항 시정 (있는 경우)",
            "숙련도시험(PT) 참가 기록 확인",
            "인정서 발급 (축하합니다! 🎉)",
        ],
        "metroai_help": "✅ **MetroAI**: PT 분석(z-score, En) + 불확도 역설계(CMC 검증)",
        "tip": "현장평가에서 가장 많이 지적되는 것: 불확도 예산표 오류, 소급성 미흡, 교육 기록 부재.",
    },
]

for i, phase in enumerate(roadmap):
    with st.container():
        # 타임라인 헤더
        col_icon, col_content = st.columns([0.08, 0.92])
        with col_icon:
            st.markdown(f"<div style='font-size:2.5rem;text-align:center;'>{phase['icon']}</div>", unsafe_allow_html=True)
        with col_content:
            st.markdown(f"### {phase['month']}: {phase['title']}")

        # 할일 목록
        for task in phase["tasks"]:
            st.markdown(f"- {task}")

        # MetroAI 도움
        if phase["metroai_help"]:
            st.success(phase["metroai_help"])

        # 팁
        st.info(f"💡 **Tip:** {phase['tip']}")

        if i < len(roadmap) - 1:
            st.markdown("<div style='text-align:center;color:#667eea;font-size:1.5rem;padding:0.5rem 0;'>⬇️</div>", unsafe_allow_html=True)

st.divider()

# ──────────────────────────────────────────
# 주의사항
# ──────────────────────────────────────────
st.markdown("### ⚠️ 참고사항")
st.markdown(
    """
    - 위 일정은 **소규모 교정기관 (1~3명)** 기준 추정치입니다. 대규모 기관은 더 빨라질 수 있고, 다품목 기관은 더 오래 걸릴 수 있습니다.
    - KOLAS 인정 후에도 **매년 정기 감시평가**, **4년마다 갱신평가**가 있습니다.
    - 숙련도시험(PT)은 **인정 후에도 정기적으로 참가**해야 합니다.
    - KOLAS 관련 지침(G-001, G-002 등)은 **수시로 개정**되므로 최신본을 확인하세요.
    """
)

# ──────────────────────────────────────────
# CTA
# ──────────────────────────────────────────
st.divider()
st.markdown("### 🚀 지금 바로 시작하세요")

cta1, cta2, cta3 = st.columns(3)
with cta1:
    if st.button("📐 불확도 계산 시작", type="primary", use_container_width=True):
        st.switch_page("pages/1_📐_불확도_계산.py")
with cta2:
    if st.button("📋 심사 서류 체크리스트", use_container_width=True):
        st.switch_page("pages/3_📄_교정성적서.py")
with cta3:
    if st.button("📊 PT 분석", use_container_width=True):
        st.switch_page("pages/2_📊_PT_분석.py")
