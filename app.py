"""MetroAI — 랜딩 페이지.

Streamlit Cloud 진입점 겸 랜딩 페이지.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

st.set_page_config(
    page_title="MetroAI — KOLAS 불확도 예산 자동화",
    page_icon="📐",
    layout="wide",
)

# ──────────────────────────────────────────
# 히어로 섹션
# ──────────────────────────────────────────
st.markdown(
    """
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0.2rem;">📐 MetroAI</h1>
        <p style="font-size: 1.4rem; color: #555; margin-bottom: 2rem;">
            KOLAS 측정불확도 예산표, 5분 만에 완성
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_center = st.columns([1, 2, 1])[1]
with col_center:
    if st.button("지금 시작하기 →", type="primary", use_container_width=True):
        st.switch_page("pages/1_📐_불확도_계산.py")

st.divider()

# ──────────────────────────────────────────
# 기능 소개 (3컬럼)
# ──────────────────────────────────────────
st.markdown("### 주요 기능")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
        #### 📐 불확도 자동 계산
        GUM 기반 합성불확도 + MCM 검증,
        KOLAS-G-002 양식 지원.
        위자드 모드로 GUM을 몰라도 OK!
        """
    )

with c2:
    st.markdown(
        """
        #### 📊 숙련도시험 분석
        z-score, En number, ζ-score
        자동 판정. CSV 일괄 업로드 지원.
        """
    )

with c3:
    st.markdown(
        """
        #### 📄 교정성적서 생성
        KOLAS 양식 교정성적서 PDF
        원클릭 생성. 불확도 예산표 포함.
        """
    )

st.divider()

# ──────────────────────────────────────────
# 차별점
# ──────────────────────────────────────────
st.markdown("### 왜 MetroAI?")

d1, d2 = st.columns(2)
with d1:
    st.markdown(
        """
        **엑셀 수작업 → 자동화**
        기존 1~2시간 → 5분으로 단축

        **GUM을 몰라도 OK**
        위자드 모드로 쉬운 단계별 입력
        """
    )
with d2:
    st.markdown(
        """
        **한국 KOLAS 특화**
        KOLAS-G-001/G-002 양식 완벽 지원

        **무료로 시작**
        Free 플랜 3건/월
        """
    )

st.divider()

# ──────────────────────────────────────────
# 가격표
# ──────────────────────────────────────────
st.markdown("### 요금제")

p1, p2, p3, p4 = st.columns(4)

with p1:
    st.markdown(
        """
        ##### Free
        **₩0**

        불확도 3건/월
        """
    )

with p2:
    st.markdown(
        """
        ##### Pro
        **₩29,900/월**

        무제한 계산
        """
    )

with p3:
    st.markdown(
        """
        ##### Team
        **₩79,900/월**

        다중 사용자
        *(출시 예정)*
        """
    )

with p4:
    st.markdown(
        """
        ##### Enterprise
        **₩199,900/월**

        API 포함
        *(출시 예정)*
        """
    )

st.divider()

# ──────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 0.85rem; padding: 1rem 0;">
        MetroAI v0.1.0 | GUM (ISO/IEC Guide 98-3) 준거 | KOLAS-G-002 양식 지원<br>
        문의: kyb8801@gmail.com
    </div>
    """,
    unsafe_allow_html=True,
)
