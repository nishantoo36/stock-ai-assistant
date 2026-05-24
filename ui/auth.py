"""
Login, signup, and logout UI backed by Supabase Auth.
"""

from __future__ import annotations
from html import escape
import logging
from typing import Any

import streamlit as st
from streamlit.components.v1 import html as render_html

from utils.common import attr
from utils.i18n import t
from utils.supabase_client import (
    get_public_supabase_client,
    get_auth_redirect_url,
    sign_in_with_google,
)

logger = logging.getLogger(__name__)

SESSION_COOKIE_HOURS = 4
ACCESS_COOKIE = "stock_ai_access_token"
REFRESH_COOKIE = "stock_ai_refresh_token"
LOGOUT_FLAG = "auth_logout_requested"
OAUTH_VERIFIER_COOKIE = "stock_ai_oauth_verifier"
PENDING_GOOGLE_AUTH = "pending_google_auth"
SOCIAL_LOGIN_MODAL = "show_social_login_modal"


def _render_script_iframe(script_html: str, height: int = 0, width: int = 0) -> None:
    render_html(script_html, height=height, width=width)


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
        logger.info("Persisting auth session cookies")
        _render_script_iframe(_cookie_script(access_token, refresh_token))


def _oauth_redirect_script(auth_url: str, code_verifier: str, redirect: bool = True) -> str:
    redirect_script = f"window.top.location.href = {auth_url!r};" if redirect else ""
    return f"""
    <script>
    const secureCookie = window.location.protocol === "https:" ? "; Secure" : "";
    const verifierCookie = "{OAUTH_VERIFIER_COOKIE}="
        + encodeURIComponent({code_verifier!r})
        + "; path=/; max-age=600; SameSite=Lax"
        + secureCookie;
    document.cookie = verifierCookie;
    try {{
        window.parent.document.cookie = verifierCookie;
    }} catch (err) {{}}
    {redirect_script}
    </script>
    """


def _clear_persistent_auth_session() -> None:
    logger.info("Clearing persisted auth cookies")
    _render_script_iframe(_cookie_script(clear=True), height=1, width=1)


def clear_oauth_verifier() -> None:
    """Expire the short-lived OAuth PKCE verifier cookie after callback handling."""
    _render_script_iframe(
        f"""
        <script>
        document.cookie = "{OAUTH_VERIFIER_COOKIE}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; "
            + "max-age=0; path=/; SameSite=Lax";
        try {{
            window.parent.document.cookie = "{OAUTH_VERIFIER_COOKIE}=; "
                + "expires=Thu, 01 Jan 1970 00:00:00 GMT; "
                + "max-age=0; path=/; SameSite=Lax";
        }} catch (err) {{}}
        </script>
        """,
    )


def persist_current_auth_session() -> None:
    """Keep auth cookies in sync after normal Streamlit reruns."""
    if st.session_state.get(LOGOUT_FLAG) or not is_logged_in():
        return

    session = st.session_state.get("auth_session", {})
    logger.info("Syncing current auth session to browser cookies")
    _persist_auth_session(session.get("access_token"), session.get("refresh_token"))


def store_auth_session(response: Any) -> bool:
    session = attr(response, "session")
    user = attr(response, "user")
    if not session or not user:
        return False

    access_token = attr(session, "access_token")
    refresh_token = attr(session, "refresh_token")

    st.session_state.auth_user = {
        "id": attr(user, "id"),
        "email": attr(user, "email"),
        "phone": attr(user, "phone"),
    }
    st.session_state.auth_session = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    st.session_state.pop(LOGOUT_FLAG, None)
    st.session_state.pop(PENDING_GOOGLE_AUTH, None)
    logger.info("Auth session stored for user id=%s", attr(user, "id"))
    return True


def restore_auth_session() -> None:
    """Restore a recent browser session after a refresh."""
    if st.session_state.get(LOGOUT_FLAG):
        logger.info("Skipping auth restore because logout was requested")
        _clear_persistent_auth_session()
        return

    if is_logged_in():
        logger.info("Skipping auth restore because user is already logged in")
        return

    access_token = st.context.cookies.get(ACCESS_COOKIE)
    refresh_token = st.context.cookies.get(REFRESH_COOKIE)
    if not access_token or not refresh_token:
        logger.info("No persisted auth session found in cookies")
        return

    try:
        logger.info("Restoring auth session from cookies")
        response = get_public_supabase_client().auth.set_session(access_token, refresh_token)
        store_auth_session(response)
    except Exception:
        logger.exception("Failed to restore auth session from cookies")
        _clear_persistent_auth_session()


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_user", {}).get("id"))


def get_current_user() -> dict:
    return st.session_state.get("auth_user", {})


def get_access_token() -> str | None:
    return st.session_state.get("auth_session", {}).get("access_token")


def logout() -> None:
    logger.info("Logout requested")
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_session", None)
    st.session_state.pop(PENDING_GOOGLE_AUTH, None)
    st.session_state[LOGOUT_FLAG] = True


def render_login_required_dialog() -> None:
    @st.dialog(t("auth.login_required_title"))
    def _dialog() -> None:
        st.caption(t("auth.login_required"))
        if st.button(t("auth.login"), key="go_to_inline_login", use_container_width=True):
            st.session_state.show_login = True
            st.session_state.scroll_to_login = True
            st.rerun()

    _dialog()


def _store_pending_google_auth(auth_url: str, code_verifier: str) -> None:
    st.session_state[PENDING_GOOGLE_AUTH] = {
        "url": auth_url,
        "code_verifier": code_verifier,
    }
    logger.info("Stored pending Google auth flow")


def _persist_oauth_verifier_cookie(code_verifier: str) -> None:
    # Keep the cookie fallback, while the callback URL carries the verifier.
    logger.info("Persisting OAuth verifier cookie")
    _render_script_iframe(
        _oauth_redirect_script("", code_verifier, redirect=False),
    )


def _get_or_create_google_auth() -> str | None:
    pending_auth = st.session_state.get(PENDING_GOOGLE_AUTH)
    if pending_auth and pending_auth.get("url"):
        return pending_auth["url"]

    logger.info("Generating Google sign-in URL for modal flow")
    redirect_to = get_auth_redirect_url()
    response = sign_in_with_google(redirect_to)
    auth_url = attr(response, "url")
    code_verifier = attr(response, "code_verifier")
    if auth_url and code_verifier:
        _store_pending_google_auth(auth_url, code_verifier)
        _persist_oauth_verifier_cookie(code_verifier)
        logger.info("Google sign-in URL generated successfully: %s", auth_url)
        return auth_url

    logger.warning("Google sign-in flow did not return a usable URL")
    return None


def _render_google_sign_in_modal() -> None:
    @st.dialog(t("auth.social_login"), width="small")
    def _dialog() -> None:
        st.caption("Let's login with google")

        auth_url = _get_or_create_google_auth()
        if not auth_url:
            st.error("Failed to get Google sign-in URL")
            return

        st.markdown(
            "<p style='margin:0 0 12px 0;color:var(--muted);font-size:0.88rem'>"
            "Continue in the same tab. The app will return to this page after login."
            "</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <a class="google-auth-link" href="{escape(auth_url, quote=True)}" target="_top" rel="noopener noreferrer">
                <span class="google-auth-icon" aria-hidden="true">↪</span>
                <span>Login with Google</span>
            </a>
            """,
            unsafe_allow_html=True,
        )

    _dialog()


def _render_sign_in_options() -> None:
    """Render available sign-in methods."""
    if st.button("Quick Sign in", key="open_social_login_modal", use_container_width=True):
        st.session_state[SOCIAL_LOGIN_MODAL] = True
        st.rerun()

    if st.session_state.pop(SOCIAL_LOGIN_MODAL, False):
        _render_google_sign_in_modal()


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

        _render_sign_in_options()


def render_login_section() -> None:
    """Render an inline login target for unauthenticated action prompts."""
    if is_logged_in():
        st.session_state.show_login = False
        return

    st.markdown("<div id='login-section'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        col_body, col_close = st.columns([5, 1])
        with col_body:
            st.markdown("### 🔐 Quick Sign in")
            _render_sign_in_options()
        with col_close:
            if st.button("X", key="close_inline_login", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()

    if st.session_state.pop("scroll_to_login", False):
        _render_script_iframe(
            """
            <script>
            const loginTarget = window.parent.document.getElementById("login-section");
            if (loginTarget) {
              loginTarget.scrollIntoView({ behavior: "smooth", block: "start" });
            }
            </script>
            """,
        )
