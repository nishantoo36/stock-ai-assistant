"""Session defaults and URL synchronization for the Streamlit app."""

from __future__ import annotations

import streamlit as st

from utils.platform.common import query_param


SESSION_DEFAULTS = {
    "selected_ticker": None,
    "company_name": None,
    "search_results": [],
    "chart_period": "1D",
    "search_no_results": None,
    "show_login": False,
    "search_query": "",
    "last_search_query": "",
    "selected_countries": [],
    "countries_url_value": None,
    "quick_topic": "trending",
    "topic_url_value": None,
    "reset_search_query": False,
    "url_selected_stock": False,
}


def init_session_state() -> None:
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def sync_selected_stock_from_url() -> str | None:
    url_stock = query_param(st.query_params, "stock")
    url_company = query_param(st.query_params, "company")
    if url_stock:
        if st.session_state.selected_ticker != url_stock:
            st.session_state.selected_ticker = url_stock
            st.session_state.company_name = url_company or url_stock
            st.session_state.search_results = []
            st.session_state.search_no_results = None
        st.session_state.url_selected_stock = True
    elif st.session_state.get("url_selected_stock"):
        st.session_state.selected_ticker = None
        st.session_state.company_name = None
        st.session_state.search_results = []
        st.session_state.search_no_results = None
        st.session_state.url_selected_stock = False
    return url_stock


def sync_search_from_url(url_stock: str | None) -> None:
    from ui.search.components import _execute_search

    url_search_query = query_param(st.query_params, "q")
    if not url_stock and url_search_query:
        if (
            st.session_state.get("last_search_query") != url_search_query
            or not st.session_state.search_results
        ):
            st.session_state.search_query = url_search_query
            _execute_search(url_search_query, update_url=False)
    elif (
        not url_stock
        and not url_search_query
        and st.session_state.get("last_search_query")
    ):
        st.session_state.search_results = []
        st.session_state.search_no_results = None
        st.session_state.reset_search_query = True
        st.session_state.last_search_query = ""


def sync_topic_from_url() -> None:
    from services.homepage_market_data import QUICK_TOPIC_KEYS

    url_topic = query_param(st.query_params, "topic")
    if st.session_state.get("topic_url_value") != url_topic:
        st.session_state.quick_topic = (
            url_topic if url_topic in QUICK_TOPIC_KEYS else "trending"
        )
        st.session_state.topic_url_value = url_topic
        if st.session_state.quick_topic != "trending":
            st.session_state.search_results = []
            st.session_state.search_no_results = None
            st.session_state.search_query = ""
            st.session_state.last_search_query = ""


def sync_url_state() -> None:
    if query_param(st.query_params, "auth"):
        st.query_params.pop("auth", None)

    url_stock = sync_selected_stock_from_url()
    sync_search_from_url(url_stock)
    sync_topic_from_url()
