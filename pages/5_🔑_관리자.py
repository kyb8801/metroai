"""관리자 전용 페이지 — 사용자 관리, 사용량 통계, 시스템 설정."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.auth import (
    init_auth_state,
    render_auth_sidebar,
    get_auth_manager,
    get_usage_manager,
    is_admin,
)

st.set_page_config(
    page_title="MetroAI — 관리자",
    page_icon="🔑",
    layout="wide",
)

# ──────────────────────────────────────────
# 인증
# ──────────────────────────────────────────
init_auth_state()
username, name = render_auth_sidebar()

if username:
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.name = name

# ──────────────────────────────────────────
# 관리자 권한 체크
# ──────────────────────────────────────────
if not is_admin():
    st.title("🔑 관리자 페이지")
    st.warning("⛔ 관리자 계정으로 로그인해야 접근할 수 있습니다.")
    st.info("**관리자 로그인:** 사이드바에서 admin 계정으로 로그인하세요.")
    st.stop()

# ──────────────────────────────────────────
# 관리자 대시보드
# ──────────────────────────────────────────
st.title("🔑 관리자 대시보드")
st.caption(f"👑 {st.session_state.name} ({st.session_state.username})")

tab_users, tab_usage, tab_settings = st.tabs(["👥 사용자 관리", "📊 사용량 통계", "⚙️ 시스템 설정"])

# ──────────────────────────────────────────
# 탭 1: 사용자 관리
# ──────────────────────────────────────────
with tab_users:
    st.subheader("👥 등록된 사용자")

    auth_manager = get_auth_manager()
    users = auth_manager.get_all_users()

    if users:
        # 사용자 목록 테이블
        user_data = []
        for uname, info in users.items():
            role_display = "👑 관리자" if info["role"] == "admin" else "👤 일반"
            user_data.append({
                "사용자명": uname,
                "이름": info["name"],
                "권한": role_display,
            })

        st.dataframe(user_data, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(users)}명 등록됨")

    # 사용자 삭제
    st.markdown("---")
    st.subheader("🗑️ 사용자 삭제")
    deletable_users = [u for u in users.keys() if u != "admin"]
    if deletable_users:
        del_target = st.selectbox("삭제할 사용자", deletable_users)
        if st.button("삭제", type="secondary"):
            if auth_manager.delete_user(del_target):
                st.success(f"✅ {del_target} 삭제 완료")
                st.rerun()
            else:
                st.error("삭제 실패")
    else:
        st.info("삭제 가능한 사용자가 없습니다.")

    # 비밀번호 변경
    st.markdown("---")
    st.subheader("🔒 비밀번호 변경")
    all_usernames = list(users.keys())
    with st.form("change_pw_form"):
        pw_target = st.selectbox("대상 사용자", all_usernames)
        new_pw = st.text_input("새 비밀번호", type="password")
        pw_submit = st.form_submit_button("변경")
    if pw_submit and new_pw:
        if auth_manager.change_password(pw_target, new_pw):
            st.success(f"✅ {pw_target} 비밀번호 변경 완료")
        else:
            st.error("변경 실패")

# ──────────────────────────────────────────
# 탭 2: 사용량 통계
# ──────────────────────────────────────────
with tab_usage:
    st.subheader("📊 사용량 현황")

    usage_manager = get_usage_manager()
    all_usage = usage_manager.get_all_users_usage()

    if all_usage:
        usage_rows = []
        for uname, info in all_usage.items():
            usage_rows.append({
                "사용자명": uname,
                "이번 달 계산 횟수": info.get("count", 0),
                "기준 월": info.get("month", "-"),
                "최초 사용일": info.get("first_used", "-")[:10] if info.get("first_used") else "-",
            })
        st.dataframe(usage_rows, use_container_width=True, hide_index=True)

        total_calcs = sum(r["이번 달 계산 횟수"] for r in usage_rows)
        st.metric("이번 달 총 계산 횟수", total_calcs)
    else:
        st.info("아직 사용 기록이 없습니다.")

# ──────────────────────────────────────────
# 탭 3: 시스템 설정
# ──────────────────────────────────────────
with tab_settings:
    st.subheader("⚙️ 시스템 정보")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("MetroAI 버전", "v0.4.0")
        st.metric("테스트", "69/69 통과")
        st.metric("Streamlit 페이지", "5개")
    with col2:
        st.metric("코어 엔진", "GUM + MCM + 역설계")
        st.metric("템플릿", "5개 (블록게이지, 분동, 온도, 압력, 수동)")
        st.metric("인증 방식", "세션 기반 (SHA-256)")

    st.markdown("---")
    st.subheader("📋 시스템 경로")
    auth_mgr = get_auth_manager()
    usage_mgr = get_usage_manager()
    st.code(f"Config: {auth_mgr.config_path}\nUsage:  {usage_mgr.usage_data_path}")
