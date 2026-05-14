import numpy as np
import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Internal modules ──────────────────────────────────────────────────────────
from utils.styles         import inject_css
from utils.data           import load_stock_info, load_chart_data, load_analysis_data, load_news
from utils.indicators     import get_last_close
from utils.forex          import get_currency_symbol, convert_price
from utils.recommendation import generate_recommendation
from ui.search            import render_search_bar, render_no_results, render_result_cards, render_change_stock_button
from ui.chart             import render_period_selector, render_chart
from ui.analysis          import (
    render_rate_limit_error, render_stock_header, render_price,
    render_metric_cards, render_score_bar, render_ai_summary,
    render_signal_breakdown, render_news, render_education, render_cta,
)

# ── Inject CSS ────────────────────────────────────────────────────────────────
inject_css()

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in {
    "selected_ticker":   None,
    "company_name":      None,
    "search_results":    [],
    "chart_period":      "1D",
    "search_no_results": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── App header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-header-icon">📈</div>
    <div>
        <h1>AI Investment Assistant</h1>
        <p>Multi-signal stock analysis · Beginner friendly · Live data</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Search bar (returns selected currency) ────────────────────────────────────
currency_option = render_search_bar()

# ── Search results / no-results feedback ─────────────────────────────────────
render_no_results()
render_result_cards()
render_change_stock_button()

# ── Main analysis ─────────────────────────────────────────────────────────────
if st.session_state.selected_ticker:
    ticker       = st.session_state.selected_ticker
    company_name = st.session_state.company_name

    # Period selector
    period = render_period_selector()

    # Load data
    with st.spinner("Loading data and running analysis..."):
        try:
            info = load_stock_info(ticker)
        except Exception:
            render_rate_limit_error()
            st.stop()

        orig_curr   = info.get("currency", "USD")
        df_chart    = load_chart_data(ticker, period)
        df_analysis = load_analysis_data(ticker)
        news        = load_news(company_name)

    if df_analysis.empty and df_chart.empty:
        st.error("No market data available for this stock.")
        st.stop()

    if df_analysis.empty or len(df_analysis) < 10:
        df_analysis = df_chart

    # Price + currency conversion
    raw_price           = get_last_close(df_analysis, info)
    curr_price, fx_rate = convert_price(raw_price, orig_curr, currency_option)
    disp_curr           = currency_option if currency_option != "Original" else orig_curr
    sym                 = get_currency_symbol(disp_curr)

    # Day change (both values in display currency)
    raw_prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
    if raw_prev and not np.isnan(curr_price):
        prev_conv   = float(raw_prev) * fx_rate
        day_chg     = curr_price - prev_conv
        day_chg_pct = (day_chg / prev_conv) * 100
    else:
        day_chg = day_chg_pct = None

    # Run analysis engine
    (rec, conf, risk, summary, signals,
     news_label, news_detail,
     rsi, sma20, sma50, mom5, score_pct
    ) = generate_recommendation(df_analysis, info, news)

    # Render
    render_stock_header(company_name, ticker)
    render_price(curr_price, day_chg, day_chg_pct, sym)
    render_metric_cards(rec, conf, risk)

    st.markdown("<br>", unsafe_allow_html=True)
    render_score_bar(score_pct)
    st.markdown("<hr>", unsafe_allow_html=True)

    render_chart(df_chart, df_analysis, period, disp_curr)

    render_ai_summary(rec, summary)
    st.markdown("<br>", unsafe_allow_html=True)

    render_signal_breakdown(signals, rsi, mom5, sym, info)
    render_news(news_label, news_detail)
    render_education()
    render_cta()