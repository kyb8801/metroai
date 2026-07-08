"""KOLAS / 측정불확도 용어사전 페이지 (v0.5.0).

KOLAS와 불확도 관련 전문 용어를 한 줄 설명 + 상세 설명으로 제공.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="MetroAI — 용어사전",
    page_icon="📖",
    layout="wide",
)

st.header("📖 KOLAS / 측정불확도 용어사전")
st.caption("KOLAS 심사와 불확도 계산에서 자주 등장하는 용어를 쉽게 설명합니다.")

# ──────────────────────────────────────────
# 검색
# ──────────────────────────────────────────
search = st.text_input("🔍 용어 검색", placeholder="GUM, CMC, MCM, A형, B형 ...", key="glossary_search")

st.divider()

# ──────────────────────────────────────────
# 용어 데이터
# ──────────────────────────────────────────
glossary = [
    {
        "term": "KOLAS",
        "short": "Korea Laboratory Accreditation Scheme — 한국인정기구(KAB)가 운영하는 시험·교정 기관 인정 제도",
        "detail": "ISO/IEC 17025 기반으로 시험·교정기관의 기술적 적격성을 평가하고 인정하는 국가 제도. 인정받은 기관의 교정성적서는 법적 효력을 가집니다.",
        "tags": ["기관인정", "ISO 17025"],
    },
    {
        "term": "ISO/IEC 17025",
        "short": "시험·교정기관의 적격성에 대한 일반 요구사항 국제 표준",
        "detail": "시험 및 교정기관이 기술적으로 유능하고 유효한 결과를 생성할 수 있음을 증명하기 위한 요구사항을 규정한 국제 표준. 2017년 개정판(17025:2017)이 현행.",
        "tags": ["국제표준", "기관인정"],
    },
    {
        "term": "GUM",
        "short": "Guide to the Expression of Uncertainty in Measurement — 측정불확도 표현 가이드 (ISO/IEC Guide 98-3)",
        "detail": "측정 결과의 불확도를 평가하고 표현하는 국제 표준 방법론. A형(통계적)과 B형(비통계적) 평가, 합성불확도 계산, 확장불확도 보고 방법을 규정. MetroAI는 GUM을 완전히 구현합니다.",
        "tags": ["불확도", "국제표준"],
    },
    {
        "term": "MCM (몬테카를로법)",
        "short": "Monte Carlo Method — GUM Supplement 1에 기반한 불확도 검증 방법",
        "detail": "입력량의 확률분포에서 대량의 무작위 샘플을 추출하여 출력량의 분포를 직접 구하는 방법. GUM의 선형 근사가 적절한지 검증하는 데 사용. MetroAI는 자동으로 MCM 검증을 수행합니다.",
        "tags": ["불확도", "검증"],
    },
    {
        "term": "A형 평가",
        "short": "반복 측정의 통계적 분석으로 표준불확도를 구하는 방법",
        "detail": "같은 조건에서 n회 반복 측정하고, 평균의 표준편차(s/√n)로 표준불확도를 산출. 자유도 = n-1. '실험적 방법'이라고도 합니다.",
        "tags": ["불확도", "GUM"],
    },
    {
        "term": "B형 평가",
        "short": "반복 측정 이외의 방법(교정성적서, 사양서, 경험 등)으로 표준불확도를 구하는 방법",
        "detail": "교정성적서의 불확도, 제조사 사양, 핸드북 데이터, 경험 등 비통계적 정보에서 표준불확도를 추정. 분포 가정(정규, 균일, 삼각 등)이 필요합니다.",
        "tags": ["불확도", "GUM"],
    },
    {
        "term": "합성불확도 (uc)",
        "short": "모든 불확도 성분을 합성한 전체 표준불확도",
        "detail": "각 입력량의 표준불확도에 감도계수(ci)를 곱하여 제곱합의 제곱근으로 구함. Welch-Satterthwaite 식으로 유효자유도를 계산. uc = √(Σ ci²·u(xi)²)",
        "tags": ["불확도", "GUM"],
    },
    {
        "term": "확장불확도 (U)",
        "short": "합성불확도에 포함인자(k)를 곱한 신뢰구간. U = k × uc",
        "detail": "보통 k≈2 (신뢰수준 약 95%)를 사용. KOLAS 교정성적서에 보고되는 값. '확장불확도 U = 0.05 μm (k=2)' 같은 형태로 표기.",
        "tags": ["불확도", "GUM", "KOLAS"],
    },
    {
        "term": "포함인자 (k)",
        "short": "확장불확도를 구하기 위해 합성불확도에 곱하는 계수. 보통 k≈2",
        "detail": "유효자유도(νeff)와 신뢰수준(보통 95%)에서 t-분포표로 결정. νeff가 충분히 크면(>30) k≈2. 작으면 k는 2보다 큼.",
        "tags": ["불확도", "GUM"],
    },
    {
        "term": "CMC",
        "short": "Calibration and Measurement Capability — 교정측정능력",
        "detail": "기관이 정상 운영 조건에서 달성할 수 있는 최소 불확도. KOLAS 인정범위에 기재되며, 고객에게 제공 가능한 불확도의 하한. MetroAI의 역설계 기능으로 CMC 달성 가능성을 미리 검증할 수 있습니다.",
        "tags": ["KOLAS", "기관인정"],
    },
    {
        "term": "소급성 (Traceability)",
        "short": "측정 결과를 국가표준(KRISS)까지 끊김 없이 연결할 수 있는 성질",
        "detail": "모든 교정은 더 상위 표준에 의해 교정된 표준기를 사용해야 하며, 최종적으로 국가측정표준(KRISS)까지 연결되어야 합니다. 소급성 체계도로 이를 문서화.",
        "tags": ["KOLAS", "교정"],
    },
    {
        "term": "Welch-Satterthwaite 식",
        "short": "합성불확도의 유효자유도(νeff)를 계산하는 근사식",
        "detail": "νeff = uc⁴ / Σ(ci·u(xi))⁴/νi — 각 불확도 성분의 자유도를 가중 합성하여 전체 유효자유도를 구합니다. 이 값으로 t-분포에서 포함인자 k를 결정.",
        "tags": ["불확도", "GUM"],
    },
    {
        "term": "숙련도시험 (PT)",
        "short": "Proficiency Testing — 여러 기관이 같은 시료를 측정하여 기관 간 일치도를 확인하는 시험",
        "detail": "KOLAS 인정기관은 정기적으로 PT에 참가해야 합니다. z-score, En number, ζ-score로 판정. 불만족(|z|>3) 시 시정조치 필요.",
        "tags": ["KOLAS", "PT"],
    },
    {
        "term": "z-score",
        "short": "PT 결과 판정 지표. z = (x - X) / σ_pt. |z| < 2: 만족, 2~3: 주의, >3: 불만족",
        "detail": "참가기관 측정값(x)과 배정값(X)의 차이를 숙련도 평가용 표준편차(σ_pt)로 나눈 값. ISO 13528 기반.",
        "tags": ["PT", "판정"],
    },
    {
        "term": "En number",
        "short": "PT 결과 판정 지표. En = (x - X) / √(U_lab² + U_ref²). |En| < 1: 적합",
        "detail": "참가기관 측정값과 기준값의 차이를 양측 확장불확도의 합으로 나눈 값. 불확도가 적절한지를 함께 판정.",
        "tags": ["PT", "판정"],
    },
    {
        "term": "KOLAS-G-001",
        "short": "KOLAS 인정기관 인정 기준 해설서",
        "detail": "ISO/IEC 17025 요구사항을 한국 실정에 맞게 해설한 문서. 심사관이 이 기준으로 평가합니다. 수시 개정되므로 최신본 확인 필요.",
        "tags": ["KOLAS", "기준"],
    },
    {
        "term": "KOLAS-G-002",
        "short": "측정불확도 추정 및 표현을 위한 지침",
        "detail": "GUM을 기반으로 한국 KOLAS 기관이 불확도를 산출하고 보고할 때의 양식과 표현 방법을 규정. MetroAI는 이 양식을 자동 생성합니다.",
        "tags": ["KOLAS", "불확도", "기준"],
    },
    {
        "term": "KOLAS-G-004",
        "short": "교정성적서 발행 지침",
        "detail": "교정성적서에 포함되어야 하는 항목, 양식, 서명, 보관 방법 등을 규정.",
        "tags": ["KOLAS", "교정", "기준"],
    },
    {
        "term": "역설계 (Reverse Uncertainty Engineering)",
        "short": "목표 불확도(CMC)에서 각 불확도 성분의 허용 한계를 역으로 산출하는 기법",
        "detail": "MetroAI 독자 기능 (세계 최초). 예: 'CMC 0.1 μm를 달성하려면 반복성은 얼마 이하여야 하는가?' 장비 업그레이드 의사결정, 신규 품목 추가 계획에 활용.",
        "tags": ["불확도", "MetroAI"],
    },
    {
        "term": "감도계수 (ci)",
        "short": "입력량의 변화가 출력량에 미치는 영향의 정도. ci = ∂f/∂xi",
        "detail": "측정 모델 f의 입력량 xi에 대한 편미분값. 합성불확도 계산 시 각 성분의 가중치 역할을 합니다.",
        "tags": ["불확도", "GUM"],
    },
]

# ──────────────────────────────────────────
# 필터링 및 표시
# ──────────────────────────────────────────
filtered = glossary
if search.strip():
    query = search.strip().lower()
    filtered = [
        g for g in glossary
        if query in g["term"].lower()
        or query in g["short"].lower()
        or any(query in t.lower() for t in g["tags"])
    ]

if not filtered:
    st.warning(f"'{search}'에 해당하는 용어를 찾을 수 없습니다.")
else:
    st.caption(f"총 {len(filtered)}개 용어")

    for g in filtered:
        tags_str = " · ".join(f"`{t}`" for t in g["tags"])
        with st.expander(f"**{g['term']}** — {g['short']}"):
            st.markdown(g["detail"])
            st.caption(f"관련: {tags_str}")
