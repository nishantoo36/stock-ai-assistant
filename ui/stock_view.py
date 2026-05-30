"""
Stock analysis view — loaded when a ticker is selected.
Handles data loading, price/change calculation, and all rendering.
"""

import numpy as np
import pandas as pd
import streamlit as st

from utils.data           import load_stock_info, load_chart_data, load_analysis_data, load_news, load_live_price
from utils.indicators     import get_last_close
from utils.forex          import get_currency_symbol, convert_price
from utils.i18n           import t
from utils.recommendation import generate_recommendation
from utils.timesfm_forecast import build_timesfm_forecast
from ui.chart             import CHART_PERIODS, render_period_selector, render_chart
from ui.alerts            import render_alert_form
from ui.analysis          import (
    render_rate_limit_error, render_stock_header, render_price,
    render_metric_cards, render_score_bar, render_ai_summary,
    render_signal_breakdown, render_news, render_education, render_cta,
)
from ui.forecast           import render_timesfm_forecast
from ui.user_stocks       import render_stock_actions


def _has_price_data(df: pd.DataFrame) -> bool:
    """Return True only if the DataFrame has a usable Close column with real values."""
    return (
        df is not None
        and not df.empty
        and "Close" in df.columns
        and df["Close"].notna().any()
    )


def _calc_period_change(
    df_chart: pd.DataFrame,
    curr_price: float,
    fx_rate: float,
    info: dict,
    live: dict,
    period: str = "1D",
) -> tuple:
    """
    Return (absolute_change, pct_change) for the selected chart period.
    - 1D: always uses previous_close (yesterday close → now = standard today % change)
    - Other periods: uses first candle of chart data (period start → now)
    % is currency-neutral — fx_rate cancels in the ratio.
    """
    if np.isnan(curr_price):
        return None, None

    def _chg(base_raw):
        base = float(base_raw) * fx_rate
        if base > 0:
            c = curr_price - base
            return c, (c / base) * 100
        return None, None

    # 1D: use previous_close so % matches "today's change" shown on Google/Bloomberg
    if period == "1D":
        prev = live.get("previous_close") or info.get("previousClose") or info.get("regularMarketPreviousClose")
        if prev:
            return _chg(prev)
        return None, None

    # Multi-day periods: use first candle of chart (period open → now)
    clean = df_chart.dropna(subset=["Close"]) if not df_chart.empty else pd.DataFrame()
    if len(clean) >= 2:
        first_raw = float(clean["Close"].iloc[0])
        if not np.isnan(first_raw) and first_raw > 0:
            return _chg(first_raw)

    # Fallback for multi-day when chart empty
    prev = live.get("previous_close") or info.get("previousClose") or info.get("regularMarketPreviousClose")
    if prev:
        return _chg(prev)

    return None, None


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
        except Exception:
            render_rate_limit_error()
            st.stop()

        orig_curr   = info.get("currency", "USD")
        df_chart    = load_chart_data(ticker, period)
        df_analysis = load_analysis_data(ticker)
        news        = load_news(company_name, ticker)
        live        = load_live_price(ticker)

    # ── Dynamic guard: no usable price data from yfinance ────────────────────
    # Catches dark pools, delisted tickers, restricted feeds — any exchange
    # that yfinance can't provide OHLCV data for, regardless of suffix.
    if not _has_price_data(df_analysis) and not _has_price_data(df_chart):
        st.warning(
            f"⚠️ {t('stock_view.no_price_data_title', ticker=ticker)}\n\n"
            f"{t('stock_view.no_price_data_help')}"
        )
        st.stop()

    if df_analysis.empty or len(df_analysis) < 10:
        df_analysis = df_chart

    # Live price first; fall back to historical df only when unavailable
    raw_price = live.get("price")
    if not raw_price or np.isnan(float(raw_price)):
        raw_price = get_last_close(df_analysis, info)

    curr_price, fx_rate = convert_price(float(raw_price), orig_curr, currency_option)
    disp_curr           = currency_option if currency_option != "CurrencySelector" else orig_curr
    sym                 = get_currency_symbol(disp_curr)

    day_chg, day_chg_pct = _calc_period_change(df_chart, curr_price, fx_rate, info, live, period)
    prev_raw = live.get("previous_close") or info.get("previousClose") or info.get("regularMarketPreviousClose")
    previous_close = None
    if prev_raw:
        previous_close, _ = convert_price(float(prev_raw), orig_curr, currency_option)

    # Analysis
    (rec, conf, risk, summary, signals,
     news_label, news_detail,
     rsi, sma20, sma50, mom5, score_pct
    ) = generate_recommendation(df_analysis, info, news)
    timesfm_forecast = build_timesfm_forecast(df_analysis, news)

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
            render_alert_form(ticker, company_name, None if np.isnan(curr_price) else curr_price)
    render_price(curr_price, day_chg, day_chg_pct, sym, period)
    render_metric_cards(rec, conf, risk)

    st.markdown("<br>", unsafe_allow_html=True)
    render_score_bar(score_pct)
    st.markdown("<hr>", unsafe_allow_html=True)

    render_chart(
        df_chart,
        df_analysis,
        period,
        disp_curr,
        previous_close=previous_close,
        exchange_timezone=info.get("exchangeTimezoneName"),
    )
    render_period_selector()
    render_timesfm_forecast(timesfm_forecast, orig_curr, disp_curr, sym)
    render_ai_summary(rec, summary)
    st.markdown("<br>", unsafe_allow_html=True)

    render_signal_breakdown(signals, rsi, mom5, sym, info)
    render_news(news_label, news_detail)
    render_education()
    render_cta()
