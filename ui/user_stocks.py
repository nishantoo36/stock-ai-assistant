"""
Saved searches and watchlist actions for authenticated users.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from ui.auth import (
    get_access_token,
    get_current_user,
    is_logged_in,
    render_login_required_dialog,
)
from utils.i18n import t
from utils.supabase_client import SupabaseConfigError, get_user_supabase_client

PAGE_SIZE = 30


def _user_client():
    return get_user_supabase_client(get_access_token())


def _user_id() -> str | None:
    return get_current_user().get("id")


def save_searched_stock(ticker: str, company_name: str | None) -> None:
    user_id = _user_id()
    if not user_id:
        raise RuntimeError(t("auth.login_required"))

    _user_client().table("saved_searches").insert({
        "user_id": user_id,
        "ticker": ticker,
        "company_name": company_name,
    }).execute()


def remove_saved_stock(ticker: str) -> None:
    user_id = _user_id()
    if not user_id:
        raise RuntimeError(t("auth.login_required"))

    (
        _user_client()
        .table("saved_searches")
        .delete()
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .execute()
    )


def is_saved_stock(ticker: str) -> bool:
    user_id = _user_id()
    if not user_id:
        return False

    response = (
        _user_client()
        .table("saved_searches")
        .select("ticker")
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def add_to_watchlist(ticker: str, company_name: str | None) -> None:
    user_id = _user_id()
    if not user_id:
        raise RuntimeError(t("auth.login_required"))

    _user_client().table("watchlists").upsert(
        {
            "user_id": user_id,
            "ticker": ticker,
            "company_name": company_name,
        },
        on_conflict="user_id,ticker",
    ).execute()


def remove_from_watchlist(ticker: str) -> None:
    user_id = _user_id()
    if not user_id:
        raise RuntimeError(t("auth.login_required"))

    (
        _user_client()
        .table("watchlists")
        .delete()
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .execute()
    )


def is_in_watchlist(ticker: str) -> bool:
    user_id = _user_id()
    if not user_id:
        return False

    response = (
        _user_client()
        .table("watchlists")
        .select("ticker")
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def render_stock_actions(ticker: str, company_name: str | None) -> None:
    if not is_logged_in():
        if st.button(t("user_stocks.add_watchlist"), key=f"login_to_save_{ticker}", use_container_width=True):
            render_login_required_dialog()
        return

    try:
        saved = is_saved_stock(ticker)
        watched = is_in_watchlist(ticker)
    except (SupabaseConfigError, Exception) as exc:
        st.error(t("user_stocks.load_watchlist_error", error=str(exc)))
        return

    watch_label = t("user_stocks.remove_watchlist") if watched else t("user_stocks.add_watchlist")
    if st.button(watch_label, use_container_width=True, key=f"watchlist_{ticker}"):
        try:
            if watched:
                remove_from_watchlist(ticker)
                st.success(t("user_stocks.watchlist_removed"))
            else:
                add_to_watchlist(ticker, company_name)
                st.success(t("user_stocks.watchlist_added"))
            st.rerun()
        except (SupabaseConfigError, Exception) as exc:
            st.error(t("user_stocks.watchlist_error", error=str(exc)))


def render_watchlist_preview(limit: int = 8) -> None:
    if not is_logged_in():
        return

    with st.expander(t("user_stocks.my_watchlist"), expanded=False):
        try:
            response = (
                _user_client()
                .table("watchlists")
                .select("ticker, company_name, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        except Exception as exc:
            st.error(t("user_stocks.load_watchlist_error", error=str(exc)))
            return

        rows = response.data or []
        if not rows:
            st.caption(t("user_stocks.empty_watchlist"))
            return

        for row in rows:
            name = row.get("company_name") or row.get("ticker")
            st.markdown(f"- **{name}** `{row.get('ticker')}`")


def _load_watchlist_page(page: int, page_size: int = PAGE_SIZE) -> tuple[list[dict], bool]:
    offset = max(page, 0) * page_size
    response = (
        _user_client()
        .table("watchlists")
        .select("ticker, company_name, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data or []
    return rows[:page_size], len(rows) > page_size


def _open_stock(row: dict) -> None:
    st.session_state.selected_ticker = row.get("ticker")
    st.session_state.company_name = row.get("company_name") or row.get("ticker")
    st.rerun()


def _render_watchlist_page() -> None:
    page_key = "watchlist_page"
    st.session_state.setdefault(page_key, 0)
    page = st.session_state[page_key]

    try:
        rows, has_next = _load_watchlist_page(page)
    except Exception as exc:
        st.error(t("user_stocks.load_watchlist_error", error=str(exc)))
        return

    if not rows:
        st.caption(t("user_stocks.empty_watchlist"))
        return

    for index, row in enumerate(rows):
        name = escape(row.get("company_name") or row.get("ticker") or "")
        ticker = escape(row.get("ticker") or "")
        created_at = escape(str(row.get("created_at") or "")[:10])
        col_info, col_action = st.columns([4, 1])
        with col_info:
            st.markdown(
                f"<div class='list-row-title'>{name}</div>"
                f"<div class='list-row-meta'>{ticker} · {created_at}</div>",
                unsafe_allow_html=True,
            )
        with col_action:
            if st.button(t("common.open"), key=f"open_watchlist_{page}_{index}", use_container_width=True):
                _open_stock(row)
        st.markdown("<div class='list-row-divider'></div>", unsafe_allow_html=True)

    prev_col, page_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if st.button(t("common.previous"), disabled=page == 0, use_container_width=True, key="watchlist_prev"):
            st.session_state[page_key] = max(page - 1, 0)
            st.rerun()
    with page_col:
        st.markdown(
            f"<div style='text-align:center;font-size:0.95rem;color:var(--muted)'>"
            f"{t('common.page', page=page + 1)}</div>",
            unsafe_allow_html=True,
        )
    with next_col:
        if st.button(t("common.next"), disabled=not has_next, use_container_width=True, key="watchlist_next"):
            st.session_state[page_key] = page + 1
            st.rerun()


def render_watchlist_dialog() -> None:
    @st.dialog(t("user_stocks.my_watchlist"), width="large")
    def _dialog() -> None:
        _render_watchlist_page()

    _dialog()


def render_watchlist_button() -> None:
    if not is_logged_in():
        return

    if st.button(t("user_stocks.my_watchlist"), key="open_watchlist_dialog", use_container_width=True):
        render_watchlist_dialog()
