import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils.styles  import inject_css
from utils.i18n    import t, set_language, get_current_language, get_available_languages, get_language_flag
from ui.search     import render_search_bar, render_no_results, render_result_cards, render_change_stock_button
from ui.stock_view import render_stock_view

inject_css()

# ── Always-visible language selector ─────────────────────────────────────────
def render_language_selector() -> None:
    available_langs = get_available_languages()
    lang_options = [
        (f"{get_language_flag(code)} {name}", code)
        for code, name in available_langs.items()
    ]
    current_lang = get_current_language()
    current_display = next(
        (display for display, code in lang_options if code == current_lang),
        lang_options[0][0]
    )

    _, lang_col = st.columns([5, 2])
    with lang_col:
        st.markdown(
            f"<div style='color:#94a3b8;font-size:0.72rem;font-weight:600;"
            f"letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px'>"
            f"{t('common.language')}</div>",
            unsafe_allow_html=True,
        )
        selected_lang_display = st.selectbox(
            t("common.language"),
            [display for display, _ in lang_options],
            index=[display for display, _ in lang_options].index(current_display),
            key="language_selector",
            label_visibility="collapsed",
        )

    selected_lang_code = next(
        (code for display, code in lang_options if display == selected_lang_display),
        "en"
    )
    set_language(selected_lang_code)


render_language_selector()

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
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
</div>
""".format(title=t("app.title"), subtitle=t("app.subtitle")), unsafe_allow_html=True)

# ── Search ────────────────────────────────────────────────────────────────────
currency_option = render_search_bar()
render_no_results()
render_result_cards()
render_change_stock_button()

# ── Stock view ────────────────────────────────────────────────────────────────
if st.session_state.selected_ticker:
    render_stock_view(currency_option)
