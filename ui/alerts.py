"""
Price alert creation and notification preview for authenticated users.
"""

from __future__ import annotations

from html import escape

import streamlit as st

# Avoid top-level import from ui.auth to prevent circular imports; import lazily inside functions
from utils.i18n import t
from utils.supabase_client import SupabaseConfigError, get_user_supabase_client

PAGE_SIZE = 30


def _user_client():
    from ui.auth import get_access_token
    return get_user_supabase_client(get_access_token())


def _user_id() -> str | None:
    from ui.auth import get_current_user
    return get_current_user().get("id")


def create_price_alert(
    ticker: str,
    company_name: str | None,
    target_price: float,
    condition: str,
    alert_type: str,
) -> None:
    user_id = _user_id()
    if not user_id:
        raise RuntimeError(t("auth.login_required"))

    payload = {
        "user_id": user_id,
        "ticker": ticker,
        "company_name": company_name,
        "target_price": target_price,
        "condition": condition,
        "alert_type": alert_type,
        "is_active": True,
    }
    client = _user_client()
    existing = (
        client
        .table("price_alerts")
        .select("id")
        .eq("user_id", user_id)
        .eq("ticker", ticker)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    if existing.data:
        keep_id = existing.data[0]["id"]
        client.table("price_alerts").update(payload).eq("id", keep_id).execute()
        for duplicate in existing.data[1:]:
            client.table("price_alerts").delete().eq("id", duplicate["id"]).execute()
        return

    client.table("price_alerts").insert(payload).execute()


def render_alert_form(ticker: str, company_name: str | None, current_price: float | None = None) -> None:
    from ui.auth import is_logged_in
    with st.popover(t("alerts.create_alert"), use_container_width=True):
        if not is_logged_in():
            st.caption(t("auth.login_required"))
            if st.button(t("auth.login"), key=f"login_for_alert_{ticker}", use_container_width=True):
                st.session_state.show_login = True
                st.rerun()
            return

        default_price = float(current_price) if current_price and current_price > 0 else 0.01
        target_price = st.number_input(
            t("alerts.target_price"),
            min_value=0.01,
            value=default_price,
            step=1.0,
            key=f"alert_target_price_{ticker}",
        )
        condition_label = st.selectbox(
            t("alerts.condition"),
            [t("alerts.above"), t("alerts.below")],
            key=f"alert_condition_{ticker}",
        )
        alert_type_label = st.selectbox(
            t("alerts.alert_type"),
            [t("alerts.target"), t("alerts.buy"), t("alerts.sell")],
            key=f"alert_type_{ticker}",
        )

        if not st.button(t("alerts.save_alert"), key=f"save_alert_{ticker}"):
            return

        condition = "above" if condition_label == t("alerts.above") else "below"
        alert_type_by_label = {
            t("alerts.target"): "target",
            t("alerts.buy"): "buy",
            t("alerts.sell"): "sell",
        }
        alert_type = alert_type_by_label.get(alert_type_label, "target")

        try:
            create_price_alert(ticker, company_name, float(target_price), condition, alert_type)
            st.success(t("alerts.alert_saved"))
        except (SupabaseConfigError, Exception) as exc:
            st.error(t("alerts.alert_error", error=str(exc)))


def render_notifications_preview(limit: int = 5) -> None:
    from ui.auth import is_logged_in
    if not is_logged_in():
        return

    with st.expander(t("alerts.notifications"), expanded=False):
        try:
            response = (
                _user_client()
                .table("notification_events")
                .select("ticker, message, is_read, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        except Exception as exc:
            st.error(t("alerts.notification_error", error=str(exc)))
            return

        rows = response.data or []
        if not rows:
            st.caption(t("alerts.no_notifications"))
            return

        for row in rows:
            status = "" if row.get("is_read") else t("alerts.unread_marker")
            st.markdown(f"- {status} **{row.get('ticker')}**: {row.get('message')}")


def _load_notifications_page(page: int, page_size: int = PAGE_SIZE) -> tuple[list[dict], bool]:
    offset = max(page, 0) * page_size
    response = (
        _user_client()
        .table("notification_events")
        .select("ticker, message, is_read, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data or []
    return rows[:page_size], len(rows) > page_size


def _render_notifications_page() -> None:
    page_key = "notifications_page"
    st.session_state.setdefault(page_key, 0)
    page = st.session_state[page_key]

    try:
        rows, has_next = _load_notifications_page(page)
    except Exception as exc:
        st.error(t("alerts.notification_error", error=str(exc)))
        return

    if not rows:
        st.caption(t("alerts.no_notifications"))
        return

    for row in rows:
        status = escape(t("alerts.unread_marker")) if not row.get("is_read") else ""
        ticker = escape(row.get("ticker") or "")
        created_at = escape(str(row.get("created_at") or "")[:10])
        message = escape(row.get("message") or "")
        st.markdown(
            f"<div class='list-row-title'>{status} {ticker}</div>"
            f"<div class='list-row-meta'>{created_at}</div>"
            f"<div class='notification-message'>{message}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='list-row-divider'></div>", unsafe_allow_html=True)

    prev_col, page_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if st.button(t("common.previous"), disabled=page == 0, use_container_width=True, key="notifications_prev"):
            st.session_state[page_key] = max(page - 1, 0)
            st.rerun()
    with page_col:
        st.caption(t("common.page", page=page + 1))
    with next_col:
        if st.button(t("common.next"), disabled=not has_next, use_container_width=True, key="notifications_next"):
            st.session_state[page_key] = page + 1
            st.rerun()


def render_notifications_dialog() -> None:
    @st.dialog(t("alerts.notifications"), width="large")
    def _dialog() -> None:
        _render_notifications_page()

    _dialog()


def render_notifications_button() -> None:
    from ui.auth import is_logged_in
    if not is_logged_in():
        return

    if st.button(t("alerts.notifications"), key="open_notifications_dialog", use_container_width=True):
        render_notifications_dialog()


def _load_price_alerts(page: int, page_size: int = PAGE_SIZE) -> tuple[list[dict], bool]:
    offset = max(page, 0) * page_size
    response = (
        _user_client()
        .table("price_alerts")
        .select("id, ticker, company_name, target_price, condition, alert_type, is_active, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data or []
    return rows[:page_size], len(rows) > page_size


def _render_price_alerts_page() -> None:
    page_key = "price_alerts_page"
    edit_key = "editing_price_alert_id"
    st.session_state.setdefault(page_key, 0)
    st.session_state.setdefault(edit_key, None)
    page = st.session_state[page_key]

    try:
        rows, has_next = _load_price_alerts(page)
    except Exception as exc:
        st.error(t("alerts.alerts_load_error", error=str(exc)))
        return

    if not rows:
        st.caption(t("alerts.no_alerts"))
        return

    for index, row in enumerate(rows):
        aid = row.get("id")
        ticker = escape(row.get("ticker") or "")
        name = escape(row.get("company_name") or "")
        price = escape(str(row.get("target_price") or ""))
        cond = escape(row.get("condition") or "")
        atype = escape(row.get("alert_type") or "")
        created = escape(str(row.get("created_at") or "")[:10])

        st.markdown(
            f"<div class='list-row-title'>{name} `{ticker}`</div>"
            f"<div class='list-row-meta'>{cond.upper()} • {atype} • {price} • {created}</div>",
            unsafe_allow_html=True,
        )

        col_open, col_edit, col_delete = st.columns([1, 1, 1])
        with col_open:
            if st.button(t("common.open"), key=f"open_alert_{page}_{index}", use_container_width=True):
                st.session_state.selected_ticker = row.get("ticker")
                st.session_state.company_name = row.get("company_name") or row.get("ticker")
                st.rerun()
        with col_edit:
            if st.button(t("common.edit"), key=f"edit_alert_{page}_{index}", use_container_width=True):
                st.session_state[edit_key] = None if st.session_state[edit_key] == aid else aid
        with col_delete:
            if st.button(t("common.delete"), key=f"delete_alert_{page}_{index}", use_container_width=True):
                try:
                    _user_client().table("price_alerts").delete().eq("id", aid).execute()
                    if st.session_state.get(edit_key) == aid:
                        st.session_state[edit_key] = None
                    st.success(t("alerts.alert_deleted"))
                    st.rerun()
                except Exception as exc:
                    st.error(t("alerts.alert_error", error=str(exc)))

        if st.session_state.get(edit_key) == aid:
            condition_options = [t("alerts.above"), t("alerts.below")]
            type_options = [t("alerts.target"), t("alerts.buy"), t("alerts.sell")]
            current_condition = 0 if row.get("condition") == "above" else 1
            current_type = {"target": 0, "buy": 1, "sell": 2}.get(row.get("alert_type"), 0)

            with st.form(f"edit_alert_form_{aid}"):
                new_price = st.number_input(
                    t("alerts.target_price"),
                    min_value=0.01,
                    value=float(row.get("target_price") or 0.01),
                    step=1.0,
                )
                new_condition = st.selectbox(
                    t("alerts.condition"),
                    condition_options,
                    index=current_condition,
                )
                new_type = st.selectbox(
                    t("alerts.alert_type"),
                    type_options,
                    index=current_type,
                )
                save_col, cancel_col = st.columns(2)
                with save_col:
                    submitted = st.form_submit_button(t("common.save"), use_container_width=True)
                with cancel_col:
                    cancelled = st.form_submit_button(t("common.cancel"), use_container_width=True)

            if cancelled:
                st.session_state[edit_key] = None
                st.rerun()

            if submitted:
                cond_val = "above" if new_condition == t("alerts.above") else "below"
                type_map = {t("alerts.target"): "target", t("alerts.buy"): "buy", t("alerts.sell"): "sell"}
                atype_val = type_map.get(new_type, "target")
                try:
                    _user_client().table("price_alerts").update({
                        "target_price": float(new_price),
                        "condition": cond_val,
                        "alert_type": atype_val,
                    }).eq("id", aid).execute()
                    st.session_state[edit_key] = None
                    st.success(t("alerts.alert_updated"))
                    st.rerun()
                except Exception as exc:
                    st.error(t("alerts.alert_error", error=str(exc)))

        st.markdown("<div class='list-row-divider'></div>", unsafe_allow_html=True)

    prev_col, page_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if st.button(t("common.previous"), disabled=page == 0, use_container_width=True, key="alerts_prev"):
            st.session_state[page_key] = max(page - 1, 0)
            st.rerun()
    with page_col:
        st.caption(t("common.page", page=page + 1))
    with next_col:
        if st.button(t("common.next"), disabled=not has_next, use_container_width=True, key="alerts_next"):
            st.session_state[page_key] = page + 1
            st.rerun()


def render_price_alerts_dialog() -> None:
    @st.dialog(t("alerts.my_alerts"), width="large")
    def _dialog() -> None:
        _render_price_alerts_page()

    _dialog()


def render_manage_alerts_button() -> None:
    from ui.auth import is_logged_in
    if not is_logged_in():
        return

    if st.button(t("alerts.my_alerts"), key="open_alerts_dialog", use_container_width=True):
        render_price_alerts_dialog()
