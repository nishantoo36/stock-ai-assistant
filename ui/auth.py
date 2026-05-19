"""
Login, signup, and logout UI backed by Supabase Auth - Social Login Only.
"""

from __future__ import annotations
import re
from typing import Any
import streamlit as st
import streamlit.components.v1 as components

from utils.i18n import t
from utils.supabase_client import (
    SupabaseConfigError,
    get_public_supabase_client,
    send_phone_otp,
    sign_in_with_google,
    verify_phone_otp,
)

SESSION_COOKIE_HOURS = 4
ACCESS_COOKIE = "stock_ai_access_token"
REFRESH_COOKIE = "stock_ai_refresh_token"
LOGOUT_FLAG = "auth_logout_requested"

COUNTRY_CODE_OPTIONS = {
    "🇺🇸 +1": "+1",
    "🇮🇳 +91": "+91",
    "🇬🇧 +44": "+44",
    "🇫🇷 +33": "+33",
    "🇦🇺 +61": "+61",
    "🇦🇪 +971": "+971",
    "🇯🇵 +81": "+81",
    "Custom": "",
}


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
    _persist_auth_session(access_token, refresh_token)
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


def _format_phone_number(country_code: str, phone_number: str) -> str:
    code_digits = re.sub(r"\D", "", country_code)
    phone_digits = re.sub(r"\D", "", phone_number)
    if not code_digits or not phone_digits:
        return ""
    return f"+{code_digits}{phone_digits}"


def _render_phone_sign_in(key_prefix: str) -> None:
    st.markdown("#### Phone sign in")
    country_label = st.selectbox(
        "Country code",
        list(COUNTRY_CODE_OPTIONS.keys()),
        key=f"{key_prefix}_phone_country",
        label_visibility="collapsed",
    )

    country_code = COUNTRY_CODE_OPTIONS[country_label]
    if country_label == "Custom":
        country_code = st.text_input(
            "Country code",
            placeholder="+1",
            key=f"{key_prefix}_phone_custom_country",
        )

    phone_number = st.text_input(
        "Phone number",
        placeholder="Phone number",
        key=f"{key_prefix}_phone_number",
    )
    full_phone = _format_phone_number(country_code, phone_number)

    if st.button("Send code", key=f"{key_prefix}_send_phone_otp", use_container_width=True):
        if not full_phone:
            st.error("Enter a country code and phone number.")
        else:
            try:
                send_phone_otp(full_phone)
                st.session_state[f"{key_prefix}_phone_pending"] = full_phone
                st.success(f"Code sent to {full_phone}.")
            except SupabaseConfigError as exc:
                st.error(str(exc))

    pending_phone = st.session_state.get(f"{key_prefix}_phone_pending")
    if not pending_phone:
        return

    otp = st.text_input(
        "Verification code",
        placeholder="6-digit code",
        key=f"{key_prefix}_phone_otp",
    )
    if st.button("Verify code", key=f"{key_prefix}_verify_phone_otp", use_container_width=True):
        if not otp.strip():
            st.error("Enter the verification code.")
            return

        try:
            response = verify_phone_otp(pending_phone, otp.strip())
            if store_auth_session(response):
                st.session_state.pop(f"{key_prefix}_phone_pending", None)
                st.success("Signed in successfully.")
                st.rerun()
            else:
                st.error("Could not complete phone sign-in.")
        except SupabaseConfigError as exc:
            st.error(str(exc))


def _render_social_buttons(key_prefix: str = "auth") -> None:
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

        # Show only social login buttons
        _render_social_buttons("account")


def render_login_section() -> None:
    """Render an inline login target for unauthenticated action prompts."""
    if is_logged_in():
        st.session_state.show_login = False
        return

    with st.container(border=True):
        col_body, col_close = st.columns([5, 1])
        with col_body:
            _render_social_buttons("inline")
        with col_close:
            if st.button("X", key="close_inline_login", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()
