"""MetroAI — 전문적인 랜딩 페이지 (v0.5.0).

Streamlit Cloud 진입점. KOLAS 컴플라이언스 자동화 플랫폼 소개.
슈어소프트 벤치마킹 반영:
 - 5개 도구 카드 병렬 제시
 - 지원 표준 배지 스트립
 - "심사 서류 N종 자동 생성" 카운터
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
    page_title="MetroAI — KOLAS 심사 준비 자동화 플랫폼",
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
        padding: 3.5rem 2rem 2.5rem 2rem;
        background: linear-gradient(135deg, #1E40AF 0%, #0B1220 100%);
        color: white;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        border: 1px solid #1E40AF;
    }
    .hero-title {
        font-size: 3.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .hero-tagline {
        font-size: 1.4rem;
        font-weight: 300;
        margin-bottom: 0.5rem;
        opacity: 0.95;
    }
    .hero-sub {
        font-size: 1.0rem;
        opacity: 0.85;
    }
    /* 표준 배지 스트립 */
    .standards-strip {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.5rem;
        padding: 1rem 0 2rem 0;
    }
    .std-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        background: #F8FAFC;
        color: #1E40AF;
        border: 1px solid #06B6D4;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    .std-badge.primary {
        background: #1E40AF;
        color: white;
        border-color: #1E40AF;
    }
    /* 산출물 카운터 */
    .counter-box {
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
        border: 2px solid #06B6D4;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0 2rem 0;
    }
    .counter-label {
        font-size: 1.0rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .counter-number {
        font-size: 3.5rem;
        font-weight: 800;
        color: #1E40AF;
        line-height: 1.0;
        margin: 0.3rem 0;
    }
    .counter-unit {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    .counter-list {
        display: inline-block;
        text-align: left;
        font-size: 0.92rem;
        color: #555;
        line-height: 1.8;
        margin-top: 0.5rem;
    }
    /* 5-도구 카드 */
    .tool-card {
        background: white;
        padding: 1.8rem 1.2rem;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        height: 100%;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    .tool-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(74, 78, 160, 0.12);
        border-color: #1E40AF;
    }
    .tool-card.featured {
        border: 2px solid #1E40AF;
        background: linear-gradient(180deg, #F8FAFC 0%, #ffffff 60%);
    }
    .tool-card.disabled {
        opacity: 0.75;
        background: #F1F5F9;
    }
    .tool-icon {
        font-size: 2.8rem;
        margin-bottom: 0.8rem;
    }
    .tool-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #222;
        margin-bottom: 0.3rem;
    }
    .tool-badge {
        font-size: 0.72rem;
        padding: 0.18rem 0.55rem;
        background: #FEF3C7;
        color: #F59E0B;
        border-radius: 10px;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    .tool-badge.first {
        background: #FEE2E2;
        color: #EF4444;
    }
    .tool-badge.soon {
        background: #E2E8F0;
        color: #475569;
    }
    .tool-desc {
        color: #666;
        font-size: 0.88rem;
        line-height: 1.55;
        flex-grow: 1;
        margin-bottom: 1rem;
    }
    /* 3단계 가이드 */
    .step-card {
        background: #F8FAFC;
        padding: 1.5rem 1.2rem;
        border-radius: 10px;
        text-align: center;
        border-top: 4px solid #1E40AF;
        height: 100%;
    }
    .step-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E40AF;
        margin-bottom: 0.3rem;
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
        line-height: 1.55;
    }
    /* Before/After 테이블 */
    .comparison-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .comparison-table th,
    .comparison-table td {
        padding: 0.9rem;
        text-align: left;
        border-bottom: 1px solid #E2E8F0;
    }
    .comparison-table th {
        background: #F8FAFC;
        font-weight: 600;
        color: #1E40AF;
    }
    .before-cell { color: #EF4444; font-weight: 500; }
    .after-cell  { color: #10B981; font-weight: 500; }
    /* 요금제 */
    .pricing-card {
        border: 2px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.8rem 1.2rem;
        text-align: center;
        transition: all 0.2s;
        height: 100%;
    }
    .pricing-card.recommended {
        border-color: #1E40AF;
        background: #F8FAFC;
    }
    .pricing-badge {
        display: inline-block;
        background: #1E40AF;
        color: white;
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .pricing-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .pricing-price {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E40AF;
        margin-bottom: 0.7rem;
    }
    .pricing-features {
        text-align: left;
        font-size: 0.88rem;
        color: #666;
        line-height: 1.8;
    }
    .footer-content {
        text-align: center;
        color: #888;
        font-size: 0.88rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #E2E8F0;
        line-height: 1.7;
        margin-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# 1. 히어로
# ──────────────────────────────────────────
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">📐 MetroAI</div>
        <div class="hero-tagline">KOLAS 인정, 어디서부터 시작할지 모르겠다면</div>
        <div class="hero-sub">
            심사 준비 체크리스트부터 불확도 예산표·교정성적서 자동 생성까지 — MetroAI가 안내합니다.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# CTA 버튼
col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
with col_cta2:
    cta_a, cta_b = st.columns(2)
    with cta_a:
        if st.button("🚀 불확도 계산 바로가기", type="primary", use_container_width=True):
            st.switch_page("pages/1_📐_불확도_계산.py")
    with cta_b:
        if st.button("📄 교정성적서 만들기", use_container_width=True):
            st.switch_page("pages/3_📄_교정성적서.py")

# ──────────────────────────────────────────
# 2. 지원 표준 배지 스트립 (NEW — 슈어소프트 B-2)
# ──────────────────────────────────────────
st.markdown(
    """
    <div class="standards-strip">
        <span class="std-badge primary">ISO/IEC 17025:2017</span>
        <span class="std-badge primary">KOLAS-G-001</span>
        <span class="std-badge primary">KOLAS-G-002</span>
        <span class="std-badge">KOLAS-G-004</span>
        <span class="std-badge">GUM (ISO/IEC Guide 98-3)</span>
        <span class="std-badge">GUM Supplement 1 (MCM)</span>
        <span class="std-badge">ISO 13528</span>
        <span class="std-badge">ISO 17043</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# 3. 산출물 카운터 (NEW — 슈어소프트 B-3)
# ──────────────────────────────────────────
st.markdown(
    """
    <div class="counter-box">
        <div class="counter-label">KOLAS 심사 서류 23종 중</div>
        <div class="counter-number">2</div>
        <div class="counter-unit">종 자동 생성 중 &nbsp;·&nbsp; 로드맵에서 5종까지 확장</div>
        <div class="counter-list">
            ✅ 측정불확도 예산표 (KOLAS-G-002 양식)<br>
            ✅ 교정성적서 PDF<br>
            🔄 PT 결과 보고서 <em style="color:#888;">(로드맵)</em><br>
            🔄 소급성 체계도 <em style="color:#888;">(로드맵)</em><br>
            🔄 장비 교정 이력 관리대장 <em style="color:#888;">(로드맵)</em>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# 4. 3단계 가이드
# ──────────────────────────────────────────
st.markdown("## 🎯 KOLAS 인정, 어떻게 준비하나요?")
st.caption("MetroAI는 KOLAS 심사의 전체 여정을 3단계로 안내합니다.")

step1, step2, step3 = st.columns(3)
with step1:
    st.markdown(
        """
        <div class="step-card">
            <div class="step-number">1️⃣</div>
            <div class="step-title">KOLAS 이해하기</div>
            <div class="step-desc">
                KOLAS 인정이 무엇인지,<br>
                우리 기관에 필요한지 확인하고<br>
                심사 준비 흐름을 파악하세요.
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
            <div class="step-title">서류 준비</div>
            <div class="step-desc">
                심사 제출 서류 23종 체크리스트로<br>
                무엇이 필요한지 한눈에 확인하고,<br>
                MetroAI가 자동 생성 가능한 것부터 시작.
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
            <div class="step-title">불확도 예산표 작성</div>
            <div class="step-desc">
                GUM 기반 불확도 계산부터<br>
                MCM 검증·교정성적서 PDF까지<br>
                원스톱으로 완성합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("&nbsp;")

# ──────────────────────────────────────────
# 5. MetroAI 도구 세트 — 5개 카드 (NEW — 슈어소프트 B-1)
# ──────────────────────────────────────────
st.markdown("## ⚙️ MetroAI 도구 세트")
st.caption("단일 도구가 아닌, KOLAS 업무 전 과정을 커버하는 5개 도구의 집합입니다.")

tool_cols = st.columns(5)

with tool_cols[0]:
    st.markdown(
        """
        <div class="tool-card featured">
            <div class="tool-icon">📐</div>
            <div class="tool-name">불확도 계산</div>
            <div class="tool-badge">핵심 도구</div>
            <div class="tool-desc">
                GUM 기반 합성불확도 자동 계산,<br>
                MCM 몬테카를로 검증,<br>
                KOLAS-G-002 양식 출력.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("📐 시작하기", key="tool_calc", use_container_width=True):
        st.switch_page("pages/1_📐_불확도_계산.py")

with tool_cols[1]:
    st.markdown(
        """
        <div class="tool-card">
            <div class="tool-icon">📊</div>
            <div class="tool-name">PT 분석</div>
            <div class="tool-badge">ISO 13528</div>
            <div class="tool-desc">
                숙련도시험 결과를<br>
                z-score / En / ζ-score로<br>
                자동 판정합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("📊 시작하기", key="tool_pt", use_container_width=True):
        st.switch_page("pages/2_📊_PT_분석.py")

with tool_cols[2]:
    st.markdown(
        """
        <div class="tool-card">
            <div class="tool-icon">📄</div>
            <div class="tool-name">교정성적서</div>
            <div class="tool-badge">KOLAS 양식</div>
            <div class="tool-desc">
                KOLAS 양식 교정성적서 PDF,<br>
                심사 서류 체크리스트,<br>
                예시 다운로드 제공.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("📄 시작하기", key="tool_cert", use_container_width=True):
        st.switch_page("pages/3_📄_교정성적서.py")

with tool_cols[3]:
    st.markdown(
        """
        <div class="tool-card featured">
            <div class="tool-icon">🔄</div>
            <div class="tool-name">불확도 역설계</div>
            <div class="tool-badge first">🌟 세계 최초</div>
            <div class="tool-desc">
                목표 불확도에서<br>
                각 요소의 허용 한계를<br>
                역으로 산출합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🔄 시작하기", key="tool_rev", use_container_width=True):
        st.switch_page("pages/4_🔄_불확도_역설계.py")

with tool_cols[4]:
    st.markdown(
        """
        <div class="tool-card disabled">
            <div class="tool-icon">🔑</div>
            <div class="tool-name">AI 심사 컨설팅</div>
            <div class="tool-badge soon">Phase 5 · 출시 예정</div>
            <div class="tool-desc">
                KOLAS 심사 대비<br>
                셀프 체크 + 전문가 연결.<br>
                <em>로드맵 진행 중.</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button("🔑 티저 보기", key="tool_consult", use_container_width=True, disabled=True)

st.markdown("&nbsp;")

# ──────────────────────────────────────────
# 6. Before/After 비교
# ──────────────────────────────────────────
st.markdown("## 📈 Before vs After")
st.caption("엑셀 수작업과 MetroAI의 차이.")

comparison_data = [
    ("작업시간", "1~2시간", "5분"),
    ("오류 위험", "수식 오류 가능 ⚠️", "자동 검증 ✅"),
    ("MCM 검증", "별도 코딩 필요", "원클릭 ✅"),
    ("KOLAS 양식", "수동 작성", "KOLAS-G-002 자동 ✅"),
    ("PT 분석", "수동 계산", "CSV 업로드 자동 ✅"),
    ("성적서 생성", "레이아웃 조정 필요", "원클릭 PDF ✅"),
    ("감사 추적", "어려움", "완전 기록 ✅"),
]

table_html = "<table class='comparison-table'>"
table_html += (
    "<tr><th>구분</th>"
    "<th style='color:#EF4444;'>엑셀 수작업</th>"
    "<th style='color:#10B981;'>MetroAI</th></tr>"
)
for label, before, after in comparison_data:
    table_html += (
        f"<tr><td><strong>{label}</strong></td>"
        f"<td><span class='before-cell'>{before}</span></td>"
        f"<td><span class='after-cell'>{after}</span></td></tr>"
    )
table_html += "</table>"
st.markdown(table_html, unsafe_allow_html=True)

st.markdown("&nbsp;")

# ──────────────────────────────────────────
# 7. 요금제 (축소)
# ──────────────────────────────────────────
st.markdown("## 💰 요금제")
st.caption("Free로 먼저 체험해보세요. 신용카드 필요 없음.")

p1, p2, p3 = st.columns(3)

with p1:
    st.markdown(
        """
        <div class="pricing-card">
            <div class="pricing-title">Free</div>
            <div class="pricing-price">₩0</div>
            <div class="pricing-features">
                ✓ 불확도 계산 3건/월<br>
                ✓ PDF / 엑셀 다운로드<br>
                ✓ MCM 검증<br>
                ✓ 심사 체크리스트
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with p2:
    st.markdown(
        """
        <div class="pricing-card recommended">
            <div class="pricing-badge">추천</div>
            <div class="pricing-title">Pro</div>
            <div class="pricing-price">₩29,900<span style='font-size:0.9rem;color:#888;'>/월</span></div>
            <div class="pricing-features">
                ✓ 무제한 계산<br>
                ✓ 역설계 풀 기능<br>
                ✓ PT 분석 풀 기능<br>
                ✓ 이메일 지원<br>
                ✓ 우선 업데이트
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with p3:
    st.markdown(
        """
        <div class="pricing-card">
            <p style="color:#999;font-style:italic;font-size:0.8rem;margin:0 0 0.3rem 0;">출시 예정</p>
            <div class="pricing-title">Consulting</div>
            <div class="pricing-price">맞춤</div>
            <div class="pricing-features">
                ✓ Pro 전체 포함<br>
                ✓ AI 심사 셀프체크<br>
                ✓ KOLAS 전문가 연결<br>
                ✓ 기관 맞춤 컨설팅<br>
                ✓ Phase 5 예정
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("&nbsp;")

# ──────────────────────────────────────────
# 8. FAQ
# ──────────────────────────────────────────
st.markdown("## ❓ 자주 묻는 질문")

with st.expander("🏛️ KOLAS 인정이 뭔가요?", expanded=False):
    st.markdown(
        """
        **KOLAS (Korea Laboratory Accreditation Scheme)** 는 한국인정기구(KAB)가 운영하는
        **ISO/IEC 17025** 기반의 시험·교정 기관 인정 제도입니다.

        - **적용 대상:** 교정기관, 시험기관, 표준물질 생산기관, 숙련도시험 운영기관, 의료시험기관
        - **인정 표준:** ISO/IEC 17025 (시험·교정 기관의 적격성 요구사항)
        - **심사 절차:** 신청 → 서류심사 → 현장평가 → 인정서 발급 (평균 6~12개월)
        - **재심사:** 4년 주기 (정기 감시평가는 매년)

        MetroAI는 이 과정에서 가장 어려운 **불확도 예산표 작성, 교정성적서 생성, PT 분석**을 자동화합니다.
        """
    )

with st.expander("🔬 GUM이 뭔가요?", expanded=False):
    st.markdown(
        """
        **GUM (Guide to the Expression of Uncertainty in Measurement)** — ISO/IEC Guide 98-3.
        측정 결과의 불확도를 표현하는 국제 표준입니다.

        - **A형 불확도:** 반복 측정 통계 (표준편차)
        - **B형 불확도:** 교정성적서, 기기 사양, 경험 등에서 유추
        - **합성불확도 uc:** A형 + B형 합성 (불확도 전파)
        - **확장불확도 U:** 신뢰도 95% 수준 (uc × 포함인자 k, 보통 k≈2)

        MetroAI는 이 모든 과정을 자동화하므로 GUM 세부 내용을 몰라도 괜찮습니다.
        """
    )

with st.expander("✅ MetroAI 결과를 KOLAS 심사에 그대로 제출할 수 있나요?", expanded=False):
    st.markdown(
        """
        **네, 설계부터 KOLAS 심사 제출용으로 만들어졌습니다.**

        - ✓ **GUM 준거 계산:** ISO/IEC Guide 98-3 표준 수식 구현
        - ✓ **MCM 검증:** GUM Supplement 1 기반 몬테카를로 시뮬레이션
        - ✓ **KOLAS-G-002 양식:** 불확도 예산표 자동 포맷
        - ✓ **감사 추적:** 모든 입력값·계산 과정 재현 가능

        다만 기관별 세부 포맷(로고, 서명란 위치 등)은 조직에서 직접 조정이 필요할 수 있습니다.
        """
    )

with st.expander("🏭 어떤 교정 분야를 지원하나요?", expanded=False):
    st.markdown(
        """
        **현재 지원:** 길이(블록게이지), 질량(분동), 온도(온도계), 압력(압력계)
        **곧 추가:** 전기(전압/전류/저항), 시간·주파수, 습도·이슬점

        필요한 분야가 있으시면 **kyb8801@gmail.com** 으로 알려주세요. 우선순위에 반영합니다.
        """
    )

with st.expander("💳 무료 플랜의 제한사항은?", expanded=False):
    st.markdown(
        """
        **Free:** 월 3건 계산 + 모든 기능 사용 가능 (PDF/엑셀/MCM/체크리스트 포함)
        **Pro:** 무제한 계산 + 우선 지원 + 월 ₩29,900
        **Consulting:** Phase 5에서 출시 예정

        신용카드 없이 바로 시작할 수 있으며, 언제든 업/다운그레이드 가능합니다.
        """
    )

st.markdown("&nbsp;")

# ──────────────────────────────────────────
# 9. 푸터
# ──────────────────────────────────────────
st.markdown(
    """
    <div class="footer-content">
        <strong>MetroAI v0.5.0</strong> &nbsp;·&nbsp;
        ISO/IEC 17025 · GUM · KOLAS-G-002 준거<br>
        📧 <strong>kyb8801@gmail.com</strong> &nbsp;·&nbsp;
        한국 KOLAS 인정 교정·시험기관 전용<br>
        © 2026 MetroAI. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True,
)
