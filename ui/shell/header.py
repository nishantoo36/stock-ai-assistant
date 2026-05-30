import streamlit as st

from ui.user.alerts import render_notifications_button
from ui.auth.session import is_logged_in, render_auth_panel
from ui.user.stocks import render_watchlist_button
from utils.platform.i18n import (
    get_available_languages,
    get_current_language,
    get_language_flag,
    set_language,
    t,
)


def render_language_selector() -> None:
    available_langs = get_available_languages()
    lang_options = [
        (f"{get_language_flag(code)} {code.upper()}", code)
        for code in available_langs
    ]
    current_lang = get_current_language()
    current_display = next(
        (display for display, code in lang_options if code == current_lang),
        lang_options[0][0],
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
        "en",
    )
    set_language(selected_lang_code)


def render_header() -> None:
    header_ratio = [1.05, 1.65] if is_logged_in() else [1.45, 1]
    header_col, action_col = st.columns(header_ratio, vertical_alignment="center")
    with header_col:
        st.markdown(
            """
            <div class="app-header">
                <div class="app-header-icon">📈</div>
                <div>
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
            </div>
            """.format(title=t("app.title"), subtitle=t("app.subtitle")),
            unsafe_allow_html=True,
        )

    with action_col:
        if is_logged_in():
            lang_col, watch_col, notif_col, account_col = st.columns(
                [1.15, 1.15, 1.15, 1.0]
            )
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
