"""6 AI Agents 대시보드 — v0.6.0 신규.

v2 spec(MetroAI_ClaudeDesign_Phase1_v2.md) 블록 2 (메인 대시보드) 기반.
6개 에이전트의 실시간 상태와 통합 작업 큐를 표시한다.

KOLAS 컴플라이언스 SaaS 의 핵심 진입 화면.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.agents import (
    JobScoutAgent,
    KolasAuditPredictorAgent,
    KolasMonitorAgent,
    OrchestratorAgent,
    ScheduleAgent,
    SemiIntelAgent,
)

# ──────────────────────────────────────────
# Page config + v2 spec styling
# ──────────────────────────────────────────
st.set_page_config(
    page_title="6 AI Agents — MetroAI",
    page_icon="🤖",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* v2 spec — KOLAS compliance brand */
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
    .v2-kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
    }
    .v2-kpi-label {
        color: #475569;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .v2-kpi-value {
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 1.85rem;
        font-weight: 600;
        color: #0F172A;
        line-height: 1;
    }
    .v2-kpi-meta {
        color: #475569;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .v2-section-h {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1E293B;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .v2-ai-card {
        background: rgba(6, 182, 212, 0.05);
        border-left: 3px solid #06B6D4;
        padding: 0.85rem 1rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        font-size: 0.95rem;
        color: #0F172A;
    }
    .v2-ai-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        background: #06B6D4;
        color: white;
        padding: 0.05rem 0.4rem;
        border-radius: 3px;
        margin-right: 0.5rem;
    }
    .v2-agent-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.5rem;
        font-family: -apple-system, 'Pretendard', 'Inter', sans-serif;
    }
    .v2-agent-name {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        color: #1E40AF;
    }
    .v2-agent-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #475569;
        margin-left: 0.5rem;
    }
    .v2-agent-output {
        font-size: 0.9rem;
        color: #0F172A;
        margin-top: 0.35rem;
        line-height: 1.4;
    }
    .v2-status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.4rem;
    }
    .dot-ok { background: #10B981; }
    .dot-stale { background: #F59E0B; }
    .dot-error { background: #EF4444; }
    .dot-disabled { background: #94A3B8; }
    .v2-task-row {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #1E40AF;
        border-radius: 6px;
        padding: 0.65rem 0.9rem;
        margin-bottom: 0.4rem;
        font-size: 0.93rem;
    }
    .v2-task-row.p0 { border-left-color: #EF4444; }
    .v2-task-row.p1 { border-left-color: #F59E0B; }
    .v2-task-row.p2 { border-left-color: #06B6D4; }
    .v2-task-priority {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.78rem;
        padding: 0.05rem 0.4rem;
        border-radius: 3px;
        margin-right: 0.5rem;
    }
    .p0-badge { background: #FEE2E2; color: #EF4444; }
    .p1-badge { background: #FEF3C7; color: #F59E0B; }
    .p2-badge { background: #E0F2FE; color: #06B6D4; }
    .v2-task-source {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #475569;
        margin-left: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Header
# ──────────────────────────────────────────
st.markdown(
    "<div class='v2-brand-h1'>6 AI Agents · 컴플라이언스 모니터링</div>"
    "<div class='v2-subtle'>v0.6.0 — 박수연 통합 백본. 6개 에이전트가 24시간 KOLAS 환경을 모니터링합니다.</div>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Run all agents (cached per session)
# ──────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def run_all() -> dict:
    """6개 에이전트 동시 실행 + orchestrator 통합."""
    semi = SemiIntelAgent().run({})
    job = JobScoutAgent().run({})
    monitor = KolasMonitorAgent().run({})
    predictor = KolasAuditPredictorAgent().run({})
    sched = ScheduleAgent().run({})

    orch = OrchestratorAgent().run({
        "agent_results": {
            "semi-intel": semi,
            "job-scout": job,
            "kolas-monitor": monitor,
            "kolas-audit-predictor": predictor,
            "schedule": sched,
        }
    })
    return {
        "semi-intel": semi,
        "job-scout": job,
        "kolas-monitor": monitor,
        "kolas-audit-predictor": predictor,
        "schedule": sched,
        "orchestrator": orch,
    }


# Refresh control
col_refresh, _ = st.columns([1, 6])
with col_refresh:
    if st.button("🔄 새로고침", use_container_width=True):
        run_all.clear()

results = run_all()

# ──────────────────────────────────────────
# Row 1 — Compliance KPI strip (v2 spec)
# ──────────────────────────────────────────
predictor_r = results["kolas-audit-predictor"]
schedule_r = results["schedule"]
orch_r = results["orchestrator"]
monitor_r = results["kolas-monitor"]

risk = predictor_r.payload.get("risk_score", 0.0) * 100
confidence = predictor_r.payload.get("confidence", 0.0) * 100
d_day = schedule_r.payload.get("next_regulatory_audit_d_day", None)
upcoming_count = len(schedule_r.payload.get("upcoming_events", []))
task_count = orch_r.payload.get("task_count", 0)
monitor_high = sum(
    1 for it in monitor_r.payload.get("feed_items", [])
    if it.get("impact_level") == "high"
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"<div class='v2-kpi-card'>"
        f"<div class='v2-kpi-label'>다음 정기심사</div>"
        f"<div class='v2-kpi-value'>D-{d_day}</div>"
        f"<div class='v2-kpi-meta'>schedule 에이전트</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with c2:
    color = "#EF4444" if risk > 40 else ("#F59E0B" if risk > 20 else "#10B981")
    st.markdown(
        f"<div class='v2-kpi-card'>"
        f"<div class='v2-kpi-label'>감사 위험 (predictor)</div>"
        f"<div class='v2-kpi-value' style='color:{color};'>{risk:.1f}%</div>"
        f"<div class='v2-kpi-meta'>신뢰도 {confidence:.0f}% · v0.6 baseline</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"<div class='v2-kpi-card'>"
        f"<div class='v2-kpi-label'>오늘의 작업</div>"
        f"<div class='v2-kpi-value'>{task_count}</div>"
        f"<div class='v2-kpi-meta'>orchestrator 통합 큐</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"<div class='v2-kpi-card'>"
        f"<div class='v2-kpi-label'>high-impact 고시 변경</div>"
        f"<div class='v2-kpi-value'>{monitor_high}</div>"
        f"<div class='v2-kpi-meta'>kolas-monitor 최근 7일</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────
# Row 2 — Audit risk detail + Today's tasks
# ──────────────────────────────────────────
left, right = st.columns([2, 1])

with left:
    st.markdown("<div class='v2-section-h'>감사 위험 기여 요인</div>", unsafe_allow_html=True)
    contributors = predictor_r.payload.get("contributors", [])
    if contributors:
        import pandas as pd

        df = pd.DataFrame(contributors)
        df = df.rename(columns={
            "factor": "기여 요인",
            "contribution_pct": "기여도 (pp)",
            "direction": "방향",
        })
        df["기여도 (pp)"] = df["기여도 (pp)"].round(2)
        st.dataframe(df, use_container_width=True, hide_index=True)

    reasoning = predictor_r.payload.get("reasoning", "")
    if reasoning:
        st.markdown(
            f"<div class='v2-ai-card'>"
            f"<span class='v2-ai-badge'>AI</span>"
            f"{reasoning}"
            f"</div>",
            unsafe_allow_html=True,
        )

with right:
    st.markdown("<div class='v2-section-h'>오늘의 작업</div>", unsafe_allow_html=True)
    for task in orch_r.payload.get("tasks", []):
        prio = task["priority"]
        prio_class = prio.lower()
        title = task["title"]
        source = task["source_agent"]
        impact = task.get("expected_impact", "")
        due = task.get("due_date") or f"~{task.get('due_in_days','?')}일 내"
        st.markdown(
            f"<div class='v2-task-row {prio_class}'>"
            f"<span class='v2-task-priority {prio_class}-badge'>{prio}</span>"
            f"{title}"
            f"<span class='v2-task-source'>· {source} · {due}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────
# Row 3 — KOLAS feed + Upcoming events
# ──────────────────────────────────────────
fcol, ecol = st.columns(2)

with fcol:
    st.markdown("<div class='v2-section-h'>최근 KOLAS 고시 변경 (kolas-monitor)</div>", unsafe_allow_html=True)
    for item in monitor_r.payload.get("feed_items", []):
        level = item.get("impact_level", "low")
        color = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}[level]
        affected = ", ".join(item.get("affected_sops", [])) or "—"
        st.markdown(
            f"<div class='v2-ai-card'>"
            f"<span class='v2-ai-badge'>AI</span>"
            f"<strong>{item['date']} · {item['source']}</strong> "
            f"<span style='color:{color};font-weight:600;'>[{level}]</span><br>"
            f"<span style='color:#0F172A;font-weight:500;'>{item['title']}</span><br>"
            f"<span style='font-size:0.85rem;color:#475569;'>영향 SOP: {affected}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

with ecol:
    st.markdown("<div class='v2-section-h'>향후 일정 (schedule)</div>", unsafe_allow_html=True)
    for ev in schedule_r.payload.get("upcoming_events", []):
        urg = ev.get("urgency", "low")
        color = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}[urg]
        st.markdown(
            f"<div class='v2-task-row'>"
            f"<strong>{ev['date']}</strong> "
            f"<span style='color:{color};font-weight:600;'>· {ev['type']}</span><br>"
            f"<span style='color:#0F172A;'>{ev['title']}</span>"
            f"<span class='v2-task-source'>· D-{ev['days_until']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────
# Bottom — Agent activity strip (6 cards)
# ──────────────────────────────────────────
st.markdown("<div class='v2-section-h'>에이전트 활동 (6 strip)</div>", unsafe_allow_html=True)

agent_order = [
    "semi-intel", "job-scout", "kolas-monitor",
    "kolas-audit-predictor", "orchestrator", "schedule",
]
cols = st.columns(6)
for col, name in zip(cols, agent_order):
    r = results[name]
    status = r.status.value
    ai_badge = "<span class='v2-ai-badge'>AI</span>" if r.powered_by_ai else ""
    with col:
        st.markdown(
            f"<div class='v2-agent-card'>"
            f"<span class='v2-status-dot dot-{status}'></span>"
            f"<span class='v2-agent-name'>{name}</span>"
            f"<span class='v2-agent-meta'>· {r.timestamp.strftime('%H:%M')}</span>"
            f"<div class='v2-agent-output'>{ai_badge}{r.latest_output}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────
# Footer
# ──────────────────────────────────────────
st.markdown("---")
st.caption(
    f"v0.6.0 baseline · 마지막 새로고침: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}. "
    f"본 페이지는 v2 design spec(Phase 1) 기반으로 구현되었습니다. "
    f"AI 출력은 cyan 라벨로 표시됩니다. 최종 판단은 품질책임자가 수행해야 합니다."
)
