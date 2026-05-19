"""
Login, signup, and logout UI backed by Supabase Auth.
"""

from __future__ import annotations
from typing import Any
import streamlit as st
import streamlit.components.v1 as components

from utils.i18n import t
from utils.supabase_client import (
    get_public_supabase_client,
    sign_in_with_google,
)

SESSION_COOKIE_HOURS = 4
ACCESS_COOKIE = "stock_ai_access_token"
REFRESH_COOKIE = "stock_ai_refresh_token"
LOGOUT_FLAG = "auth_logout_requested"


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _cookie_script(access_token: str = "", refresh_token: str = "", clear: bool = False) -> str:
    if clear:
        # clear cookies by expiring them immediately
        expires = "Thu, 01 Jan 1970 00:00:00 GMT"
        return f"""
        <script>
        document.cookie = "{ACCESS_COOKIE}=; expires={expires}; max-age=0; path=/; SameSite=Lax";
        document.cookie = "{REFRESH_COOKIE}=; expires={expires}; max-age=0; path=/; SameSite=Lax";
        </script>
        """
    else:
        max_age = SESSION_COOKIE_HOURS * 60 * 60
        return f"""
        <script>
        const options = "path=/; max-age={max_age}; SameSite=Lax";
        document.cookie = "{ACCESS_COOKIE}=" + encodeURIComponent({access_token!r}) + "; " + options;
        document.cookie = "{REFRESH_COOKIE}=" + encodeURIComponent({refresh_token!r}) + "; " + options;
        </script>
        """


def _persist_auth_session(access_token: str | None, refresh_token: str | None) -> None:
    if access_token and refresh_token:
        components.html(_cookie_script(access_token, refresh_token), height=0, width=0)


def _clear_persistent_auth_session() -> None:
    components.html(_cookie_script(clear=True), height=1, width=1)


def persist_current_auth_session() -> None:
    """Keep auth cookies in sync after normal Streamlit reruns."""
    if st.session_state.get(LOGOUT_FLAG) or not is_logged_in():
        return

    session = st.session_state.get("auth_session", {})
    _persist_auth_session(session.get("access_token"), session.get("refresh_token"))


def store_auth_session(response: Any) -> bool:
    session = _attr(response, "session")
    user = _attr(response, "user")
    if not session or not user:
        return False

    access_token = _attr(session, "access_token")
    refresh_token = _attr(session, "refresh_token")

    st.session_state.auth_user = {
        "id": _attr(user, "id"),
        "email": _attr(user, "email"),
        "phone": _attr(user, "phone"),
    }
    st.session_state.auth_session = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    st.session_state.pop(LOGOUT_FLAG, None)
    return True


def restore_auth_session() -> None:
    """Restore a recent browser session after a refresh."""
    if st.session_state.get(LOGOUT_FLAG):
        _clear_persistent_auth_session()
        return

    if is_logged_in():
        return

    access_token = st.context.cookies.get(ACCESS_COOKIE)
    refresh_token = st.context.cookies.get(REFRESH_COOKIE)
    if not access_token or not refresh_token:
        return

    try:
        response = get_public_supabase_client().auth.set_session(access_token, refresh_token)
        store_auth_session(response)
    except Exception:
        _clear_persistent_auth_session()


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_user", {}).get("id"))


def get_current_user() -> dict:
    return st.session_state.get("auth_user", {})


def get_access_token() -> str | None:
    return st.session_state.get("auth_session", {}).get("access_token")


def logout() -> None:
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_session", None)
    st.session_state[LOGOUT_FLAG] = True


def _render_sign_in_options(key_prefix: str = "auth") -> None:
    """Render available sign-in methods."""
    st.markdown("### 🔐 Quick Sign In")

    if st.button(
        "🔵 Sign in with Google",
        key=f"{key_prefix}_google_oauth",
        use_container_width=True,
    ):
        try:
            response = sign_in_with_google()
            auth_url = _attr(response, "url")
            if auth_url:
                st.markdown(f"[Click here to sign in with Google]({auth_url})")
            else:
                st.error("Failed to get Google sign-in URL")
        except Exception as exc:
            st.error(f"Google sign-in error: {str(exc)}")


def render_auth_panel() -> None:
    """Render account controls - Social login only."""
    with st.popover(t("auth.account"), use_container_width=True):
        if is_logged_in():
            user = get_current_user()
            identity = user.get("email") or user.get("phone") or ""
            st.caption(t("auth.signed_in_as", email=identity))
            if st.button("Manage alerts", use_container_width=True):
                from ui.alerts import render_price_alerts_dialog
                render_price_alerts_dialog()
            if st.button(t("auth.logout"), use_container_width=True):
                logout()
                st.rerun()
            return

        _render_sign_in_options("account")


def render_login_section() -> None:
    """Render an inline login target for unauthenticated action prompts."""
    if is_logged_in():
        st.session_state.show_login = False
        return

    with st.container(border=True):
        col_body, col_close = st.columns([5, 1])
        with col_body:
            _render_sign_in_options("inline")
        with col_close:
            if st.button("X", key="close_inline_login", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()
