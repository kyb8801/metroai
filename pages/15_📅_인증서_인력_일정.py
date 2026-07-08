"""인증서 / 인력 / 일정 통합 뷰 — v0.7.0 신규 (v2 spec 블록 6).

3 tabs: 인증서 / 인력 / 일정. schedule + job-scout agents 활용.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.agents import JobScoutAgent, ScheduleAgent

st.set_page_config(
    page_title="인증서 · 인력 · 일정 — MetroAI",
    page_icon="📅",
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
    .v2-section-h {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E293B;
        margin: 1.25rem 0 0.75rem 0;
    }
    .v2-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.6rem;
    }
    .v2-card.urgent { border-left: 4px solid #EF4444; }
    .v2-card.medium { border-left: 4px solid #F59E0B; }
    .v2-card.ok { border-left: 4px solid #10B981; }
    .v2-mono {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    .v2-ai-card {
        background: rgba(6, 182, 212, 0.05);
        border-left: 3px solid #06B6D4;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #0F172A;
        margin-top: 0.5rem;
    }
    .v2-ai-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        background: #06B6D4;
        color: white;
        padding: 0.1rem 0.4rem;
        border-radius: 3px;
        margin-right: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Header
# ──────────────────────────────────────────
st.markdown(
    "<div class='v2-brand-h1'>운영 백본 · 인증서 / 인력 / 일정</div>"
    "<div class='v2-subtle'>일일 운영 도구. schedule + job-scout 에이전트가 자동 갱신.</div>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Run agents (cached)
# ──────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _run_agents():
    sched = ScheduleAgent().run({})
    job = JobScoutAgent().run({})
    return {
        "schedule": sched.payload,
        "job_scout": job.payload,
    }


data = _run_agents()
events = data["schedule"]["upcoming_events"]
ts = data["schedule"]["today"]

# Refresh
c1, _ = st.columns([1, 6])
with c1:
    if st.button("🔄 새로고침", use_container_width=True):
        _run_agents.clear()
        st.rerun()

# ──────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏷️ 인증서", "👥 인력", "📅 일정"])

# ──────────────────────────────────────────
# Tab 1 — Certificates
# ──────────────────────────────────────────
with tab1:
    # 인증서 데모 데이터 — v0.7 stub. 실배포 시 SQLite 또는 사용자 업로드.
    certs = [
        {
            "id": "2026-CL-014", "type": "교정 인증서", "issuer": "KRISS",
            "issued": "2024-07-15", "expires": "2026-07-15",
            "days_left": 60, "attached": True,
        },
        {
            "id": "RMP-001", "type": "RMP 인정", "issuer": "KOLAS",
            "issued": "2024-05-13", "expires": "2028-05-13",
            "days_left": 730, "attached": True,
        },
        {
            "id": "ISO-17034-2024", "type": "ISO 17034 인증", "issuer": "KTR",
            "issued": "2024-01-10", "expires": "2027-01-10",
            "days_left": 605, "attached": True,
        },
        {
            "id": "BG-25mm-2025", "type": "블록게이지 교정", "issuer": "KRISS",
            "issued": "2025-05-22", "expires": "2026-05-22",
            "days_left": 4, "attached": True,
        },
        {
            "id": "PT-2025-Q4", "type": "PT 참가 증서", "issuer": "ISO 17043 PT provider",
            "issued": "2025-10-30", "expires": "2026-10-30",
            "days_left": 165, "attached": False,
        },
    ]

    st.markdown(
        f"<div class='v2-subtle'>총 {len(certs)} 인증서 · "
        f"60일 내 만료 {sum(1 for c in certs if c['days_left'] <= 60)} · "
        f"첨부 PDF {sum(1 for c in certs if c['attached'])}</div>",
        unsafe_allow_html=True,
    )

    cs1, cs2 = st.columns([1, 1])
    with cs1:
        if st.button("60일 내 만료 일괄 알림", use_container_width=True):
            st.success("3건의 알림 이메일이 큐에 추가됨 (orchestrator)")
    with cs2:
        st.button("새 인증서 추가", use_container_width=True)

    # Card list
    for c in certs:
        if c["days_left"] <= 30:
            cls, label_color = "urgent", "#EF4444"
        elif c["days_left"] <= 90:
            cls, label_color = "medium", "#F59E0B"
        else:
            cls, label_color = "ok", "#10B981"

        attached = "📎 첨부됨" if c["attached"] else "⚠️ PDF 미첨부"
        st.markdown(
            f"""
            <div class='v2-card {cls}'>
              <div style='display:flex;justify-content:space-between;'>
                <div>
                  <span class='v2-mono' style='color:{label_color};font-weight:600;'>{c['id']}</span> ·
                  <span style='color:#1E293B;'>{c['type']}</span>
                  <small style='color:#475569;display:block;margin-top:0.2rem;'>
                    {c['issuer']} · 발급 {c['issued']} → 만료 {c['expires']}
                  </small>
                </div>
                <div style='text-align:right;'>
                  <span class='v2-mono' style='color:{label_color};font-weight:600;'>D-{c['days_left']}</span><br>
                  <small style='color:#475569;'>{attached}</small>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────
# Tab 2 — Personnel
# ──────────────────────────────────────────
with tab2:
    personnel = [
        {
            "name": "김용범", "role": "품질책임자",
            "kolas_cert": "KOLAS RMP 인정 자격자 · KTR ISO 17034 cert. 2024-CM-007",
            "last_training": "2025-11-08",
            "next_renewal": "2026-11-08",
            "days_to_renewal": 174,
            "turnover_signal": 0.05,  # very low
        },
        {
            "name": "이○○", "role": "기술관리자 (RMP)",
            "kolas_cert": "KAB-F-21-2026 양식 (마이그레이션 필요)",
            "last_training": "2024-09-12",
            "next_renewal": "2026-09-12",
            "days_to_renewal": 117,
            "turnover_signal": 0.18,
        },
        {
            "name": "박○○", "role": "기술관리자 (교정)",
            "kolas_cert": "KOLAS 교정 분야 자격자",
            "last_training": "2025-03-21",
            "next_renewal": "2027-03-21",
            "days_to_renewal": 672,
            "turnover_signal": 0.10,
        },
    ]

    turnover_avg = data["job_scout"].get("turnover_signal", 0.0)
    st.markdown(
        f"<div class='v2-subtle'>총 {len(personnel)} 명 · "
        f"30일 내 갱신 {sum(1 for p in personnel if p['days_to_renewal'] <= 30)} · "
        f"job-scout 회전율 추정 평균 {turnover_avg:.2f}</div>",
        unsafe_allow_html=True,
    )

    for p in personnel:
        if p["turnover_signal"] >= 0.4:
            cls, ai_text = "urgent", "⚠️ 외부 채용 공고 또는 인력 이동 신호 감지"
        elif p["turnover_signal"] >= 0.2:
            cls, ai_text = "medium", "주의 — 인력 이동 가능성 중간"
        else:
            cls, ai_text = "ok", "안정적 운영"

        days_color = "#EF4444" if p["days_to_renewal"] <= 30 else "#475569"
        st.markdown(
            f"""
            <div class='v2-card {cls}'>
              <div style='display:flex;justify-content:space-between;'>
                <div>
                  <span style='font-size:1.05rem;font-weight:600;color:#1E293B;'>{p['name']}</span>
                  <span class='v2-mono' style='color:#1E40AF;margin-left:0.5rem;'>· {p['role']}</span>
                  <small style='color:#475569;display:block;margin-top:0.3rem;'>
                    {p['kolas_cert']}
                  </small>
                </div>
                <div style='text-align:right;'>
                  <span class='v2-mono'>마지막 교육 {p['last_training']}</span><br>
                  <span class='v2-mono' style='color:{days_color};font-weight:600;'>
                    갱신까지 D-{p['days_to_renewal']}
                  </span>
                </div>
              </div>
              <div class='v2-ai-card'>
                <span class='v2-ai-badge'>AI</span>
                <span style='color:#475569;'>job-scout 신호 {p['turnover_signal']:.2f}</span> · {ai_text}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────
# Tab 3 — Schedule
# ──────────────────────────────────────────
with tab3:
    st.markdown(
        f"<div class='v2-subtle'>schedule 에이전트 자동 생성 · 향후 {data['schedule']['horizon_days']}일 · "
        f"{len(events)} 이벤트</div>",
        unsafe_allow_html=True,
    )

    # Calendar-style chronological list
    df_events = pd.DataFrame(events)
    df_events["date"] = pd.to_datetime(df_events["date"])
    df_events = df_events.sort_values("date").reset_index(drop=True)

    for _, ev in df_events.iterrows():
        urg = ev.get("urgency", "low")
        cls = {"high": "urgent", "medium": "medium", "low": "ok"}.get(urg, "ok")
        urg_color = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}.get(urg, "#475569")
        d = ev["date"].strftime("%Y-%m-%d (%a)")
        days = ev.get("days_until", "?")
        st.markdown(
            f"""
            <div class='v2-card {cls}'>
              <div style='display:flex;justify-content:space-between;'>
                <div>
                  <span class='v2-mono' style='font-size:1.0rem;color:{urg_color};font-weight:600;'>
                    {d}
                  </span>
                  <span style='color:#1E40AF;font-weight:600;margin-left:0.6rem;'>{ev['type']}</span>
                  <div style='color:#1E293B;margin-top:0.3rem;'>{ev['title']}</div>
                </div>
                <div style='text-align:right;'>
                  <span class='v2-mono' style='color:{urg_color};font-weight:600;'>D-{days}</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='margin-top:1rem;color:#475569;font-size:0.85rem;'>"
        "💡 이벤트는 schedule 에이전트가 인증서 만료일 + 정기심사 주기 + 내부 감사 빈도 + "
        "표준기 교정 cycle 기반으로 자동 생성합니다."
        "</div>",
        unsafe_allow_html=True,
    )

st.caption(
    "본 페이지는 schedule + job-scout 에이전트의 출력입니다. v0.6 데모 데이터 · "
    "실배포 시 SQLite events / 사용자 업로드 인증서 / 인력 DB 로 교체."
)
