"""
Search bar, result cards, and no-results feedback.
"""

import streamlit as st
from utils.data import do_search
from utils.i18n import t

TYPE_ICON = {
    "EQUITY": "📈", "ETF": "📊", "MUTUALFUND": "🏦",
    "INDEX": "📉", "CRYPTOCURRENCY": "₿",
}
EXCH_LABEL = {
    "NSI": "🇮🇳 NSE", "BSE": "🇮🇳 BSE", "NMS": "🇺🇸 NASDAQ",
    "NYQ": "🇺🇸 NYSE", "LSE": "🇬🇧 LSE", "TOR": "🇨🇦 TSX",
}

CURRENCY_OPTIONS = ["CurrencySelector", "USD", "EUR", "INR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SGD", "AED"]


def _format_currency_option(value: str) -> str:
    return t("search.currency_selector") if value == "CurrencySelector" else value


def render_search_bar() -> str:
    """Renders currency selector + search bar. Returns selected currency."""
    st.markdown("""
<style>
div[data-testid="stSelectbox"] > label { display: none !important; }
div[data-testid="stTextInput"]  > label { display: none !important; }
</style>
""", unsafe_allow_html=True)

    col_curr, col_search, col_btn = st.columns([2, 5, 1])
    with col_curr:
        currency_option = st.selectbox(
            t("search.currency_selector"),
            CURRENCY_OPTIONS,
            format_func=_format_currency_option,
            label_visibility="collapsed",
        )
    with col_search:
        search_text = st.text_input(
            t("search.search"),
            placeholder=t("search.placeholder"),
            label_visibility="collapsed",
        )
    with col_btn:
        search_clicked = st.button(t("search.button"), use_container_width=True)

    if search_clicked and search_text:
        _execute_search(search_text)

    return currency_option


def _execute_search(search_text: str) -> None:
    with st.spinner(t("search.searching")):
        try:
            res    = do_search(search_text)
            quotes = res.get("quotes", [])
            results = []
            for q in quotes[:8]:
                sym  = q.get("symbol", "")
                name = q.get("shortname") or q.get("longname") or sym
                exch = q.get("exchange", "")
                qt   = q.get("quoteType", "")
                if sym and name:
                    results.append({"ticker": sym, "name": name, "exchange": exch, "type": qt})

            st.session_state.search_results     = results
            st.session_state.selected_ticker    = None
            st.session_state.company_name       = None
            st.session_state.search_no_results  = search_text if not results else None
        except Exception as e:
            st.error(t("search.search_error", error=str(e)))


def render_no_results() -> None:
    q = st.session_state.get("search_no_results")
    if q and not st.session_state.search_results and not st.session_state.selected_ticker:
        st.markdown(
            f"<div style='margin-top:16px;padding:16px 20px;"
            f"background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);"
            f"border-left:3px solid #f59e0b;border-radius:12px;font-size:0.9rem'>"
            f"{t('search.no_results_title', query=q)}<br>"
            f"<span style='color:#94a3b8;font-size:0.82rem'>"
            f"{t('search.no_results_help')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_result_cards() -> None:
    if not st.session_state.search_results or st.session_state.selected_ticker:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:#94a3b8;font-size:0.82rem;font-weight:500;"
        f"letter-spacing:.06em;text-transform:uppercase;margin-bottom:12px'>"
        f"{t('search.select_stock')}</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for i, item in enumerate(st.session_state.search_results):
        icon  = TYPE_ICON.get(item["type"], "📌")
        exch  = EXCH_LABEL.get(item["exchange"], item["exchange"])
        label = f"{icon} **{item['name']}**\n\n`{item['ticker']}` · {exch}"
        with cols[i % 2]:
            if st.button(label, key=f"card_{i}", use_container_width=True):
                st.session_state.selected_ticker = item["ticker"]
                st.session_state.company_name    = item["name"]
                st.session_state.search_results  = []
                st.rerun()


def render_change_stock_button() -> None:
    if st.session_state.selected_ticker:
        if st.button(t("search.change_stock")):
            st.session_state.selected_ticker = None
            st.session_state.company_name    = None
            st.session_state.search_results  = []
            st.rerun()
