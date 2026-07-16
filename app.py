"""MetroAI — v2 spec 랜딩 페이지 (v0.8.0).

v2 design Phase 1 블록 1 (마케팅 랜딩 페이지) Streamlit 구현.
KOLAS 컴플라이언스 SaaS positioning, 6 AI agents, KOLAS-실무자 톤.

5/19 swap 완료 — 이전 v0.5 랜딩은 app_v0_5_backup.py 에 보존됨.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.agents import all_agents

st.set_page_config(
    page_title="MetroAI — KOLAS Compliance OS",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# v2 design tokens
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

    html, body, [class*="css"] {
        font-family: 'Pretendard', 'Inter', -apple-system, sans-serif !important;
    }
    .stApp {
        background: #FFFFFF;
    }
    .block-container {
        max-width: 1180px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    /* Hero */
    .v2-hero {
        padding: 4rem 2rem 3.5rem 2rem;
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .v2-hero h1 {
        font-size: 3rem;
        font-weight: 600;
        line-height: 1.15;
        color: #0F172A;
        letter-spacing: -0.025em;
        margin: 0 0 1rem 0;
    }
    .v2-hero p.subhead {
        font-size: 1.15rem;
        color: #475569;
        line-height: 1.6;
        max-width: 720px;
        margin: 0 0 2rem 0;
    }

    /* CTAs */
    .v2-cta-primary {
        display: inline-block;
        background: #1E40AF;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        text-decoration: none;
        margin-right: 0.75rem;
        border: 1px solid #1E40AF;
    }
    .v2-cta-primary:hover { background: #1E3A8A; }
    .v2-cta-ghost {
        display: inline-block;
        background: transparent;
        color: #1E40AF;
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        text-decoration: none;
        border: 1px solid #E2E8F0;
    }
    .v2-cta-ghost:hover { background: #F8FAFC; }

    /* Credibility row */
    .v2-cred-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 2.5rem 0;
    }
    .v2-cred-card {
        padding: 1rem 1.25rem;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
    }
    .v2-cred-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }
    .v2-cred-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        color: #1E40AF;
        font-weight: 600;
    }

    /* Section heading */
    .v2-section {
        font-size: 1.75rem;
        font-weight: 600;
        color: #0F172A;
        letter-spacing: -0.015em;
        margin: 3rem 0 1.5rem 0;
    }
    .v2-section-sub {
        color: #475569;
        font-size: 0.95rem;
        margin: -1rem 0 1.5rem 0;
    }

    /* Feature cards */
    .v2-feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
    .v2-feature {
        padding: 1.5rem;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
    }
    .v2-feature h3 {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E293B;
        margin: 0 0 0.5rem 0;
    }
    .v2-feature p {
        color: #475569;
        font-size: 0.92rem;
        line-height: 1.55;
        margin: 0;
    }

    /* Agent card */
    .v2-agent-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.85rem;
    }
    .v2-agent-card {
        padding: 1.1rem;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
    }
    .v2-agent-name {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        color: #1E40AF;
        margin-bottom: 0.35rem;
    }
    .v2-agent-desc {
        font-size: 0.88rem;
        color: #475569;
        line-height: 1.45;
    }
    .v2-agent-ai {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        background: #06B6D4;
        color: white;
        padding: 0.1rem 0.4rem;
        border-radius: 3px;
        margin-left: 0.4rem;
    }

    /* Pricing */
    .v2-pricing-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
    .v2-tier {
        padding: 1.5rem;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        text-align: center;
    }
    .v2-tier.featured {
        border: 2px solid #1E40AF;
    }
    .v2-tier-name {
        font-size: 1rem;
        font-weight: 600;
        color: #1E40AF;
        margin-bottom: 0.4rem;
    }
    .v2-tier-price {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0.5rem 0;
    }
    .v2-tier-desc {
        color: #475569;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }

    /* Founder note */
    .v2-founder {
        background: #F8FAFC;
        border-left: 3px solid #1E40AF;
        padding: 1.5rem;
        border-radius: 6px;
        font-family: 'Georgia', serif;
        color: #1E293B;
        margin: 3rem 0 2rem 0;
    }
    .v2-founder cite {
        display: block;
        font-family: 'Pretendard', sans-serif;
        font-style: normal;
        color: #475569;
        font-size: 0.85rem;
        margin-top: 0.75rem;
    }

    /* Footer */
    .v2-footer {
        border-top: 1px solid #E2E8F0;
        padding-top: 1.5rem;
        margin-top: 3rem;
        color: #475569;
        font-size: 0.85rem;
    }

    /* Hide default Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Hero
# ──────────────────────────────────────────────
st.markdown(
    """
    <div class='v2-hero'>
      <h1>KOLAS 감사를 데이터로 관리합니다.</h1>
      <p class='subhead'>
        1,200개 KOLAS 인정 기관이 여전히 엑셀과 이메일로 운영합니다.
        MetroAI는 SOP·감사 이력·인증서·인력을 하나로 묶고,
        AI 에이전트 6종으로 부적합을 사전에 잡습니다.
      </p>
      <a href='?page=dashboard' class='v2-cta-primary'>6 AI Agents 대시보드 열기 →</a>
      <a href='https://github.com/kyb8801/metroai' class='v2-cta-ghost' target='_blank'>GitHub 보기</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Domain selector (v0.7.0 P0-1 — 분야별 진입 wizard)
# ──────────────────────────────────────────────
st.markdown(
    "<h2 class='v2-section'>어떤 장비로 KOLAS 인정을 받으세요?</h2>"
    "<p class='v2-section-sub'>분야를 선택하면 해당 분야 전용 가이드 · KOLAS 절차 · "
    "측정 불확도 템플릿 · SOP 갭 점검표가 한 화면에 모입니다.</p>",
    unsafe_allow_html=True,
)

from metroai.content import list_domains  # noqa: E402

domain_cards_html = "<div class='v2-feature-grid'>"
domain_page_map = {
    "sem": "16_🔬_SEM_분야",
    "tem": "17_⚛️_TEM_분야",
    "afm": "18_📐_AFM_분야",
    "ocd": "19_📏_OCD_분야",
    "general": "1_📐_불확도_계산",
}
for g in list_domains():
    page_slug = domain_page_map.get(g.key, "1_📐_불확도_계산")
    domain_cards_html += (
        f"<div class='v2-feature' style='cursor:pointer;'>"
        f"<h3>{g.icon} {g.label_ko}</h3>"
        f"<p style='font-size:0.88rem;color:#1E293B;margin-bottom:0.5rem;'>{g.one_liner}</p>"
        f"<p style='font-size:0.75rem;color:#475569;'>대표 표준: "
        f"{', '.join([s['code'].split(':')[0] for s in g.iso_standards[:3]])}</p>"
        f"<p style='margin-top:0.6rem;font-family:JetBrains Mono,monospace;"
        f"font-size:0.78rem;color:#06B6D4;'>→ 사이드바에서 \"{page_slug.replace('_', ' ')}\" 페이지</p>"
        f"</div>"
    )
domain_cards_html += "</div>"
st.markdown(domain_cards_html, unsafe_allow_html=True)

st.caption(
    "💡 분야를 클릭한 적이 없어도, 사이드바의 각 분야 페이지로 직접 진입할 수 있습니다. "
    "분야별 가이드는 ISO 표준 + KOLAS 공개 문서 기반 generic 콘텐츠입니다."
)

# ──────────────────────────────────────────────
# Credibility row
# ──────────────────────────────────────────────
st.markdown(
    """
    <div class='v2-cred-row'>
      <div class='v2-cred-card'>
        <div class='v2-cred-label'>현재 상태</div>
        <div class='v2-cred-value'>v0.8.0 · 운영 중</div>
      </div>
      <div class='v2-cred-card'>
        <div class='v2-cred-label'>kolas-audit-predictor</div>
        <div class='v2-cred-value'>baseline · 실데이터 검증 진행 중</div>
      </div>
      <div class='v2-cred-card'>
        <div class='v2-cred-label'>표준</div>
        <div class='v2-cred-value'>ISO/IEC 17025 · 17034 native</div>
      </div>
    </div>
    <p style='color:#475569;font-size:0.85rem;margin-top:-1rem;'>
      본 서비스는 KOLAS 인정 기관 실무자에 의해 설계되었습니다 ·
      Youngbum Kim · KOLAS-accredited ISO 17034 RM-producer practitioner
    </p>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# What MetroAI does
# ──────────────────────────────────────────────
st.markdown("<h2 class='v2-section'>MetroAI 가 하는 것</h2>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='v2-feature-grid'>
      <div class='v2-feature'>
        <h3>감사 위험 예측</h3>
        <p>
          kolas-audit-predictor 에이전트가 SOP 완성도·인력 회전율·이전 감사 결과로
          다음 정기심사 부적합 위험을 예측합니다. (v0.6 baseline, 실데이터 검증 진행 중)
        </p>
      </div>
      <div class='v2-feature'>
        <h3>SOP / 인증서 통합 관리</h3>
        <p>
          흩어진 SOP·교정 인증서·시험 보고서를 한 화면에서.
          만료 30 / 60 / 90일 알림 자동.
        </p>
      </div>
      <div class='v2-feature'>
        <h3>KOLAS 고시 자동 모니터링</h3>
        <p>
          kolas-monitor 에이전트가 KOLAS · KAB · KTR 고시 변경을 일 단위 스캔.
          영향 받는 SOP 를 자동 식별.
        </p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Six AI agents
# ──────────────────────────────────────────────
st.markdown(
    "<h2 class='v2-section'>6 AI agents 가 24시간 모니터링합니다</h2>"
    "<p class='v2-section-sub'>각 에이전트의 출력에 <code>is_live</code> / <code>data_origin</code> 플래그가 동반됩니다 (live · stub · synthetic).</p>",
    unsafe_allow_html=True,
)

agents = all_agents()
agent_cards_html = "<div class='v2-agent-grid'>"
for a in agents:
    ai_badge = "<span class='v2-agent-ai'>AI</span>" if a.powered_by_ai else ""
    agent_cards_html += (
        f"<div class='v2-agent-card'>"
        f"<div class='v2-agent-name'>{a.name}{ai_badge}</div>"
        f"<div class='v2-agent-desc'>{a.description}</div>"
        f"</div>"
    )
agent_cards_html += "</div>"
st.markdown(agent_cards_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Workflow sections
# ──────────────────────────────────────────────
st.markdown("<h2 class='v2-section'>워크플로우</h2>", unsafe_allow_html=True)

st.markdown(
    """
    <div class='v2-feature' style='margin-bottom:1rem;'>
      <h3>SOP를 데이터로</h3>
      <p>MetroAI 가 기존 SOP (PDF / HWP) 를 indexing 합니다. 변경 이력·검토 주기·작성자
      매핑 자동. 부적합 패턴 매칭으로 다음 검토 우선순위 추천.</p>
    </div>
    <div class='v2-feature' style='margin-bottom:1rem;'>
      <h3>감사 전 30일 자동 점검</h3>
      <p>정기심사 30일 전 알림. AI 가 작년 부적합 패턴 기반 체크리스트를 생성하고,
      orchestrator 가 P0 / P1 / P2 작업 큐로 정렬합니다.</p>
    </div>
    <div class='v2-feature' style='margin-bottom:1rem;'>
      <h3>한국 1,200개 기관 데이터로 학습</h3>
      <p>예측 모델은 KOLAS 공개 부적합 데이터 + 동의 기관 감사 이력으로 학습.
      현재 합성 데이터 baseline 운영 중, 실데이터 학습 진행 중 (v0.7).</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Pricing
# ──────────────────────────────────────────────
st.markdown("<h2 class='v2-section'>가격</h2>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='v2-pricing-grid'>
      <div class='v2-tier'>
        <div class='v2-tier-name'>Lite</div>
        <div class='v2-tier-price'>₩100,000 / 월</div>
        <div class='v2-tier-desc'>측정 방법 10개 미만 소규모 기관</div>
      </div>
      <div class='v2-tier featured'>
        <div class='v2-tier-name'>Standard <span style='font-size:0.7rem;color:#06B6D4;'>(권장)</span></div>
        <div class='v2-tier-price'>₩300,000 / 월</div>
        <div class='v2-tier-desc'>일반 인정 기관 · 6 AI agents 풀 액세스</div>
      </div>
      <div class='v2-tier'>
        <div class='v2-tier-name'>Enterprise</div>
        <div class='v2-tier-price'>문의</div>
        <div class='v2-tier-desc'>다중 사이트 · 커스텀 통합 · 데이터 동의 협력</div>
      </div>
    </div>
    <p style='color:#475569;font-size:0.85rem;text-align:center;margin-top:1rem;'>
      v0.8.0 단계 — 현재 모든 기능 무료 evaluation.
    </p>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Founder note
# ──────────────────────────────────────────────
st.markdown(
    """
    <div class='v2-founder'>
      "저는 KOLAS 인정 표준물질생산기관에서 정기심사를 직접 운영했고, 부적합 0건으로
      통과시켰습니다. 그 과정의 모든 작업이 엑셀과 이메일에 흩어져 있었습니다.
      MetroAI 는 제가 그 시절에 절실히 필요했던 도구입니다."
      <cite>— 김용범, Ph.D. · KOLAS 인정 표준물질생산기관(ISO 17034) 실무</cite>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown(
    f"""
    <div class='v2-footer'>
      MetroAI v0.8.0 · © 2026 Youngbum Kim · MIT License<br>
      <a href='https://github.com/kyb8801/metroai' style='color:#1E40AF;text-decoration:none;'>GitHub</a> ·
      <a href='https://mcpize.com/mcp/measurement-uncertainty' style='color:#1E40AF;text-decoration:none;'>MCPize</a> ·
      <a href='https://glama.ai/mcp/servers?query=metroai' style='color:#1E40AF;text-decoration:none;'>Glama</a><br>
      <small style='color:#94A3B8;'>Generated {datetime.utcnow().strftime("%Y-%m-%d")} · v2 design Phase 1 block 1 + P0-1 wizard</small>
    </div>
    """,
    unsafe_allow_html=True,
)
