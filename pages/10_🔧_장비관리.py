"""장비 교정 이력 관리 페이지 (v0.5.0).

System of Record 전략의 핵심:
- 기관의 모든 장비를 등록하고 교정 이력을 추적
- 교정 기한 초과 장비 자동 알림
- 불확도 계산, 교정성적서와 데이터 연결
→ MetroAI가 기관의 품질 시스템 DB가 됨 = regulatory lock-in
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.db.database import get_db

st.set_page_config(
    page_title="MetroAI — 장비 교정 관리",
    page_icon="🔧",
    layout="wide",
)

db = get_db()

st.header("🔧 장비 교정 이력 관리")
st.caption("보유 장비의 교정 상태를 한눈에 관리하세요. KOLAS 심사 필수 서류인 '장비 교정 이력 관리대장'을 자동 생성합니다.")

# ──────────────────────────────────────────
# 대시보드
# ──────────────────────────────────────────
stats = db.get_dashboard_stats()
overdue_list = db.get_overdue_equipment()

m1, m2, m3, m4 = st.columns(4)
m1.metric("등록 장비", f"{stats['total_equipment']}대")
m2.metric("교정 기한 초과", f"{stats['overdue_equipment']}대",
          delta=f"-{stats['overdue_equipment']}" if stats['overdue_equipment'] > 0 else None,
          delta_color="inverse")
m3.metric("불확도 계산 이력", f"{stats['total_uncertainties']}건")
m4.metric("PT 참가 이력", f"{stats['total_pt']}건")

if overdue_list:
    st.error(f"⚠️ **교정 기한 초과 장비 {len(overdue_list)}대!** 아래에서 확인하세요.")

st.divider()

# ──────────────────────────────────────────
# 탭
# ──────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 장비 목록", "➕ 장비 등록", "📊 교정 현황"])

# ──── 탭 1: 장비 목록 ────
with tab1:
    equipment_list = db.get_all_equipment()

    if not equipment_list:
        st.info("등록된 장비가 없습니다. '장비 등록' 탭에서 첫 장비를 등록하세요.")
    else:
        for eq in equipment_list:
            # 상태 표시
            today = datetime.now().strftime("%Y-%m-%d")
            next_cal = eq.get("next_cal_date", "")
            if next_cal and next_cal < today:
                status_icon = "🔴"
                status_text = "교정 기한 초과"
            elif next_cal:
                days_left = (datetime.strptime(next_cal, "%Y-%m-%d") - datetime.now()).days
                if days_left <= 30:
                    status_icon = "🟡"
                    status_text = f"교정 {days_left}일 남음"
                else:
                    status_icon = "🟢"
                    status_text = f"교정 유효 ({days_left}일)"
            else:
                status_icon = "⚪"
                status_text = "교정일 미등록"

            with st.expander(
                f"{status_icon} **{eq['name']}** — {eq.get('manufacturer', '')} {eq.get('model', '')} "
                f"| S/N: {eq.get('serial_number', '-')} | {status_text}"
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**분야**: {eq.get('category', '-')}")
                    st.markdown(f"**위치**: {eq.get('location', '-')}")
                    st.markdown(f"**교정 주기**: {eq.get('cal_cycle_months', 12)}개월")
                with c2:
                    st.markdown(f"**최근 교정일**: {eq.get('last_cal_date', '-')}")
                    st.markdown(f"**다음 교정일**: {eq.get('next_cal_date', '-')}")
                    st.markdown(f"**교정 기관**: {eq.get('cal_org', '-')}")
                    st.markdown(f"**성적서 번호**: {eq.get('cal_cert_number', '-')}")

                if eq.get("notes"):
                    st.caption(f"메모: {eq['notes']}")

                # 교정 이력
                history = db.get_calibration_history(eq["id"])
                if history:
                    st.markdown("**교정 이력:**")
                    for h in history:
                        st.markdown(
                            f"- {h['cal_date']} | {h.get('cal_org', '-')} | "
                            f"성적서 {h.get('cal_cert_number', '-')} | "
                            f"U={h.get('expanded_uncertainty', '-')} | "
                            f"결과: {h.get('result', '-')}"
                        )

# ──── 탭 2: 장비 등록 ────
with tab2:
    st.subheader("새 장비 등록")

    with st.form("add_equipment", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            eq_name = st.text_input("장비명 *", placeholder="예: 블록게이지 세트")
            eq_mfr = st.text_input("제조사", placeholder="예: Mitutoyo")
            eq_model = st.text_input("모델", placeholder="예: Grade 0")
            eq_serial = st.text_input("일련번호", placeholder="예: SN-2024-001")
            eq_category = st.selectbox("분야", [
                "길이", "질량", "온도", "압력", "전기",
                "화학", "SEM/TEM/AFM", "유량", "기타",
            ])
        with c2:
            eq_location = st.text_input("보관 위치", placeholder="예: 표준실 1")
            eq_cycle = st.number_input("교정 주기 (개월)", value=12, min_value=1, max_value=60)
            eq_last_cal = st.text_input("최근 교정일", placeholder="2026-01-15")
            eq_cal_org = st.text_input("교정 기관", placeholder="예: KRISS")
            eq_cert = st.text_input("교정 성적서 번호", placeholder="예: CAL-2026-001")

        eq_notes = st.text_area("메모", placeholder="특이사항 기록", height=80)

        submitted = st.form_submit_button("📥 장비 등록", type="primary", use_container_width=True)

        if submitted and eq_name:
            # 다음 교정일 자동 계산
            next_cal = ""
            if eq_last_cal:
                try:
                    last_dt = datetime.strptime(eq_last_cal.strip(), "%Y-%m-%d")
                    next_dt = last_dt + timedelta(days=eq_cycle * 30)
                    next_cal = next_dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

            eq_id = db.add_equipment(
                name=eq_name,
                manufacturer=eq_mfr,
                model=eq_model,
                serial_number=eq_serial,
                category=eq_category,
                location=eq_location,
                cal_cycle_months=eq_cycle,
                last_cal_date=eq_last_cal,
                next_cal_date=next_cal,
                cal_org=eq_cal_org,
                cal_cert_number=eq_cert,
                notes=eq_notes,
            )

            # 초기 교정 이력도 추가
            if eq_last_cal:
                db.add_calibration(
                    equipment_id=eq_id,
                    cal_date=eq_last_cal,
                    cal_org=eq_cal_org,
                    cal_cert_number=eq_cert,
                    expanded_uncertainty="",
                    coverage_factor=2.0,
                    result="적합",
                    cost=0,
                    notes="초기 등록",
                )

            st.success(f"✅ **{eq_name}** 등록 완료! (ID: {eq_id})")
            st.rerun()

# ──── 탭 3: 교정 현황 ────
with tab3:
    st.subheader("📊 교정 현황 요약")

    equipment_list = db.get_all_equipment()
    if not equipment_list:
        st.info("장비를 먼저 등록하세요.")
    else:
        # 상태별 분류
        today_str = datetime.now().strftime("%Y-%m-%d")
        overdue = [e for e in equipment_list if e.get("next_cal_date", "9999") < today_str]
        soon = [e for e in equipment_list
                if e.get("next_cal_date", "9999") >= today_str
                and (datetime.strptime(e["next_cal_date"], "%Y-%m-%d") - datetime.now()).days <= 30]
        ok = [e for e in equipment_list if e not in overdue and e not in soon]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"### 🔴 기한 초과: {len(overdue)}대")
            for e in overdue:
                st.markdown(f"- **{e['name']}** (기한: {e.get('next_cal_date', '-')})")
        with c2:
            st.markdown(f"### 🟡 30일 이내: {len(soon)}대")
            for e in soon:
                st.markdown(f"- **{e['name']}** (기한: {e.get('next_cal_date', '-')})")
        with c3:
            st.markdown(f"### 🟢 정상: {len(ok)}대")
            st.caption(f"{len(ok)}대 모두 교정 유효 기간 내")

        # 교정 기한 타임라인
        if equipment_list:
            import plotly.express as px
            import pandas as pd

            df_data = []
            for e in equipment_list:
                if e.get("next_cal_date"):
                    df_data.append({
                        "장비": e["name"],
                        "다음 교정일": e["next_cal_date"],
                        "분야": e.get("category", "기타"),
                    })
            if df_data:
                df = pd.DataFrame(df_data)
                df["다음 교정일"] = pd.to_datetime(df["다음 교정일"])
                fig = px.timeline(
                    df,
                    x_start=pd.Timestamp.now(),
                    x_end="다음 교정일",
                    y="장비",
                    color="분야",
                    title="교정 일정 타임라인",
                )
                fig.update_layout(height=max(200, len(df_data) * 40))
                st.plotly_chart(fig, use_container_width=True)
