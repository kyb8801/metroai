"""MetroAI — 전문적인 랜딩 페이지.

Streamlit Cloud 진입점. KOLAS 측정불확도 자동화 플랫폼 소개.
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
# 커스텀 CSS 스타일
# ──────────────────────────────────────────
st.markdown(
    """
    <style>
    .hero-container {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .hero-tagline {
        font-size: 1.5rem;
        font-weight: 300;
        margin-bottom: 2rem;
        opacity: 0.95;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        height: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #222;
    }
    .feature-desc {
        color: #666;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    .pricing-card {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        transition: all 0.2s;
    }
    .pricing-card.recommended {
        border-color: #667eea;
        background: #f5f7ff;
        transform: scale(1.05);
    }
    .pricing-card:hover {
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
    }
    .pricing-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .pricing-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .pricing-price {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 1rem;
    }
    .pricing-features {
        text-align: left;
        font-size: 0.9rem;
        color: #666;
        line-height: 1.8;
    }
    .comparison-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .comparison-table th,
    .comparison-table td {
        padding: 1rem;
        text-align: left;
        border-bottom: 1px solid #e0e0e0;
    }
    .comparison-table th {
        background: #f5f7ff;
        font-weight: 600;
        color: #667eea;
    }
    .comparison-table tr:hover {
        background: #f8f9fa;
    }
    .before-cell {
        color: #d32f2f;
        font-weight: 500;
    }
    .after-cell {
        color: #388e3c;
        font-weight: 500;
    }
    .step-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        border-top: 4px solid #667eea;
    }
    .step-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    .step-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #222;
    }
    .step-desc {
        color: #666;
        font-size: 0.9rem;
    }
    .faq-item {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .faq-question {
        font-weight: 600;
        color: #667eea;
        margin-bottom: 0.5rem;
        font-size: 1.05rem;
    }
    .footer-content {
        text-align: center;
        color: #888;
        font-size: 0.9rem;
        padding: 2rem 0;
        border-top: 1px solid #e0e0e0;
        line-height: 1.8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# 1. 히어로 섹션 (개선)
# ──────────────────────────────────────────
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">📐 MetroAI</div>
        <div class="hero-tagline">KOLAS 측정불확도 예산표, 5분 만에 완성</div>
        <p style="margin-bottom: 2rem; font-size: 1.05rem; opacity: 0.9;">
            복잡한 GUM 계산을 자동화하고, KOLAS 심사 준비를 앞당기세요.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_cta = st.columns([1, 2, 1])[1]
with col_cta:
    if st.button("🚀 지금 시작하기", type="primary", use_container_width=True):
        st.switch_page("pages/1_📐_불확도_계산.py")

st.markdown("")

# ──────────────────────────────────────────
# 2. 어떻게 작동하나요? (NEW - 3단계)
# ──────────────────────────────────────────
st.markdown("## 🎯 어떻게 작동하나요?")
st.markdown("MetroAI의 위자드 모드로 3단계만 거치면 완성됩니다.")

step1, step2, step3 = st.columns(3)

with step1:
    st.markdown(
        """
        <div class="step-card">
            <div class="step-number">1️⃣</div>
            <div class="step-title">교정 분야 선택</div>
            <div class="step-desc">
                블록게이지, 분동, 온도, 압력 등<br>
                교정 분야를 선택하세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with step2:
    st.markdown(
        """
        <div class="step-card">
            <div class="step-number">2️⃣</div>
            <div class="step-title">측정값 입력</div>
            <div class="step-desc">
                위자드가 GUM 불확도 요소를<br>
                자동으로 분류하고 안내합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with step3:
    st.markdown(
        """
        <div class="step-card">
            <div class="step-number">3️⃣</div>
            <div class="step-title">결과 확인</div>
            <div class="step-desc">
                예산표 + MCM 검증 + PDF/엑셀<br>
                한 번에 생성되어 다운로드됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# ──────────────────────────────────────────
# 3. 주요 기능 (개선 - 6개 카드, 2x3 그리드)
# ──────────────────────────────────────────
st.markdown("## ⚙️ 주요 기능")
st.markdown("MetroAI는 KOLAS 교정 업무의 전체 흐름을 자동화합니다.")

# 첫 번째 행
feature_row1_col1, feature_row1_col2, feature_row1_col3 = st.columns(3)

with feature_row1_col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📐</div>
            <div class="feature-title">불확도 자동 계산</div>
            <div class="feature-desc">
                GUM 기반 합성불확도를 자동으로 계산하고,
                MCM(몬테카를로)으로 검증합니다.
                위자드 모드로 GUM을 몰라도 괜찮습니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature_row1_col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🔬</div>
            <div class="feature-title">MCM 검증</div>
            <div class="feature-desc">
                GUM Supplement 1 기반 몬테카를로 시뮬레이션으로
                예산표 신뢰성을 검증합니다.
                심사 준비 시 강력한 근거 자료가 됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature_row1_col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">숙련도시험 분석</div>
            <div class="feature-desc">
                z-score, En number, ζ-score를 자동 계산하고
                CSV 일괄 업로드를 지원합니다.
                PT 결과를 즉시 평가합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 두 번째 행
feature_row2_col1, feature_row2_col2, feature_row2_col3 = st.columns(3)

with feature_row2_col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <div class="feature-title">교정성적서 PDF</div>
            <div class="feature-desc">
                KOLAS 양식 교정성적서를 원클릭으로 생성합니다.
                불확도 예산표와 MCM 그래프가 자동 포함됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature_row2_col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">KOLAS 양식 엑셀</div>
            <div class="feature-desc">
                KOLAS-G-002 불확도 예산표 양식을
                자동으로 생성하여 다운로드합니다.
                심사 제출 전 형식 검토가 끝나있습니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature_row2_col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">✨</div>
            <div class="feature-title">위자드 모드</div>
            <div class="feature-desc">
                GUM 분류와 표준불확도 입력을 단계별로 안내합니다.
                비전문가도 정확한 불확도 예산표를 만들 수 있습니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# ──────────────────────────────────────────
# 4. Before/After 비교 (NEW)
# ──────────────────────────────────────────
st.markdown("## 📈 Before vs After")
st.markdown("MetroAI 도입 전후, 작업 효율이 얼마나 개선되는지 확인하세요.")

comparison_data = [
    ["구분", "엑셀 수작업", "MetroAI"],
    ["작업시간", "1~2시간", "5분"],
    ["오류 위험", "수식 오류 가능 ⚠️", "자동 검증 ✅"],
    ["MCM 검증", "별도 코딩 필요", "원클릭 ✅"],
    ["양식 작성", "수동 작성", "KOLAS-G-002 자동 ✅"],
    ["PT 분석", "수동 계산", "CSV 업로드 자동 ✅"],
    ["성적서 생성", "레이아웃 조정 필요", "원클릭 PDF ✅"],
    ["감사 추적", "어려움", "완전 기록 ✅"],
]

st.markdown("<table class='comparison-table'>", unsafe_allow_html=True)
for i, row in enumerate(comparison_data):
    if i == 0:
        st.markdown(
            f"<tr><th>{row[0]}</th><th style='color: #d32f2f;'>{row[1]}</th><th style='color: #388e3c;'>{row[2]}</th></tr>",
            unsafe_allow_html=True,
        )
    else:
        cell1 = f"<span class='before-cell'>{row[1]}</span>"
        cell2 = f"<span class='after-cell'>{row[2]}</span>"
        st.markdown(f"<tr><td><strong>{row[0]}</strong></td><td>{cell1}</td><td>{cell2}</td></tr>", unsafe_allow_html=True)
st.markdown("</table>", unsafe_allow_html=True)

st.markdown("")

# ──────────────────────────────────────────
# 5. 가격표 (개선)
# ──────────────────────────────────────────
st.markdown("## 💰 요금제")
st.markdown("언제든지 업그레이드 또는 다운그레이드할 수 있습니다. 신용카드가 필요하지 않습니다.")

pricing_col1, pricing_col2, pricing_col3, pricing_col4 = st.columns(4)

with pricing_col1:
    st.markdown(
        """
        <div class="pricing-card">
            <div class="pricing-title">Free</div>
            <div class="pricing-price">₩0</div>
            <div class="pricing-features">
                ✓ 불확도 계산 3건/월<br>
                ✓ PDF 생성<br>
                ✓ 기본 MCM 검증<br>
                ✓ 커뮤니티 지원
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with pricing_col2:
    st.markdown(
        """
        <div class="pricing-card recommended">
            <div class="pricing-badge">추천</div>
            <div class="pricing-title">Pro</div>
            <div class="pricing-price">₩29,900</div>
            <p style="color: #888; font-size: 0.9rem;">월간 결제</p>
            <div class="pricing-features">
                ✓ 무제한 계산<br>
                ✓ PT 분석 포함<br>
                ✓ 고급 MCM 옵션<br>
                ✓ KOLAS 양식 엑셀<br>
                ✓ 이메일 지원<br>
                ✓ 우선 업데이트
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with pricing_col3:
    st.markdown(
        """
        <div class="pricing-card">
            <p style="color: #999; font-style: italic;">출시 예정</p>
            <div class="pricing-title">Team</div>
            <div class="pricing-price">₩79,900</div>
            <p style="color: #888; font-size: 0.9rem;">월간 결제</p>
            <div class="pricing-features">
                ✓ Pro 전체 포함<br>
                ✓ 다중 사용자 (5명)<br>
                ✓ 조직 관리<br>
                ✓ 팀 분석 대시보드<br>
                ✓ 우선 지원
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with pricing_col4:
    st.markdown(
        """
        <div class="pricing-card">
            <p style="color: #999; font-style: italic;">출시 예정</p>
            <div class="pricing-title">Enterprise</div>
            <div class="pricing-price">맞춤 가격</div>
            <p style="color: #888; font-size: 0.9rem;">연간 계약</p>
            <div class="pricing-features">
                ✓ Team 전체 포함<br>
                ✓ REST API 접근<br>
                ✓ 커스텀 구성<br>
                ✓ SSO/SAML<br>
                ✓ 24/7 지원
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# ──────────────────────────────────────────
# 6. FAQ (NEW)
# ──────────────────────────────────────────
st.markdown("## ❓ 자주 묻는 질문")

with st.expander("🔬 GUM이 뭔가요?", expanded=False):
    st.markdown(
        """
        **GUM (Guide to the Expression of Uncertainty in Measurement)**은
        **ISO/IEC Guide 98-3** 표준으로, 측정 결과의 불확도를 표현하는 국제 표준입니다.

        - **불확도란?** 측정값이 참값으로부터 벗어날 수 있는 범위
        - **A형 불확도:** 반복 측정으로 산출 (표준편차)
        - **B형 불확도:** 교정성적서, 기기 사양 등에서 유추
        - **합성불확도:** A형과 B형을 합성한 전체 불확도
        - **확장불확도:** 신뢰도 95% 수준의 범위 (합성불확도 × k)

        MetroAI는 이 모든 과정을 자동화하므로 GUM의 세부 내용을 모르셔도 괜찮습니다.
        위자드 모드가 단계별로 안내해줍니다.
        """
    )

with st.expander("✅ KOLAS 심사에 사용 가능한가요?", expanded=False):
    st.markdown(
        """
        **네, 완벽히 지원합니다.**

        MetroAI는:
        - ✓ **GUM 준거:** ISO/IEC Guide 98-3 기반 계산
        - ✓ **KOLAS-G-002 양식:** KOLAS 불확도 예산표 자동 생성
        - ✓ **MCM 검증:** GUM Supplement 1 기반 몬테카를로 시뮬레이션
        - ✓ **감사 추적:** 모든 계산 과정 기록 및 재현 가능

        심사관들이 요구하는 모든 근거 자료를 MetroAI가 자동으로 생성하므로,
        심사 준비 시 신뢰성 높은 자료로 사용 가능합니다.

        실제로 KOLAS 심사 경험이 있는 고객들이 MetroAI를 추천하고 있습니다.
        """
    )

with st.expander("🏭 어떤 교정 분야를 지원하나요?", expanded=False):
    st.markdown(
        """
        **현재 지원 중인 분야:**
        - 길이 측정 (블록게이지, 게이지블록)
        - 질량 측정 (분동, 저울)
        - 온도 측정 (온도계, 써모커플)
        - 압력 측정 (압력계, 진공게이지)

        **곧 추가될 분야:**
        - 전기 (전압, 전류, 저항)
        - 시간/주파수
        - 습도/이슬점

        필요한 분야가 있으시면 고객 피드백으로 우선순위를 정하고 있습니다.
        kyb8801@gmail.com으로 문의하세요.
        """
    )

with st.expander("🎲 MCM 검증이 왜 필요한가요?", expanded=False):
    st.markdown(
        """
        **MCM (Monte Carlo Method)은 GUM 계산의 신뢰성을 검증합니다.**

        GUM은:
        - ✓ 선형 모델에 강함
        - ✗ 비선형 모델에서 오차 가능

        MCM은:
        - ✓ GUM Supplement 1 권고사항
        - ✓ 모든 분포(정규분포, 균등분포 등)에 적용 가능
        - ✓ 비선형 모델도 정확히 처리

        MetroAI는 자동으로 GUM 계산과 MCM을 동시에 수행하고,
        두 결과를 비교하여 일치도를 표시합니다.

        심사관들이 "MCM으로도 검증했나요?"라는 질문을 자주 하는데,
        MetroAI를 사용하면 이 질문에 즉시 답변할 수 있습니다.
        """
    )

with st.expander("💳 무료 플랜의 제한사항은?", expanded=False):
    st.markdown(
        """
        **Free 플랜:**
        - 월 3건까지 계산 가능
        - 모든 기능 사용 가능 (제한 없음)
        - PDF + 엑셀 다운로드 가능
        - MCM 검증 포함

        **Pro 플랜으로 업그레이드하면:**
        - 무제한 계산
        - 우선 지원
        - 신규 기능 우선 제공
        - 월 ₩29,900

        언제든 업그레이드/다운그레이드할 수 있으며, 신용카드가 필요하지 않습니다.
        """
    )

st.markdown("")

# ──────────────────────────────────────────
# 7. 푸터 (개선)
# ──────────────────────────────────────────
st.markdown(
    """
    <div class="footer-content">
        <strong>MetroAI v0.2.0</strong><br>
        GUM (ISO/IEC Guide 98-3) 준거 | KOLAS-G-002 양식 지원<br>
        GUM Supplement 1 기반 MCM 검증<br><br>
        📧 문의: <strong>kyb8801@gmail.com</strong><br>
        🏢 한국 KOLAS 인정 교정기관 전용<br>
        © 2025 MetroAI. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True,
)
