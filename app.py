import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils.styles  import inject_css
from ui.search     import render_search_bar, render_no_results, render_result_cards, render_change_stock_button
from ui.stock_view import render_stock_view

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

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-header-icon">📈</div>
    <div>
        <h1>AI Investment Assistant</h1>
        <p>Multi-signal stock analysis · Beginner friendly · Live data</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Search ────────────────────────────────────────────────────────────────────
currency_option = render_search_bar()
render_no_results()
render_result_cards()
render_change_stock_button()

# ── Stock view ────────────────────────────────────────────────────────────────
if st.session_state.selected_ticker:
    render_stock_view(currency_option)