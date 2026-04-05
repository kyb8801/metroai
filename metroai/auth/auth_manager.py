"""인증 및 사용량 관리 모듈."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from pathlib import Path


class UsageManager:
    """사용량 추적 및 제한 관리."""

    def __init__(self, usage_data_path: Path | str = None):
        """
        Args:
            usage_data_path: JSON 파일 경로. None이면 metroai/auth/usage_data.json 사용.
        """
        if usage_data_path is None:
            usage_data_path = Path(__file__).resolve().parent / "usage_data.json"
        else:
            usage_data_path = Path(usage_data_path)

        self.usage_data_path = usage_data_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """파일 생성 및 초기 데이터 설정."""
        if not self.usage_data_path.exists():
            self.usage_data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.usage_data_path, "w") as f:
                json.dump({}, f)

    def _load_data(self) -> dict:
        """사용량 데이터 로드."""
        try:
            with open(self.usage_data_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: dict):
        """사용량 데이터 저장."""
        with open(self.usage_data_path, "w") as f:
            json.dump(data, f, indent=2)

    def _get_current_month(self) -> str:
        """현재 월 (YYYY-MM 형식)."""
        return datetime.now().strftime("%Y-%m")

    def get_usage(self, username: str) -> dict:
        """사용자 사용량 조회.

        Returns:
            {
                "count": 계산 횟수,
                "month": "2026-04",
                "first_used": ISO 8601 타임스탬프
            }
        """
        data = self._load_data()
        user_data = data.get(username, {})

        # 월 리셋 확인
        current_month = self._get_current_month()
        user_month = user_data.get("month")

        if user_month != current_month:
            # 새 달이면 리셋
            user_data = {
                "count": 0,
                "month": current_month,
                "first_used": datetime.now().isoformat(),
            }
            data[username] = user_data
            self._save_data(data)

        return user_data

    def check_limit(self, username: str, limit: int = 3) -> bool:
        """사용 가능 여부 확인.

        Args:
            username: 사용자명
            limit: 월 한도 (기본값 3)

        Returns:
            True if 사용 가능, False if 한도 초과
        """
        usage = self.get_usage(username)
        return usage.get("count", 0) < limit

    def increment_usage(self, username: str):
        """사용량 증가."""
        data = self._load_data()
        usage = self.get_usage(username)
        usage["count"] = usage.get("count", 0) + 1
        data[username] = usage
        self._save_data(data)

    def get_remaining(self, username: str, limit: int = 3) -> int:
        """남은 사용량.

        Returns:
            남은 계산 횟수 (최소 0)
        """
        usage = self.get_usage(username)
        count = usage.get("count", 0)
        return max(0, limit - count)


class AuthManager:
    """Streamlit Authenticator 래퍼."""

    def __init__(self, config_path: Path | str = None):
        """
        Args:
            config_path: YAML 설정 파일 경로. None이면 metroai/auth/config.yaml 사용.
        """
        if config_path is None:
            config_path = Path(__file__).resolve().parent / "config.yaml"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """설정 파일 생성 및 기본값 설정."""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "credentials": {
                    "usernames": {
                        "admin": {
                            "name": "Admin",
                            "password": stauth.Hasher(["admin123"]).generate()[0],
                        },
                        "guest": {
                            "name": "Guest",
                            "password": stauth.Hasher(["guest"]).generate()[0],
                        },
                    }
                },
                "cookie": {
                    "expiry_days": 30,
                    "key": "metroai_auth_key",
                    "name": "metroai_auth_cookie",
                },
                "preauthorized": {"emails": []},
            }
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)

    def get_authenticator(self) -> stauth.Authenticate:
        """인증자 인스턴스 반환."""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        authenticator = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
            config["preauthorized"],
        )
        return authenticator

    def login_widget(self) -> tuple[Optional[str], Optional[str]]:
        """로그인 위젯 표시 및 반환.

        Returns:
            (username, name) 튜플, 로그인 안됨시 (None, None)
        """
        authenticator = self.get_authenticator()

        try:
            name, authentication_status, username = authenticator.login(
                "login", "main", fields={"Form name": "로그인"}
            )
        except Exception as e:
            st.error(f"로그인 오류: {e}")
            return None, None

        if authentication_status:
            return username, name
        elif authentication_status is False:
            st.error("사용자명 또는 비밀번호가 잘못되었습니다.")
            return None, None
        else:
            # 로그인 상태 아님
            return None, None

    def signup_widget(self) -> bool:
        """회원가입 위젯 표시.

        Returns:
            True if 회원가입 성공
        """
        authenticator = self.get_authenticator()

        try:
            if authenticator.register_user("회원가입", "main", preauthorization=False):
                st.success("회원가입이 완료되었습니다. 로그인해주세요.")
                return True
        except Exception as e:
            st.error(f"회원가입 오류: {e}")
            return False

        return False


# ──────────────────────────────────────────
# 편의 함수
# ──────────────────────────────────────────


def get_auth_manager() -> AuthManager:
    """AuthManager 싱글톤 반환."""
    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    return st.session_state.auth_manager


def get_usage_manager() -> UsageManager:
    """UsageManager 싱글톤 반환."""
    if "usage_manager" not in st.session_state:
        st.session_state.usage_manager = UsageManager()
    return st.session_state.usage_manager


def init_auth_state():
    """세션 상태에서 인증 정보 초기화."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "name" not in st.session_state:
        st.session_state.name = None


def render_auth_sidebar():
    """사이드바에 인증 위젯 렌더링.

    Returns:
        (username, name) 튜플 또는 (None, None)
    """
    init_auth_state()

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 인증")

    # 이미 로그인된 상태
    if st.session_state.authenticated and st.session_state.username:
        st.sidebar.success(f"✅ {st.session_state.name} 로그인됨")
        if st.sidebar.button("🚪 로그아웃", use_container_width=True, key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
            st.rerun()
        return st.session_state.username, st.session_state.name

    # 로그인 안된 상태
    auth_manager = get_auth_manager()
    auth_tab, signup_tab = st.sidebar.tabs(["로그인", "회원가입"])

    with auth_tab:
        username, name = auth_manager.login_widget()
        if username:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.name = name
            st.rerun()

    with signup_tab:
        auth_manager.signup_widget()

    return None, None


def show_usage_info(username: str):
    """사용량 정보 표시.

    Args:
        username: 로그인한 사용자명
    """
    usage_manager = get_usage_manager()
    usage = usage_manager.get_usage(username)
    remaining = usage_manager.get_remaining(username, limit=3)

    st.sidebar.markdown("---")
    st.sidebar.info(f"📊 **이번 달 남은 계산: {remaining}/3**")


def show_guest_notice():
    """게스트 사용자 안내 표시."""
    st.sidebar.markdown("---")
    st.sidebar.warning(
        "👤 **게스트 모드**\n"
        "로그인하면 이용 기록이 저장됩니다."
    )
