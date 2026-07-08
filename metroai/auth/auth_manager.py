"""인증 및 사용량 관리 모듈.

streamlit-authenticator 의존성을 제거하고, 순수 세션 기반 인증으로 교체.
쿠키/extra-streamlit-components 의존 없음.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
import yaml


# ──────────────────────────────────────────
# 비밀번호 해싱 (bcrypt 대신 hashlib 사용 — 외부 의존성 없음)
# ──────────────────────────────────────────

def _hash_password(password: str, salt: str = None) -> str:
    """비밀번호 해싱 (SHA-256 + salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password: str, stored: str) -> bool:
    """비밀번호 검증."""
    if ":" not in stored:
        return False
    salt = stored.split(":")[0]
    return _hash_password(password, salt) == stored


# ──────────────────────────────────────────
# UsageManager (변경 없음)
# ──────────────────────────────────────────

class UsageManager:
    """사용량 추적 및 제한 관리."""

    def __init__(self, usage_data_path: Path | str = None):
        if usage_data_path is None:
            usage_data_path = Path(__file__).resolve().parent / "usage_data.json"
        else:
            usage_data_path = Path(usage_data_path)
        self.usage_data_path = usage_data_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.usage_data_path.exists():
            self.usage_data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.usage_data_path, "w") as f:
                json.dump({}, f)

    def _load_data(self) -> dict:
        try:
            with open(self.usage_data_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: dict):
        with open(self.usage_data_path, "w") as f:
            json.dump(data, f, indent=2)

    def _get_current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def get_usage(self, username: str) -> dict:
        data = self._load_data()
        user_data = data.get(username, {})
        current_month = self._get_current_month()
        if user_data.get("month") != current_month:
            user_data = {
                "count": 0,
                "month": current_month,
                "first_used": datetime.now().isoformat(),
            }
            data[username] = user_data
            self._save_data(data)
        return user_data

    def check_limit(self, username: str, limit: int = 3) -> bool:
        usage = self.get_usage(username)
        return usage.get("count", 0) < limit

    def increment_usage(self, username: str):
        data = self._load_data()
        usage = self.get_usage(username)
        usage["count"] = usage.get("count", 0) + 1
        data[username] = usage
        self._save_data(data)

    def get_remaining(self, username: str, limit: int = 3) -> int:
        usage = self.get_usage(username)
        count = usage.get("count", 0)
        return max(0, limit - count)

    def get_all_users_usage(self) -> dict:
        """모든 사용자 사용량 조회 (관리자용)."""
        return self._load_data()


# ──────────────────────────────────────────
# AuthManager (streamlit-authenticator 제거, 순수 YAML+세션)
# ──────────────────────────────────────────

class AuthManager:
    """순수 세션 기반 인증 관리자."""

    ADMIN_ROLE = "admin"
    USER_ROLE = "user"

    def __init__(self, config_path: Path | str = None):
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
                            "name": "관리자",
                            "password": _hash_password("admin123"),
                            "role": self.ADMIN_ROLE,
                        },
                        "guest": {
                            "name": "게스트",
                            "password": _hash_password("guest"),
                            "role": self.USER_ROLE,
                        },
                    }
                },
            }
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

    def _load_config(self) -> dict:
        with open(self.config_path) as f:
            return yaml.safe_load(f) or {}

    def _save_config(self, config: dict):
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """로그인 인증.

        Returns:
            성공 시 {"username": str, "name": str, "role": str}, 실패 시 None
        """
        config = self._load_config()
        users = config.get("credentials", {}).get("usernames", {})
        user = users.get(username)
        if user is None:
            return None
        if _verify_password(password, user.get("password", "")):
            return {
                "username": username,
                "name": user.get("name", username),
                "role": user.get("role", self.USER_ROLE),
            }
        return None

    def register(self, username: str, name: str, password: str) -> tuple[bool, str]:
        """회원가입.

        Returns:
            (success, message)
        """
        if len(username) < 3:
            return False, "사용자명은 3자 이상이어야 합니다."
        if len(password) < 4:
            return False, "비밀번호는 4자 이상이어야 합니다."

        config = self._load_config()
        users = config.get("credentials", {}).get("usernames", {})

        if username in users:
            return False, "이미 존재하는 사용자명입니다."

        users[username] = {
            "name": name,
            "password": _hash_password(password),
            "role": self.USER_ROLE,
        }
        config["credentials"]["usernames"] = users
        self._save_config(config)
        return True, "회원가입이 완료되었습니다."

    def is_admin(self, username: str) -> bool:
        """관리자 여부 확인."""
        config = self._load_config()
        users = config.get("credentials", {}).get("usernames", {})
        user = users.get(username, {})
        return user.get("role") == self.ADMIN_ROLE

    def get_all_users(self) -> dict:
        """모든 사용자 목록 (관리자용, 비밀번호 제외)."""
        config = self._load_config()
        users = config.get("credentials", {}).get("usernames", {})
        return {
            k: {"name": v.get("name"), "role": v.get("role", self.USER_ROLE)}
            for k, v in users.items()
        }

    def delete_user(self, username: str) -> bool:
        """사용자 삭제 (관리자용). admin은 삭제 불가."""
        if username == "admin":
            return False
        config = self._load_config()
        users = config.get("credentials", {}).get("usernames", {})
        if username in users:
            del users[username]
            config["credentials"]["usernames"] = users
            self._save_config(config)
            return True
        return False

    def change_password(self, username: str, new_password: str) -> bool:
        """비밀번호 변경."""
        config = self._load_config()
        users = config.get("credentials", {}).get("usernames", {})
        if username in users:
            users[username]["password"] = _hash_password(new_password)
            config["credentials"]["usernames"] = users
            self._save_config(config)
            return True
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
    defaults = {
        "authenticated": False,
        "username": None,
        "name": None,
        "role": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


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
        role_badge = " 👑" if st.session_state.role == AuthManager.ADMIN_ROLE else ""
        st.sidebar.success(f"✅ {st.session_state.name}{role_badge} 로그인됨")

        if st.sidebar.button("🚪 로그아웃", use_container_width=True, key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
            st.session_state.role = None
            st.rerun()

        return st.session_state.username, st.session_state.name

    # 로그인 안된 상태
    auth_manager = get_auth_manager()
    auth_tab, signup_tab = st.sidebar.tabs(["로그인", "회원가입"])

    with auth_tab:
        with st.form("login_form", clear_on_submit=False):
            login_username = st.text_input("사용자명", key="login_user")
            login_password = st.text_input("비밀번호", type="password", key="login_pass")
            login_submit = st.form_submit_button("로그인", use_container_width=True)

        if login_submit and login_username and login_password:
            result = auth_manager.authenticate(login_username, login_password)
            if result:
                st.session_state.authenticated = True
                st.session_state.username = result["username"]
                st.session_state.name = result["name"]
                st.session_state.role = result["role"]
                st.rerun()
            else:
                st.error("사용자명 또는 비밀번호가 잘못되었습니다.")

    with signup_tab:
        with st.form("signup_form", clear_on_submit=True):
            reg_name = st.text_input("이름", key="reg_name")
            reg_username = st.text_input("사용자명 (영문)", key="reg_user")
            reg_password = st.text_input("비밀번호", type="password", key="reg_pass")
            reg_submit = st.form_submit_button("회원가입", use_container_width=True)

        if reg_submit and reg_username and reg_password and reg_name:
            success, msg = auth_manager.register(reg_username, reg_name, reg_password)
            if success:
                st.success(msg + " 로그인해주세요.")
            else:
                st.error(msg)

    return None, None


def show_usage_info(username: str):
    """사용량 정보 표시."""
    usage_manager = get_usage_manager()
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


def is_admin() -> bool:
    """현재 세션이 관리자인지 확인."""
    return (
        st.session_state.get("authenticated", False)
        and st.session_state.get("role") == AuthManager.ADMIN_ROLE
    )
