import logging
import os

import streamlit as st


def _setup_logging() -> None:
    level_name = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
    logging.getLogger("streamlit").setLevel(logging.WARNING)


_setup_logging()
logger = logging.getLogger(__name__)

# Page config must be the first Streamlit call.
st.set_page_config(
    page_title="AI Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from ui.auth import (
    is_logged_in,
    persist_current_auth_session,
    render_login_section,
    restore_auth_session,
)
from ui.auth_callback import handle_auth_callback
from ui.header import render_header
from ui.homepage import QUICK_TOPIC_KEYS, render_homepage
from ui.search import (
    _execute_search,
    render_no_results,
    render_result_cards,
    render_search_bar,
)
from ui.stock_view import render_stock_view
from utils.common import query_param
from utils.styles import inject_css


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
        previous = st.session_state.get("selected_ticker")
        if st.session_state.selected_ticker != url_stock:
            st.session_state.selected_ticker = url_stock
            st.session_state.company_name = url_company or url_stock
            st.session_state.search_results = []
            st.session_state.search_no_results = None
            logger.info(
                "Selected stock synced from URL: %s -> %s",
                previous,
                url_stock,
            )
        st.session_state.url_selected_stock = True
    elif st.session_state.get("url_selected_stock"):
        logger.info("Clearing URL-selected stock state")
        st.session_state.selected_ticker = None
        st.session_state.company_name = None
        st.session_state.search_results = []
        st.session_state.search_no_results = None
        st.session_state.url_selected_stock = False
    return url_stock


def sync_search_from_url(url_stock: str | None) -> None:
    url_search_query = query_param(st.query_params, "q")
    if not url_stock and url_search_query:
        if (
            st.session_state.get("last_search_query") != url_search_query
            or not st.session_state.search_results
        ):
            logger.info("Running search from URL query: %s", url_search_query)
            st.session_state.search_query = url_search_query
            _execute_search(url_search_query, update_url=False)
    elif (
        not url_stock
        and not url_search_query
        and st.session_state.get("last_search_query")
    ):
        logger.info("Clearing search state from URL reset")
        st.session_state.search_results = []
        st.session_state.search_no_results = None
        st.session_state.reset_search_query = True
        st.session_state.last_search_query = ""


def sync_topic_from_url() -> None:
    url_topic = query_param(st.query_params, "topic")
    if st.session_state.get("topic_url_value") != url_topic:
        logger.info("Syncing topic from URL: %s", url_topic)
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
        logger.info("Removed auth query parameter from URL")

    url_stock = sync_selected_stock_from_url()
    sync_search_from_url(url_stock)
    sync_topic_from_url()


def render_app() -> None:
    logger.info("App render start; query params=%s", dict(st.query_params))
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

    logger.info(
        "App render complete; logged_in=%s selected_ticker=%s search_results=%s",
        is_logged_in(),
        st.session_state.get("selected_ticker"),
        len(st.session_state.get("search_results", [])),
    )


render_app()
