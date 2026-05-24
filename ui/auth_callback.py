import logging

import streamlit as st

from ui.auth import (
    LOGOUT_FLAG,
    OAUTH_VERIFIER_COOKIE,
    PENDING_GOOGLE_AUTH,
    clear_oauth_verifier,
    store_auth_session,
)
from utils.common import attr, query_param


logger = logging.getLogger(__name__)

AUTH_QUERY_KEYS = {
    "access_token",
    "code",
    "error",
    "error_code",
    "error_description",
    "expires_in",
    "provider_refresh_token",
    "provider_token",
    "refresh_token",
    "state",
    "token_type",
}


def _clear_auth_query_params() -> None:
    for key in AUTH_QUERY_KEYS:
        st.query_params.pop(key, None)


def handle_auth_callback() -> None:
    """Process auth tokens or OAuth codes from Supabase callback links."""
    query_params = st.query_params
    if not query_params:
        return

    logger.info("Auth callback received; keys=%s", sorted(query_params.keys()))

    auth_error = query_param(query_params, "error_description") or query_param(
        query_params, "error"
    )
    if auth_error:
        logger.warning("Auth callback error: %s", auth_error)
        st.error(f"Authentication failed: {auth_error}")
        _clear_auth_query_params()
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
            logger.info(
                "Auth code callback received; verifier_present=%s pending_auth=%s",
                bool(code_verifier),
                bool(pending_auth),
            )
            if not code_verifier:
                logger.warning("Auth callback missing verifier; session likely expired")
                st.error(
                    "Authentication failed: login session expired. "
                    "Please try signing in again."
                )
                _clear_auth_query_params()
                return

            logger.info("Exchanging auth code for session")
            response = exchange_oauth_code(auth_code, code_verifier)
            if store_auth_session(response):
                logger.info("OAuth session stored successfully")
                clear_oauth_verifier()
                _clear_auth_query_params()
                st.rerun()
        except Exception as exc:
            logger.exception("Authentication callback failed")
            st.error(f"Authentication failed: {exc}")
            _clear_auth_query_params()
        return

    if access_token:
        logger.info("Implicit token callback received; refresh_token_present=%s", bool(refresh_token))
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
                logger.info("Authenticated user resolved from access token")
                st.session_state.auth_user = {
                    "id": attr(user_info.user, "id", ""),
                    "email": attr(user_info.user, "email", ""),
                    "phone": attr(user_info.user, "phone", ""),
                }
        except Exception:
            logger.exception("Failed to resolve user from access token")

        _clear_auth_query_params()
        st.rerun()
