"""Authenticated-user helpers shared by UI modules."""

from __future__ import annotations

from utils.platform.supabase_client import get_user_supabase_client


def current_user_id() -> str | None:
    from ui.auth.session import get_current_user

    return get_current_user().get("id")


def current_user_client():
    from ui.auth.session import get_access_token

    return get_user_supabase_client(get_access_token())
