import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from ui.auth import (
    LOGOUT_FLAG,
    is_logged_in,
    persist_current_auth_session,
    restore_auth_session,
    store_auth_session,
)


def _attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _query_param(query_params, name: str) -> str | None:
    value = query_params.get(name)
    if isinstance(value, list):
        return value[0] if value else None
    return value


# ── Handle Supabase auth callbacks ────────────────────────────────────────────
def _handle_auth_callback() -> None:
    """Process auth tokens or OAuth codes from Supabase callback links."""
    query_params = st.query_params
    if not query_params:
        return

    auth_error = _query_param(query_params, "error_description") or _query_param(
        query_params, "error"
    )
    if auth_error:
        st.error(f"Authentication failed: {auth_error}")
        st.query_params.clear()
        return

    access_token = _query_param(query_params, "access_token")
    refresh_token = _query_param(query_params, "refresh_token")
    auth_code = _query_param(query_params, "code")

    if auth_code:
        try:
            from utils.supabase_client import exchange_oauth_code

            response = exchange_oauth_code(auth_code)
            if store_auth_session(response):
                st.query_params.clear()
                st.rerun()
        except Exception as exc:
            st.error(f"Authentication failed: {exc}")
            st.query_params.clear()
        return

    if access_token:
        st.session_state.pop(LOGOUT_FLAG, None)
        st.session_state.auth_session = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        # Try to get user info from the token
        try:
            from utils.supabase_client import get_user_supabase_client
            client = get_user_supabase_client(access_token)
            user_info = client.auth.get_user(access_token)
            if user_info:
                st.session_state.auth_user = {
                    "id": _attr(user_info.user, "id", ""),
                    "email": _attr(user_info.user, "email", ""),
                    "phone": _attr(user_info.user, "phone", ""),
                }
        except Exception:
            pass  # Continue anyway, user will be authenticated
        
        # Clear the query parameters
        st.query_params.clear()
        st.rerun()

_handle_auth_callback()

from utils.styles  import inject_css
from utils.i18n    import t, set_language, get_current_language, get_available_languages, get_language_flag
from ui.auth       import render_auth_panel, render_login_section
from ui.alerts     import render_notifications_button
from ui.search     import render_search_bar, render_no_results, render_result_cards, render_change_stock_button
from ui.stock_view import render_stock_view
from ui.user_stocks import render_watchlist_button

inject_css()
restore_auth_session()
persist_current_auth_session()

# ── Always-visible language selector ─────────────────────────────────────────
def render_language_selector() -> None:
    available_langs = get_available_languages()
    lang_options = [
        (f"{get_language_flag(code)} {code.upper()}", code)
        for code in available_langs
    ]
    current_lang = get_current_language()
    current_display = next(
        (display for display, code in lang_options if code == current_lang),
        lang_options[0][0]
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


# ── Session state defaults ────────────────────────────────────────────────────
for key, default in {
    "selected_ticker":   None,
    "company_name":      None,
    "search_results":    [],
    "chart_period":      "1D",
    "search_no_results": None,
    "show_login":        False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if _query_param(st.query_params, "auth"):
    st.query_params.pop("auth", None)

# ── Header ────────────────────────────────────────────────────────────────────
header_ratio = [1.05, 1.65] if is_logged_in() else [1.45, 1]
header_col, action_col = st.columns(header_ratio, vertical_alignment="center")
with header_col:
    st.markdown("""
    <div class="app-header">
        <div class="app-header-icon">📈</div>
        <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
    </div>
    """.format(title=t("app.title"), subtitle=t("app.subtitle")), unsafe_allow_html=True)

with action_col:
    if is_logged_in():
        lang_col, watch_col, notif_col, account_col = st.columns([1.15, 1.15, 1.15, 1.0])
        with lang_col:
            render_language_selector()
        with watch_col:
            render_watchlist_button()
        with notif_col:
            render_notifications_button()
        with account_col:
            render_auth_panel()
    else:
        lang_col, account_col = st.columns([1.2, 1])
        with lang_col:
            render_language_selector()
        with account_col:
            render_auth_panel()

if st.session_state.get("show_login") and not is_logged_in():
    render_login_section()

# ── Search ────────────────────────────────────────────────────────────────────
currency_option = render_search_bar()
render_no_results()
render_result_cards()
render_change_stock_button()

# ── Stock view ────────────────────────────────────────────────────────────────
if st.session_state.selected_ticker:
    render_stock_view(currency_option)
