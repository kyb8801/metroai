"""기관 프로필 관리 모듈 (v0.5.0).

기관 정보를 세션에 저장하여 교정성적서 등에서 자동 불러오기.
YAML 파일로 영속 저장 (선택적).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
import streamlit as st

PROFILE_FILE = Path(__file__).resolve().parent.parent.parent / "org_profile.yaml"

# 기본 프로필 필드
PROFILE_FIELDS = {
    "org_name": ("기관명", ""),
    "kolas_id": ("KOLAS 인정번호", "KOLAS-"),
    "org_address": ("소재지", ""),
    "cal_location": ("교정 장소", ""),
    "calibrator_name": ("교정원", ""),
    "reviewer_name": ("검토자", ""),
    "approver_name": ("책임자", ""),
    "default_temp": ("기본 온도 조건", "20.0 ± 0.5 °C"),
    "default_humidity": ("기본 습도 조건", "50 ± 10 %RH"),
}


def load_profile() -> dict:
    """프로필 로드 (파일 → 세션 → 기본값 순)."""
    if "org_profile" in st.session_state:
        return st.session_state.org_profile

    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            st.session_state.org_profile = data
            return data
        except Exception:
            pass

    return {k: v[1] for k, v in PROFILE_FIELDS.items()}


def save_profile(profile: dict) -> None:
    """프로필 저장 (세션 + 파일)."""
    st.session_state.org_profile = profile
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False)
    except Exception:
        pass  # 파일 쓰기 실패해도 세션은 유지


def render_profile_form(location: str = "main") -> Optional[dict]:
    """프로필 입력 폼 렌더링.

    Args:
        location: "main" 또는 "sidebar"

    Returns:
        저장 시 프로필 dict, 아니면 None
    """
    profile = load_profile()

    container = st if location == "main" else st.sidebar

    with container.form("org_profile_form"):
        container.markdown("**기관 프로필 설정**")
        container.caption("한 번 입력하면 교정성적서 등에서 자동으로 불러옵니다.")

        updated = {}
        for key, (label, default) in PROFILE_FIELDS.items():
            updated[key] = st.text_input(
                label,
                value=profile.get(key, default),
                key=f"profile_{key}",
            )

        submitted = st.form_submit_button("💾 프로필 저장", type="primary")

        if submitted:
            save_profile(updated)
            st.success("✅ 기관 프로필이 저장되었습니다.")
            return updated

    return None


def get_profile_value(key: str, fallback: str = "") -> str:
    """프로필에서 특정 값을 가져오기."""
    profile = load_profile()
    return profile.get(key, fallback)
