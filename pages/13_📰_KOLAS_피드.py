"""KOLAS 모니터링 피드 — v0.7.0 신규 (v2 spec 블록 5).

kolas-monitor 에이전트의 출력을 Bloomberg-Terminal × Stripe-Press 톤으로 표시.
규제 변경 자동 수집 + 영향 SOP 식별 + 조치 기한 안내.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.agents import KolasMonitorAgent

st.set_page_config(
    page_title="KOLAS 피드 — MetroAI",
    page_icon="📰",
    layout="wide",
)

st.markdown(
    """
    <style>
    .v2-brand-h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: #1E40AF;
        margin-bottom: 0.25rem;
        letter-spacing: -0.01em;
    }
    .v2-subtle {
        color: #475569;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .v2-feed-item {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.85rem;
        font-family: 'Pretendard', 'Inter', sans-serif;
    }
    .v2-feed-meta {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .v2-feed-date {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.05rem;
        font-weight: 600;
        color: #1E40AF;
    }
    .v2-feed-source {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        background: #1E40AF;
        color: white;
        padding: 0.15rem 0.5rem;
        border-radius: 3px;
        letter-spacing: 0.03em;
    }
    .v2-feed-source.kab { background: #06B6D4; }
    .v2-feed-source.ktr { background: #475569; }
    .v2-feed-source.industry { background: #F59E0B; color: #1E293B; }
    .v2-feed-impact {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        padding: 0.1rem 0.5rem;
        border-radius: 3px;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .v2-feed-impact.high { background: #FEE2E2; color: #EF4444; }
    .v2-feed-impact.medium { background: #FEF3C7; color: #F59E0B; }
    .v2-feed-impact.low { background: #E0F2FE; color: #06B6D4; }
    .v2-feed-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    .v2-feed-summary {
        color: #475569;
        font-size: 0.92rem;
        line-height: 1.6;
        margin-bottom: 0.85rem;
    }
    .v2-feed-ai {
        background: rgba(6, 182, 212, 0.06);
        border-left: 3px solid #06B6D4;
        padding: 0.85rem 1rem;
        border-radius: 6px;
        margin: 0.85rem 0;
        color: #0F172A;
        font-size: 0.9rem;
    }
    .v2-feed-ai-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        background: #06B6D4;
        color: white;
        padding: 0.1rem 0.4rem;
        border-radius: 3px;
        margin-right: 0.5rem;
        vertical-align: middle;
    }
    .v2-feed-actions {
        display: flex;
        gap: 0.75rem;
        margin-top: 0.85rem;
    }
    .v2-feed-link {
        font-size: 0.85rem;
        color: #1E40AF;
        text-decoration: none;
        font-weight: 500;
        padding: 0.4rem 0.85rem;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
    }
    .v2-feed-link.primary {
        background: #1E40AF;
        color: white;
        border-color: #1E40AF;
    }
    .v2-section-h {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E293B;
        margin: 1.25rem 0 0.75rem 0;
    }
    .v2-filter-pill {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 999px;
        font-size: 0.78rem;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        color: #475569;
    }
    .v2-filter-pill.active { background: #1E40AF; color: white; border-color: #1E40AF; }
    .v2-data-flag {
        display: inline-block;
        font-size: 0.7rem;
        padding: 0.15rem 0.5rem;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        margin-left: 0.5rem;
    }
    .v2-data-flag.live { background: #DCFCE7; color: #166534; }
    .v2-data-flag.stub { background: #FEF3C7; color: #B45309; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Header
# ──────────────────────────────────────────
st.markdown(
    "<div class='v2-brand-h1'>KOLAS 모니터링 피드</div>"
    "<div class='v2-subtle'>kolas-monitor 에이전트가 KOLAS · KAB · KTR 고시를 자동 수집합니다. "
    "영향 받는 SOP 식별 + 조치 기한 자동 분석.</div>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Run agent (cached)
# ──────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _run_monitor() -> dict:
    """kolas-monitor 에이전트 실행 → live/stub 자동 fallback."""
    r = KolasMonitorAgent().run({})
    return {
        "feed_items": r.payload.get("feed_items", []),
        "is_live": r.payload.get("is_live", False),
        "data_source": r.payload.get("data_source", "unknown"),
        "fallback_reason": r.payload.get("fallback_reason"),
        "warning": r.payload.get("warning"),
        "timestamp": r.timestamp.isoformat(),
    }


data = _run_monitor()

# Refresh + status row
c1, c2, c3 = st.columns([1.5, 4, 1])
with c1:
    if st.button("🔄 새로고침", use_container_width=True):
        _run_monitor.clear()
        st.rerun()
with c2:
    flag_cls = "live" if data["is_live"] else "stub"
    flag_text = "🟢 live · knab.go.kr" if data["is_live"] else f"🟡 stub fallback ({data.get('fallback_reason','unknown')})"
    st.markdown(
        f"<span class='v2-data-flag {flag_cls}'>{flag_text}</span> "
        f"<span style='color:#475569;font-size:0.85rem;'>마지막 갱신: {data['timestamp'][:19].replace('T', ' ')} UTC</span>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"<div style='text-align:right;color:#475569;font-size:0.85rem;'>피드 {len(data['feed_items'])}건</div>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────
# Filters (sidebar)
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 필터")
    src_filter = st.multiselect(
        "출처",
        options=["KOLAS", "KAB", "KTR", "산업부", "기타"],
        default=[],
    )
    impact_filter = st.selectbox(
        "영향도",
        options=["전체", "high 만", "medium 이상", "low 이상"],
        index=0,
    )
    st.markdown("---")
    st.markdown("### 즐겨찾는 검색")
    st.markdown(
        """
        <div class='v2-filter-pill active'>RMP 관련</div>
        <div class='v2-filter-pill'>내 인정범위</div>
        <div class='v2-filter-pill'>측정불확도</div>
        <div class='v2-filter-pill'>인력 자격</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### 주간 다이제스트")
    st.text_input("이메일 (선택)", placeholder="kyb8801@gmail.com")
    st.button("주간 알림 구독", use_container_width=True)

# ──────────────────────────────────────────
# Feed
# ──────────────────────────────────────────
def _filter(item: dict) -> bool:
    if src_filter and item.get("source", "기타") not in src_filter:
        return False
    impact = item.get("impact_level", "low")
    if impact_filter == "high 만" and impact != "high":
        return False
    if impact_filter == "medium 이상" and impact not in ("medium", "high"):
        return False
    if impact_filter == "low 이상":  # all
        pass
    return True


filtered = [it for it in data["feed_items"] if _filter(it)]

if not filtered:
    st.info("필터에 일치하는 항목이 없습니다.")
else:
    for item in filtered:
        source = item.get("source", "기타")
        source_cls = source.lower() if source in ("KAB", "KTR") else ("kab" if source == "KAB" else "")
        impact = item.get("impact_level", "low")
        impact_cls = impact if impact in ("high", "medium", "low") else "low"
        affected = ", ".join(item.get("affected_sops", [])) or "— (영향 SOP 미식별)"
        action_by = item.get("recommended_action_by", "—")
        scope = ", ".join(item.get("affected_scope", [])) or "—"

        impact_label = {"high": "high impact", "medium": "medium impact", "low": "low impact"}.get(impact, impact)

        st.markdown(
            f"""
            <div class='v2-feed-item'>
              <div class='v2-feed-meta'>
                <div class='v2-feed-date'>{item.get('date', '-')}</div>
                <div class='v2-feed-source'>{source}</div>
                <div class='v2-feed-impact {impact_cls}'>{impact_label}</div>
              </div>
              <div class='v2-feed-title'>{item.get('title', '(제목 미상)')}</div>
              <div class='v2-feed-summary'>{item.get('summary', '')}</div>
              <div class='v2-feed-ai'>
                <span class='v2-feed-ai-badge'>AI</span>
                <strong>영향 분석</strong> ·
                영향 SOP: <code>{affected}</code> ·
                인정범위: <code>{scope}</code> ·
                권장 조치 기한: <code>{action_by}</code>
              </div>
              <div class='v2-feed-actions'>
                <a href='{item.get('url') or '#'}' class='v2-feed-link' target='_blank'>원문 열기 ↗</a>
                <a href='/SOP_갭_분석' class='v2-feed-link primary'>내 SOP 에 적용하기 →</a>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────
# Footer note
# ──────────────────────────────────────────
st.markdown(
    f"""
    <div style='border-top:1px solid #E2E8F0;padding-top:1rem;margin-top:2rem;
                color:#475569;font-size:0.85rem;'>
    이 페이지는 <code>kolas-monitor</code> 에이전트의 출력입니다.
    데이터 origin: <span class='v2-data-flag {"live" if data["is_live"] else "stub"}'>
    {"live" if data["is_live"] else "stub"}</span>
    {'· ' + data['warning'] if data.get('warning') else ''}
    <br>
    AI 출력은 cyan 라벨로 표시됩니다. 최종 판단은 품질책임자가 수행해야 합니다.
    </div>
    """,
    unsafe_allow_html=True,
)
