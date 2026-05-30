"""Reusable Streamlit sections for the homepage."""

from __future__ import annotations

import textwrap
from collections.abc import Callable

import streamlit as st

from utils.platform.common import select_stock
from utils.platform.i18n import t

MarketQuoteFn = Callable[[str, str], tuple[str, str]]


def short_reason(reason: str, width: int = 44) -> str:
    return textwrap.shorten(reason, width=width, placeholder="...")


def render_homepage_styles() -> None:
    st.markdown(
        """
        <style>
        .homepage-panel {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 18px;
            background: var(--surface);
        }
        .stock-card {
            display: block;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 12px;
            color: var(--text) !important;
            text-decoration: none !important;
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .stock-card:hover {
            border-color: var(--accent);
            color: var(--accent) !important;
        }
        .stock-card b {
            color: inherit;
        }
        .stock-card .positive {
            color: var(--green);
            font-family: var(--mono);
        }
        .stock-card .negative {
            color: var(--red);
            font-family: var(--mono);
        }
        .stock-card .neutral {
            color: var(--muted);
            font-family: var(--mono);
        }
        .ai-pick-link {
            display: block;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 10px;
            color: var(--text) !important;
            text-decoration: none !important;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .ai-pick-link:hover {
            border-color: var(--accent);
            color: var(--accent) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_quick_topic_buttons(on_topic_selected: Callable[[str], None]) -> None:
    q1, q2, q3, q4 = st.columns(4)

    with q1:
        if st.button(t("homepage.best_etfs"), use_container_width=True):
            on_topic_selected("best_etfs")

    with q2:
        if st.button(t("homepage.dividend_stocks"), use_container_width=True):
            on_topic_selected("dividend")

    with q3:
        if st.button(t("homepage.ai_stocks"), use_container_width=True):
            on_topic_selected("ai")

    with q4:
        if st.button(t("homepage.undervalued_stocks"), use_container_width=True):
            on_topic_selected("undervalued")


def render_market_snapshot(
    selected_countries: list[str],
    market_indexes: list[tuple[str, str, str]],
    quote_fn: MarketQuoteFn,
) -> None:
    snapshot_title = (
        f"### 📊 {t('homepage.global_market_snapshot')}"
        if not selected_countries
        else f"### 📊 {t('homepage.selected_country_markets')}"
    )
    st.markdown(snapshot_title)

    snapshot_cols = st.columns(4)
    for index, (label, symbol, market_currency) in enumerate(market_indexes):
        value, delta = quote_fn(symbol, market_currency)
        with snapshot_cols[index % 4]:
            if st.button(
                f"{label}\n{symbol} · {value} · {delta}",
                key=f"snapshot-market-{symbol}",
                use_container_width=True,
            ):
                select_stock(symbol, label)
                st.rerun()


def render_stock_discovery(
    quick_topic: str,
    selected_countries: list[str],
    display_stocks: list[tuple[str, str, str]],
    ai_picks: list[tuple[str, str, str]],
    quote_fn: MarketQuoteFn,
) -> None:
    left, right = st.columns([2, 1])

    with left:
        st.markdown(_stock_section_title(quick_topic, selected_countries))
        _render_stock_buttons(display_stocks, quote_fn)

    with right:
        st.markdown(f"### 🤖 {t('homepage.ai_picks_today')}")
        for ticker, company_name, reason in ai_picks:
            if st.button(
                f"{company_name}\n{ticker} · {short_reason(reason)}",
                key=f"homepage-ai-{ticker}",
                use_container_width=True,
            ):
                select_stock(ticker, company_name)
                st.rerun()


def render_education_cards() -> None:
    st.markdown(f"### 📚 {t('homepage.learn_before_invest')}")

    e1, e2, e3 = st.columns(3)
    with e1:
        with st.expander(t("homepage.analyze_stock_title")):
            st.markdown(t("homepage.analyze_stock_body"))
    with e2:
        with st.expander(t("homepage.etf_basics_title")):
            st.markdown(t("homepage.etf_basics_body"))
    with e3:
        with st.expander(t("homepage.risk_management_title")):
            st.markdown(t("homepage.risk_management_body"))


def _stock_section_title(quick_topic: str, selected_countries: list[str]) -> str:
    if quick_topic == "trending":
        return (
            f"### 🔥 {t('homepage.global_trending_stocks')}"
            if not selected_countries
            else f"### 🔥 {t('homepage.trending_stocks_by_country')}"
        )

    title_by_topic = {
        "best_etfs": t("homepage.best_etfs"),
        "dividend": t("homepage.dividend_stocks"),
        "ai": t("homepage.ai_stocks"),
        "undervalued": t("homepage.undervalued_stocks"),
    }
    return f"### 🔎 {title_by_topic.get(quick_topic, t('homepage.global_trending_stocks'))}"


def _render_stock_buttons(
    display_stocks: list[tuple[str, str, str]],
    quote_fn: MarketQuoteFn,
) -> None:
    visible_count = 0
    for stock, symbol, stock_currency in display_stocks:
        price, change = quote_fn(symbol, stock_currency)
        if price == t("common.unavailable"):
            continue

        if st.button(
            f"{stock}\n{symbol} · {price} · {change}",
            key=f"homepage-stock-{symbol}",
            use_container_width=True,
        ):
            select_stock(symbol, stock)
            st.rerun()
        visible_count += 1
        if visible_count >= 5:
            break
