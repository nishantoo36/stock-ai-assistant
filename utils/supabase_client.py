"""
Supabase client helpers.

The public anon/publishable key is safe to use from Streamlit, while the
service-role key must never be placed in st.secrets for this app.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any
from urllib.parse import urlencode, urlparse

import streamlit as st


class SupabaseConfigError(RuntimeError):
    """Raised when Supabase is not configured for the local app."""


OAUTH_STATE_MAX_AGE_SECONDS = 10 * 60


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


def _is_local_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"}


def _encode_oauth_state(payload: dict[str, Any]) -> str:
    state_json = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(state_json).decode().rstrip("=")


def parse_oauth_state(state: str | None) -> dict[str, Any]:
    """Decode short-lived OAuth callback state from the authorize URL."""
    if not state:
        return {}

    try:
        padded_state = state + ("=" * (-len(state) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded_state))
    except (ValueError, TypeError):
        return {}

    created_at = payload.get("created_at")
    if not isinstance(created_at, (int, float)):
        return {}

    if time.time() - created_at > OAUTH_STATE_MAX_AGE_SECONDS:
        return {}

    return payload


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
    Return the local/deployed app URL Supabase should redirect back to.

    Configure APP_URL in .streamlit/secrets.toml for deployed environments.
    """
    current_url = getattr(st.context, "url", "") or ""
    if current_url:
        parsed = urlparse(current_url)
        current_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    configured_url = _get_secret("APP_URL") or _get_secret("STREAMLIT_APP_URL")
    if (
        current_url
        and configured_url
        and _is_local_url(configured_url)
        and not _is_local_url(current_url)
    ):
        url = current_url
    else:
        url = configured_url or current_url

    return _validate_url(url or "http://localhost:8501", "APP_URL")


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
    params = {
        "auth_code": auth_code,
        "redirect_to": get_auth_redirect_url(),
    }
    if code_verifier:
        params["code_verifier"] = code_verifier

    return client.auth.exchange_code_for_session(params)


def sign_in_with_google() -> dict[str, Any]:
    """
    Initiate Google OAuth sign in flow.
    Returns the OAuth response with URL for redirecting user to Google.
    """
    try:
        from supabase_auth.helpers import generate_pkce_challenge, generate_pkce_verifier

        url, _ = get_supabase_config()
        verifier = generate_pkce_verifier()
        challenge = generate_pkce_challenge(verifier)
        state = _encode_oauth_state(
            {
                "code_verifier": verifier,
                "created_at": time.time(),
            }
        )
        query = urlencode(
            {
                "provider": "google",
                "redirect_to": get_auth_redirect_url(),
                "code_challenge": challenge,
                "code_challenge_method": "s256",
                "state": state,
            }
        )
        return {
            "url": f"{url}/auth/v1/authorize?{query}",
            "code_verifier": verifier,
        }
    except Exception as exc:
        raise SupabaseConfigError(f"Google OAuth failed: {str(exc)}") from exc
