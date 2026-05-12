"""SOP 갭 분석 — v0.6.0 신규 (v2 spec 블록 4).

기술관리자 작업 화면. kolas-monitor 가 식별한 SOP 갭을 한 화면에서
스캔하고, AI 권장 변경사항을 받아 작업으로 추가한다.

데이터 소스 (v0.6.0):
  - SOP 메타데이터 — 데모 데이터셋 (실제는 SQLite 또는 사용자 업로드)
  - kolas-monitor agent.run() 출력 — affected_sops 매핑
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.agents import KolasMonitorAgent

# ──────────────────────────────────────────
# Page config + v2 spec styling
# ──────────────────────────────────────────
st.set_page_config(
    page_title="SOP 갭 분석 — MetroAI",
    page_icon="📋",
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
        font-size: 1.05rem;
        font-weight: 600;
        color: #1E293B;
        margin-top: 1.25rem;
        margin-bottom: 0.5rem;
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
    .v2-mono { font-family: 'JetBrains Mono', monospace; }
    .v2-completeness-bar-wrap {
        display: inline-block;
        width: 100%;
        height: 8px;
        background: #E2E8F0;
        border-radius: 4px;
        overflow: hidden;
        vertical-align: middle;
    }
    .v2-completeness-bar {
        height: 100%;
        background: linear-gradient(90deg, #10B981 0%, #1E40AF 100%);
    }
    .v2-side-panel {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem;
        margin-top: 0.5rem;
    }
    .v2-chip {
        display: inline-block;
        font-size: 0.78rem;
        background: #E2E8F0;
        color: #1E293B;
        padding: 0.1rem 0.5rem;
        border-radius: 999px;
        margin-right: 0.3rem;
    }
    .v2-chip.cyan { background: #E0F2FE; color: #0E7490; }
    .v2-chip.amber { background: #FEF3C7; color: #B45309; }
    .v2-chip.red { background: #FEE2E2; color: #B91C1C; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Header
# ──────────────────────────────────────────
st.markdown(
    "<div class='v2-brand-h1'>SOP 갭 분석 · 기술관리자 작업 화면</div>"
    "<div class='v2-subtle'>kolas-monitor 가 식별한 갭 + 영향 받는 SOP 매트릭스. "
    "한 화면에서 검토 우선순위를 결정합니다.</div>",
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────
# Demo SOP dataset (v0.6.0 — 추후 SQLite/사용자 업로드 교체)
# ──────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_sop_dataset() -> list[dict]:
    """v0.6.0 데모 SOP 데이터셋 — 8개 SOP."""
    today = datetime.utcnow()
    return [
        {
            "id": "M-04-2024", "title": "AFM 표면 거칠기 측정 절차 (Sa·Sq)",
            "category": "측정",
            "last_review": today - timedelta(days=420),
            "next_review": today + timedelta(days=14),
            "completeness": 78,
            "scope": ["RMP", "교정"],
            "ai_gap": "KAB-S-15 개정 영향",
        },
        {
            "id": "M-07-2024", "title": "SEM-EDS 원소 정량 분석 절차 (ZAF)",
            "category": "측정",
            "last_review": today - timedelta(days=290),
            "next_review": today + timedelta(days=80),
            "completeness": 85,
            "scope": ["RMP"],
            "ai_gap": "KAB-S-15 개정 영향",
        },
        {
            "id": "M-12-2024", "title": "TEM 격자상수 측정 절차",
            "category": "측정",
            "last_review": today - timedelta(days=110),
            "next_review": today + timedelta(days=230),
            "completeness": 92,
            "scope": ["RMP"],
            "ai_gap": None,
        },
        {
            "id": "C-03-2024", "title": "블록게이지 비교 교정 절차",
            "category": "교정",
            "last_review": today - timedelta(days=180),
            "next_review": today + timedelta(days=180),
            "completeness": 88,
            "scope": ["교정"],
            "ai_gap": None,
        },
        {
            "id": "C-08-2024", "title": "온도 보정 절차 (PRT)",
            "category": "교정",
            "last_review": today - timedelta(days=395),
            "next_review": today + timedelta(days=-25),
            "completeness": 65,
            "scope": ["교정"],
            "ai_gap": "검토 만료 지났음",
        },
        {
            "id": "S-01-2024", "title": "시료 전처리 표준 절차",
            "category": "시료준비",
            "last_review": today - timedelta(days=210),
            "next_review": today + timedelta(days=150),
            "completeness": 82,
            "scope": ["RMP", "교정", "시험"],
            "ai_gap": None,
        },
        {
            "id": "R-02-2024", "title": "교정성적서 발급 절차",
            "category": "보고",
            "last_review": today - timedelta(days=95),
            "next_review": today + timedelta(days=270),
            "completeness": 95,
            "scope": ["교정"],
            "ai_gap": None,
        },
        {
            "id": "R-05-2024", "title": "시험 보고서 검토 절차",
            "category": "보고",
            "last_review": today - timedelta(days=340),
            "next_review": today + timedelta(days=25),
            "completeness": 70,
            "scope": ["시험"],
            "ai_gap": "KAB-F-21 양식 마이그레이션 필요",
        },
    ]


sops = load_sop_dataset()
monitor_r = KolasMonitorAgent().run({})
monitor_feed = {it["title"]: it for it in monitor_r.payload.get("feed_items", [])}

# ──────────────────────────────────────────
# Filter bar
# ──────────────────────────────────────────
f1, f2, f3, f4, f5 = st.columns([1.5, 1.2, 1.2, 1.2, 1])

with f1:
    scope_filter = st.multiselect(
        "인정 범위",
        options=["RMP", "교정", "시험"],
        default=[],
    )
with f2:
    cat_filter = st.multiselect(
        "카테고리",
        options=["측정", "교정", "시료준비", "보고"],
        default=[],
    )
with f3:
    urgency_filter = st.selectbox(
        "검토 임박도",
        options=["전체", "만료 / 30일 이내", "60일 이내", "여유"],
        index=0,
    )
with f4:
    ai_gap_filter = st.selectbox(
        "AI 갭 표시",
        options=["전체", "갭 있음만", "갭 없음만"],
        index=0,
    )
with f5:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 새로고침", use_container_width=True):
        load_sop_dataset.clear()


# Apply filters
def _filter(sop: dict) -> bool:
    if scope_filter and not (set(sop["scope"]) & set(scope_filter)):
        return False
    if cat_filter and sop["category"] not in cat_filter:
        return False
    days_to = (sop["next_review"] - datetime.utcnow()).days
    if urgency_filter == "만료 / 30일 이내" and days_to > 30:
        return False
    if urgency_filter == "60일 이내" and days_to > 60:
        return False
    if urgency_filter == "여유" and days_to <= 60:
        return False
    if ai_gap_filter == "갭 있음만" and not sop["ai_gap"]:
        return False
    if ai_gap_filter == "갭 없음만" and sop["ai_gap"]:
        return False
    return True


filtered = [s for s in sops if _filter(s)]

# ──────────────────────────────────────────
# Summary line
# ──────────────────────────────────────────
total = len(sops)
shown = len(filtered)
gap_count = sum(1 for s in filtered if s["ai_gap"])
overdue = sum(
    1 for s in filtered
    if (s["next_review"] - datetime.utcnow()).days < 0
)
st.markdown(
    f"<div class='v2-subtle'>"
    f"{shown}/{total} SOP 표시 · "
    f"<span style='color:#06B6D4;font-weight:600;'>AI 갭 {gap_count}건</span> · "
    f"<span style='color:#EF4444;font-weight:600;'>검토 만료 {overdue}건</span>"
    f"</div>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────
# Main table + Side panel
# ──────────────────────────────────────────
table_col, detail_col = st.columns([2, 1])

# Session-state row selection
if "sop_selected_id" not in st.session_state:
    st.session_state.sop_selected_id = filtered[0]["id"] if filtered else None

with table_col:
    st.markdown("<div class='v2-section-h'>SOP 매트릭스</div>", unsafe_allow_html=True)
    # Render as Streamlit native table with selection
    import pandas as pd

    rows = []
    for s in filtered:
        days_to = (s["next_review"] - datetime.utcnow()).days
        if days_to < 0:
            urg = f"⚠️ 만료 {abs(days_to)}일 경과"
        elif days_to <= 30:
            urg = f"🔴 D-{days_to}"
        elif days_to <= 60:
            urg = f"🟡 D-{days_to}"
        else:
            urg = f"🟢 D-{days_to}"

        rows.append({
            "ID": s["id"],
            "제목": s["title"][:35] + ("…" if len(s["title"]) > 35 else ""),
            "카테고리": s["category"],
            "마지막 검토": s["last_review"].strftime("%Y-%m-%d"),
            "다음 검토": urg,
            "완성도": f"{s['completeness']}/100",
            "AI 갭": "🟦 " + s["ai_gap"] if s["ai_gap"] else "—",
        })

    df = pd.DataFrame(rows)
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Update selection from dataframe event
    if event and event.selection and event.selection.rows:
        idx = event.selection.rows[0]
        st.session_state.sop_selected_id = filtered[idx]["id"]


# Detail panel
sel_id = st.session_state.sop_selected_id
selected = next((s for s in sops if s["id"] == sel_id), None)

with detail_col:
    st.markdown("<div class='v2-section-h'>SOP 상세</div>", unsafe_allow_html=True)
    if not selected:
        st.info("좌측 표에서 SOP 를 선택하면 상세 정보가 표시됩니다.")
    else:
        days_to = (selected["next_review"] - datetime.utcnow()).days
        scope_chips = " ".join(
            f"<span class='v2-chip'>{sc}</span>" for sc in selected["scope"]
        )
        st.markdown(
            f"<div class='v2-side-panel'>"
            f"<div class='v2-mono' style='color:#1E40AF;font-weight:600;'>{selected['id']}</div>"
            f"<div style='font-size:1.05rem;font-weight:600;margin:0.4rem 0;'>{selected['title']}</div>"
            f"<div style='color:#475569;font-size:0.85rem;'>{selected['category']} · {scope_chips}</div>"
            f"<hr style='margin:0.8rem 0;border-color:#E2E8F0;'>"
            f"<div style='display:flex;justify-content:space-between;'>"
            f"  <div><div style='color:#475569;font-size:0.75rem;'>마지막 검토</div>"
            f"       <div class='v2-mono'>{selected['last_review'].strftime('%Y-%m-%d')}</div></div>"
            f"  <div><div style='color:#475569;font-size:0.75rem;'>다음 검토</div>"
            f"       <div class='v2-mono'>{selected['next_review'].strftime('%Y-%m-%d')} (D-{days_to})</div></div>"
            f"</div>"
            f"<div style='margin-top:0.8rem;'>"
            f"  <div style='color:#475569;font-size:0.75rem;margin-bottom:0.25rem;'>완성도 {selected['completeness']}/100</div>"
            f"  <div class='v2-completeness-bar-wrap'>"
            f"    <div class='v2-completeness-bar' style='width:{selected['completeness']}%;'></div>"
            f"  </div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # AI gap analysis
        if selected["ai_gap"]:
            # Find matching kolas-monitor feed item
            ai_text = (
                f"kolas-monitor 가 본 SOP 에서 갭을 식별했습니다.<br>"
                f"<strong>{selected['ai_gap']}</strong><br>"
                f"권장: 본 SOP 의 영향 받는 절차 섹션을 KAB-S-15 개정사항 (2026.04.18 발효) "
                f"에 맞춰 보완하시기 바랍니다."
            )
            st.markdown(
                f"<div class='v2-ai-card' style='margin-top:1rem;'>"
                f"<span class='v2-ai-badge'>AI</span>"
                f"{ai_text}"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.button("이 갭을 작업으로 추가", type="primary", use_container_width=True)
        else:
            st.success("✅ 현재 AI 가 식별한 갭이 없습니다.")

# ──────────────────────────────────────────
# kolas-monitor feed digest (bottom)
# ──────────────────────────────────────────
st.markdown("---")
st.markdown("<div class='v2-section-h'>kolas-monitor — 최근 영향 큰 변경</div>", unsafe_allow_html=True)
for item in monitor_r.payload.get("feed_items", []):
    if item.get("impact_level") != "high":
        continue
    affected = ", ".join(item.get("affected_sops", [])) or "—"
    st.markdown(
        f"<div class='v2-ai-card'>"
        f"<span class='v2-ai-badge'>AI</span>"
        f"<strong class='v2-mono'>{item['date']} · {item['source']}</strong><br>"
        f"{item['title']}<br>"
        f"<span style='color:#475569;font-size:0.85rem;'>영향 SOP: <span class='v2-mono'>{affected}</span> · 조치 기한 <span class='v2-mono'>{item.get('recommended_action_by','-')}</span></span>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.caption(
    "v0.6.0 baseline — 데모 SOP 데이터셋 사용. 실배포 시 SQLite/사용자 업로드 SOP DB 로 교체."
)
