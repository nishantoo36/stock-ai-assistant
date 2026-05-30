"""Price-alert and notification persistence."""

from __future__ import annotations

from services.user_context import current_user_client, current_user_id
from utils.platform.i18n import t


def create_price_alert(
    ticker: str,
    company_name: str | None,
    target_price: float,
    condition: str,
    alert_type: str,
) -> None:
    user_id = current_user_id()
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
    client = current_user_client()
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


def load_notifications(limit: int) -> list[dict]:
    response = (
        current_user_client()
        .table("notification_events")
        .select("ticker, message, is_read, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def load_notifications_page(page: int, page_size: int) -> tuple[list[dict], bool]:
    offset = max(page, 0) * page_size
    response = (
        current_user_client()
        .table("notification_events")
        .select("ticker, message, is_read, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data or []
    return rows[:page_size], len(rows) > page_size


def load_price_alerts_page(page: int, page_size: int) -> tuple[list[dict], bool]:
    offset = max(page, 0) * page_size
    response = (
        current_user_client()
        .table("price_alerts")
        .select("id, ticker, company_name, target_price, condition, alert_type, is_active, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data or []
    return rows[:page_size], len(rows) > page_size


def delete_price_alert(alert_id) -> None:
    current_user_client().table("price_alerts").delete().eq("id", alert_id).execute()


def update_price_alert(
    alert_id,
    target_price: float,
    condition: str,
    alert_type: str,
) -> None:
    current_user_client().table("price_alerts").update({
        "target_price": float(target_price),
        "condition": condition,
        "alert_type": alert_type,
    }).eq("id", alert_id).execute()
