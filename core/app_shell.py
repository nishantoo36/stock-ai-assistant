"""Top-level app orchestration."""

from __future__ import annotations

import streamlit as st

from core.session_state import init_session_state, sync_url_state
from ui.auth.session import (
    is_logged_in,
    persist_current_auth_session,
    render_login_section,
    restore_auth_session,
)
from ui.auth.callback import handle_auth_callback
from ui.shell.header import render_header
from ui.home.page import render_homepage
from ui.search.components import render_no_results, render_result_cards, render_search_bar
from ui.stock.view import render_stock_view
from utils.platform.styles import inject_css


def render_app() -> None:
    handle_auth_callback()
    inject_css()
    restore_auth_session()
    persist_current_auth_session()
    init_session_state()
    sync_url_state()

    render_header()

    if st.session_state.get("show_login") and not is_logged_in():
        render_login_section()

    currency_option = render_search_bar()
    render_no_results()
    render_result_cards()
    render_homepage()

    if st.session_state.selected_ticker:
        render_stock_view(currency_option)
