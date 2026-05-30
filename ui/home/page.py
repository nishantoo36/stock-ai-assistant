import streamlit as st

from services.homepage_market_data import (
    QUICK_TOPIC_KEYS,
    get_ai_picks,
    get_homepage_market_data,
    get_live_market_quote,
    get_quick_topic_stocks,
)
from ui.home.markets import COUNTRY_MARKETS
from ui.home.sections import (
    render_education_cards,
    render_homepage_styles,
    render_market_snapshot,
    render_quick_topic_buttons,
    render_stock_discovery,
)
from utils.platform.common import query_param as _query_param
from utils.platform.i18n import t


def _set_query_param(name: str, value: str | None) -> None:
    current = _query_param(st.query_params, name)
    if value:
        if current != value:
            st.query_params[name] = value
    elif current is not None:
        st.query_params.pop(name, None)


def set_quick_topic(topic: str) -> None:
    st.session_state.quick_topic = topic
    st.session_state.topic_url_value = topic if topic != "trending" else None
    st.session_state.search_results = []
    st.session_state.search_no_results = None
    st.session_state.reset_search_query = True
    st.session_state.last_search_query = ""
    st.query_params.pop("q", None)
    st.query_params.pop("stock", None)
    st.query_params.pop("company", None)
    _set_query_param("topic", topic if topic != "trending" else None)
    st.rerun()


def _countries_from_query(country_options: list[str]) -> list[str]:
    countries_value = _query_param(st.query_params, "countries")
    if st.session_state.get("countries_url_value") == countries_value:
        return st.session_state.selected_countries

    selected = []
    if countries_value:
        selected = [
            country
            for country in countries_value.split(",")
            if country in country_options
        ][:5]

    st.session_state.selected_countries = selected
    st.session_state.countries_url_value = countries_value
    return selected


def _sync_countries_to_url(selected_countries: list[str]) -> None:
    countries_value = ",".join(selected_countries[:5])
    _set_query_param("countries", countries_value or None)
    st.session_state.countries_url_value = countries_value or None


def render_homepage() -> None:
    if st.session_state.selected_ticker or st.session_state.search_results:
        return

    render_homepage_styles()

    st.markdown(f"### 🚀 {t('homepage.quick_explore')}")
    country_options = list(COUNTRY_MARKETS.keys())
    _countries_from_query(country_options)
    selected_countries = st.multiselect(
        t("homepage.country"),
        country_options,
        format_func=lambda country: COUNTRY_MARKETS[country]["label"],
        key="selected_countries",
        placeholder=t("homepage.country_placeholder"),
        max_selections=5,
    )
    _sync_countries_to_url(selected_countries)
    render_quick_topic_buttons(set_quick_topic)

    market_indexes, trending_stocks = get_homepage_market_data(selected_countries)
    quick_topic = st.session_state.get("quick_topic", "trending")
    display_stocks = (
        trending_stocks
        if quick_topic == "trending"
        else get_quick_topic_stocks(quick_topic, selected_countries)
    )

    render_market_snapshot(
        selected_countries,
        market_indexes,
        get_live_market_quote,
    )
    render_stock_discovery(
        quick_topic,
        selected_countries,
        display_stocks,
        get_ai_picks(selected_countries),
        get_live_market_quote,
    )
    render_education_cards()
