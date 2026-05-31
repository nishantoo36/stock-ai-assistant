"""
Stock analysis view — loaded when a ticker is selected.
Handles data loading, price/change calculation, and all rendering.
"""

import numpy as np
import streamlit as st

from utils.data.market_data           import load_stock_info, load_chart_data, load_analysis_data, load_news, load_live_price
from utils.platform.i18n           import t
from utils.analysis.recommendation import generate_recommendation
from utils.analysis.timesfm_forecast import build_timesfm_forecast
from ui.stock.chart             import CHART_PERIODS, render_chart
from ui.user.alerts            import render_alert_form
from ui.stock.analysis          import (
    render_stock_header, render_price,
    render_score_bar, render_ai_summary,
    render_signal_breakdown, render_news, render_education, render_cta,
)
from ui.stock.forecast           import (
    render_ai_outlook_summary,
    render_forecast_horizon_selector,
    render_timesfm_forecast,
)
from ui.stock.state   import (
    analysis_frame, build_display_price_state, has_price_data,
)
from ui.user.stocks       import render_stock_actions


def render_stock_view(currency_option: str) -> None:
    """Render the full analysis panel for the currently selected ticker."""
    ticker       = st.session_state.selected_ticker
    company_name = st.session_state.company_name

    if st.session_state.chart_period not in CHART_PERIODS:
        st.session_state.chart_period = "1D"
    period = st.session_state.chart_period

    with st.spinner(t("stock_view.loading_analysis")):
        try:
            info = load_stock_info(ticker)
        except Exception as exc:
            info = {"currency": "USD"}
            st.warning(
                f"{t('stock_view.metadata_unavailable')}\n\n"
                f"`{type(exc).__name__}: {exc}`"
            )

        orig_curr   = info.get("currency", "USD")
        df_chart    = load_chart_data(ticker, period)
        df_analysis = load_analysis_data(ticker)
        news        = load_news(company_name, ticker)
        live        = load_live_price(ticker)

    # ── Dynamic guard: no usable price data from yfinance ────────────────────
    # Catches dark pools, delisted tickers, restricted feeds — any exchange
    # that yfinance can't provide OHLCV data for, regardless of suffix.
    if not has_price_data(df_analysis) and not has_price_data(df_chart):
        st.warning(
            f"⚠️ {t('stock_view.no_price_data_title', ticker=ticker)}\n\n"
            f"{t('stock_view.no_price_data_help')}"
        )
        st.stop()

    df_analysis = analysis_frame(df_analysis, df_chart)
    price_state = build_display_price_state(
        df_chart,
        df_analysis,
        info,
        live,
        orig_curr,
        currency_option,
        period,
    )

    # Render
    st.markdown("<hr>", unsafe_allow_html=True)
    title_col, actions_col = st.columns([1.35, 1.25], vertical_alignment="center")
    with title_col:
        render_stock_header(company_name, ticker)
    with actions_col:
        save_col, alert_col = st.columns([1, 1], vertical_alignment="center")
        with save_col:
            render_stock_actions(ticker, company_name)
        with alert_col:
            alert_price = None if np.isnan(price_state.current_price) else price_state.current_price
            render_alert_form(ticker, company_name, alert_price)
    render_price(
        price_state.current_price,
        price_state.day_change,
        price_state.day_change_pct,
        price_state.currency_symbol,
        period,
    )
    forecast_horizon = render_forecast_horizon_selector()

    with st.spinner(t("forecast.analyzing")):
        timesfm_forecast = build_timesfm_forecast(df_analysis, news, horizon=forecast_horizon)
        (rec, conf, risk, summary, signals,
         news_label, news_detail,
         rsi, sma20, sma50, mom5, score_pct
        ) = generate_recommendation(df_analysis, info, news, forecast=timesfm_forecast)

    render_ai_outlook_summary(
        rec,
        conf,
        risk,
        timesfm_forecast,
        orig_curr,
        price_state.display_currency,
        price_state.currency_symbol,
    )
    render_score_bar(score_pct)
    render_timesfm_forecast(
        timesfm_forecast,
        orig_curr,
        price_state.display_currency,
        price_state.currency_symbol,
    )
    render_ai_summary(rec, summary)
    st.markdown("<br>", unsafe_allow_html=True)

    render_chart(
        df_chart,
        df_analysis,
        period,
        price_state.display_currency,
        previous_close=price_state.previous_close,
        exchange_timezone=info.get("exchangeTimezoneName"),
        stock_info=info,
        period_change=price_state.day_change,
    )

    render_signal_breakdown(signals, rsi, mom5, price_state.currency_symbol, info)
    render_news(news_label, news_detail)
    render_education()
    render_cta()
