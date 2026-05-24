import streamlit as st

from ui.auth import (
    LOGOUT_FLAG,
    OAUTH_VERIFIER_COOKIE,
    PENDING_GOOGLE_AUTH,
    clear_oauth_verifier,
    store_auth_session,
)
from utils.common import attr, query_param


def handle_auth_callback() -> None:
    """Process auth tokens or OAuth codes from Supabase callback links."""
    query_params = st.query_params
    if not query_params:
        return

    auth_error = query_param(query_params, "error_description") or query_param(
        query_params, "error"
    )
    if auth_error:
        st.error(f"Authentication failed: {auth_error}")
        st.query_params.clear()
        return

    access_token = query_param(query_params, "access_token")
    refresh_token = query_param(query_params, "refresh_token")
    auth_code = query_param(query_params, "code")
    oauth_verifier = query_param(query_params, "oauth_verifier")

    if auth_code:
        try:
            from utils.supabase_client import exchange_oauth_code

            pending_auth = st.session_state.get(PENDING_GOOGLE_AUTH) or {}
            code_verifier = (
                st.context.cookies.get(OAUTH_VERIFIER_COOKIE)
                or pending_auth.get("code_verifier")
                or oauth_verifier
            )
            if not code_verifier:
                st.error(
                    "Authentication failed: login session expired. "
                    "Please try signing in again."
                )
                st.query_params.clear()
                return

            response = exchange_oauth_code(auth_code, code_verifier)
            if store_auth_session(response):
                clear_oauth_verifier()
                st.query_params.clear()
                st.rerun()
        except Exception as exc:
            st.error(f"Authentication failed: {exc}")
            st.query_params.clear()
        return

    if access_token:
        st.session_state.pop(LOGOUT_FLAG, None)
        st.session_state.auth_session = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        try:
            from utils.supabase_client import get_user_supabase_client

            client = get_user_supabase_client(access_token)
            user_info = client.auth.get_user(access_token)
            if user_info:
                st.session_state.auth_user = {
                    "id": attr(user_info.user, "id", ""),
                    "email": attr(user_info.user, "email", ""),
                    "phone": attr(user_info.user, "phone", ""),
                }
        except Exception:
            pass

        st.query_params.clear()
        st.rerun()
