"""Saved-search and watchlist persistence."""

from __future__ import annotations

from services.user_context import current_user_client, current_user_id
from utils.platform.i18n import t


def require_user_id() -> str:
    user_id = current_user_id()
    if not user_id:
        raise RuntimeError(t("auth.login_required"))
    return user_id


def save_searched_stock(ticker: str, company_name: str | None) -> None:
    user_id = require_user_id()
    current_user_client().table("saved_searches").insert({
        "user_id": user_id,
        "ticker": ticker,
        "company_name": company_name,
    }).execute()


def remove_saved_stock(ticker: str) -> None:
    user_id = require_user_id()
    (
        current_user_client()
        .table("saved_searches")
        .delete()
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .execute()
    )


def is_saved_stock(ticker: str) -> bool:
    user_id = current_user_id()
    if not user_id:
        return False

    response = (
        current_user_client()
        .table("saved_searches")
        .select("ticker")
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def add_to_watchlist(ticker: str, company_name: str | None) -> None:
    user_id = require_user_id()
    current_user_client().table("watchlists").upsert(
        {
            "user_id": user_id,
            "ticker": ticker,
            "company_name": company_name,
        },
        on_conflict="user_id,ticker",
    ).execute()


def remove_from_watchlist(ticker: str) -> None:
    user_id = require_user_id()
    (
        current_user_client()
        .table("watchlists")
        .delete()
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .execute()
    )


def is_in_watchlist(ticker: str) -> bool:
    user_id = current_user_id()
    if not user_id:
        return False

    response = (
        current_user_client()
        .table("watchlists")
        .select("ticker")
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def load_watchlist(limit: int) -> list[dict]:
    response = (
        current_user_client()
        .table("watchlists")
        .select("ticker, company_name, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def load_watchlist_page(page: int, page_size: int) -> tuple[list[dict], bool]:
    offset = max(page, 0) * page_size
    response = (
        current_user_client()
        .table("watchlists")
        .select("ticker, company_name, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data or []
    return rows[:page_size], len(rows) > page_size
