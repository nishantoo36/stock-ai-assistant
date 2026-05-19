"""
Supabase client helpers.

The public anon/publishable key is safe to use from Streamlit, while the
service-role key must never be placed in st.secrets for this app.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import streamlit as st


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

    url = _get_secret("APP_URL") or _get_secret("STREAMLIT_APP_URL") or current_url
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


def exchange_oauth_code(auth_code: str) -> Any:
    """Exchange a Supabase OAuth callback code for an auth session."""
    client = get_public_supabase_client()
    return client.auth.exchange_code_for_session(
        {
            "auth_code": auth_code,
            "redirect_to": get_auth_redirect_url(),
        }
    )


def sign_in_with_google() -> dict[str, Any]:
    """
    Initiate Google OAuth sign in flow.
    Returns the OAuth response with URL for redirecting user to Google.
    """
    try:
        client = get_public_supabase_client()
        response = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": get_auth_redirect_url(),
            }
        })
        return response
    except Exception as exc:
        raise SupabaseConfigError(f"Google OAuth failed: {str(exc)}") from exc


def send_phone_otp(phone: str) -> Any:
    """Send a Supabase phone OTP to an E.164 phone number."""
    try:
        client = get_public_supabase_client()
        return client.auth.sign_in_with_otp(
            {
                "phone": phone,
                "options": {
                    "channel": "sms",
                    "should_create_user": True,
                },
            }
        )
    except Exception as exc:
        raise SupabaseConfigError(f"Phone sign-in failed: {str(exc)}") from exc


def verify_phone_otp(phone: str, token: str) -> Any:
    """Verify a Supabase phone OTP and return an auth session."""
    try:
        client = get_public_supabase_client()
        return client.auth.verify_otp(
            {
                "phone": phone,
                "token": token,
                "type": "sms",
            }
        )
    except Exception as exc:
        raise SupabaseConfigError(f"Phone verification failed: {str(exc)}") from exc
