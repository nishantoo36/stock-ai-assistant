"""
Supabase client helpers.

The public anon/publishable key is safe to use from Streamlit, while the
service-role key must never be placed in st.secrets for this app.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import streamlit as st


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


class SupabaseConfigError(RuntimeError):
    """Raised when Supabase is not configured for the local app."""


def _get_secret(name: str) -> str:
    value = st.secrets.get(name, "")
    return str(value).strip() if value else ""


def _validate_url(url: str, setting_name: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SupabaseConfigError(
            f"{setting_name} must be a valid http(s) URL, for example "
            "http://localhost:8501."
        )
    return url.rstrip("/")


def _strip_auth_query_params(url: str) -> str:
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for key in AUTH_QUERY_KEYS:
        query_params.pop(key, None)
    return urlunparse(parsed._replace(query=urlencode(query_params)))


def get_supabase_config() -> tuple[str, str]:
    """Return Supabase URL and anon/publishable key from Streamlit secrets."""
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_ANON_KEY")

    if not url or not key:
        raise SupabaseConfigError(
            "Supabase is not configured. Add SUPABASE_URL and "
            "SUPABASE_ANON_KEY to .streamlit/secrets.toml."
        )

    return _validate_url(url, "SUPABASE_URL"), key


def get_auth_redirect_url() -> str:
    """
    Return the app URL Supabase should redirect back to.

    Prefer the active Streamlit URL when available so local and deployed runs
    both redirect back to the environment they were opened in.
    """
    current_url = getattr(st.context, "url", "") or ""
    if current_url:
        current_url = _strip_auth_query_params(current_url).rstrip("/")

    configured_url = (
        _get_secret("AUTH_REDIRECT_URL")
        or _get_secret("APP_URL")
        or _get_secret("STREAMLIT_APP_URL")
    )
    url = current_url or configured_url

    redirect_url = _validate_url(url or "http://localhost:8501", "APP_URL")
    logger.info(
        "Auth redirect selected: source=%s redirect=%s",
        "current_url" if current_url else "configured_url",
        redirect_url,
    )
    return redirect_url


@st.cache_resource(show_spinner=False)
def get_public_supabase_client() -> Any:
    """Create an unauthenticated Supabase client for auth operations."""
    try:
        from supabase import create_client
    except ImportError as exc:
        raise SupabaseConfigError(
            "The supabase package is not installed. Run: pip install supabase"
        ) from exc

    url, key = get_supabase_config()
    return create_client(url, key)


def get_user_supabase_client(access_token: str | None = None) -> Any:
    """
    Create a Supabase client scoped to the current user's access token.

    RLS policies in Supabase use auth.uid(), which is derived from this token.
    """
    try:
        from supabase import create_client
    except ImportError as exc:
        raise SupabaseConfigError(
            "The supabase package is not installed. Run: pip install supabase"
        ) from exc

    url, key = get_supabase_config()
    client = create_client(url, key)

    if access_token:
        postgrest = getattr(client, "postgrest", None)
        auth_method = getattr(postgrest, "auth", None)
        if callable(auth_method):
            auth_method(access_token)

    return client


def exchange_oauth_code(auth_code: str, code_verifier: str | None = None) -> Any:
    """Exchange a Supabase OAuth callback code for an auth session."""
    client = get_public_supabase_client()
    logger.info("Exchanging OAuth code for session")
    params = {
        "auth_code": auth_code,
        "redirect_to": get_auth_redirect_url(),
    }
    if code_verifier:
        params["code_verifier"] = code_verifier

    return client.auth.exchange_code_for_session(params)


def sign_in_with_google(redirect_to: str | None = None) -> dict[str, Any]:
    """
    Initiate Google OAuth sign in flow.
    Returns the OAuth response with URL for redirecting user to Google.
    """
    try:
        from supabase_auth.helpers import generate_pkce_challenge, generate_pkce_verifier

        url, _ = get_supabase_config()
        verifier = generate_pkce_verifier()
        challenge = generate_pkce_challenge(verifier)
        redirect_to = redirect_to or get_auth_redirect_url()
        query = urlencode(
            {
                "provider": "google",
                "redirect_to": redirect_to,
                "code_challenge": challenge,
                "code_challenge_method": "s256",
            }
        )
        logger.info("Generated Google OAuth authorization URL")
        return {
            "url": f"{url}/auth/v1/authorize?{query}",
            "code_verifier": verifier,
        }
    except Exception as exc:
        logger.exception("Google OAuth setup failed")
        raise SupabaseConfigError(f"Google OAuth failed: {str(exc)}") from exc
