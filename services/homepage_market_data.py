"""Homepage market-data selection and quote formatting."""

from __future__ import annotations

from utils.data.market_data import load_live_price
from utils.platform.i18n import t
from ui.home.markets import (
    COUNTRY_ETFS,
    COUNTRY_MARKETS,
    GLOBAL_MARKET,
    QUICK_TOPIC_MARKETS,
    TOPIC_FALLBACK_MARKETS,
)

QUICK_TOPIC_KEYS = {"trending", "best_etfs", "dividend", "ai", "undervalued"}


def currency_prefix(currency: str) -> str:
    return {
        "USD": "$",
        "EUR": "€",
        "INR": "₹",
        "JPY": "¥",
        "CAD": "C$",
        "GBp": "£",
        "AUD": "A$",
        "CHF": "CHF ",
        "CNY": "¥",
        "SGD": "S$",
        "AED": "د.إ",
    }.get(currency, "")


def format_live_price(price, currency: str) -> str:
    if price is None:
        return "Unavailable"

    try:
        price = float(price)
    except (TypeError, ValueError):
        return "Unavailable"

    if price != price:
        return "Unavailable"

    decimals = 0 if currency in {"", "JPY", "GBp"} else 2
    if currency == "GBp":
        price = price / 100
        decimals = 2
    return f"{currency_prefix(currency)}{price:,.{decimals}f}"


def format_live_change(price, previous_close) -> str | None:
    if price is None or previous_close is None:
        return None

    try:
        price = float(price)
        previous_close = float(previous_close)
    except (TypeError, ValueError):
        return None

    if price != price or previous_close != previous_close:
        return None

    if previous_close <= 0:
        return None

    pct = ((price - previous_close) / previous_close) * 100
    return f"{pct:+.2f}%"


def live_change_score(symbol: str) -> float | None:
    try:
        live = load_live_price(symbol)
        price = float(live.get("price"))
        previous_close = float(live.get("previous_close"))
    except (TypeError, ValueError, Exception):
        return None

    if price != price or previous_close != previous_close or previous_close <= 0:
        return None

    return ((price - previous_close) / previous_close) * 100


def rank_available_stocks(
    candidates: list[tuple[str, str, str]],
    limit: int = 5,
) -> list[tuple[str, str, str]]:
    ranked = []
    seen = set()
    for stock in candidates:
        symbol = stock[1]
        if symbol in seen:
            continue
        seen.add(symbol)

        score = live_change_score(symbol)
        if score is None:
            continue
        ranked.append((score, stock))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [stock for _score, stock in ranked[:limit]]


def get_live_market_quote(symbol: str, currency: str) -> tuple[str, str]:
    try:
        live = load_live_price(symbol)
    except Exception:
        return t("common.unavailable"), t("homepage.not_available")

    price = live.get("price")
    previous_close = live.get("previous_close")
    return (
        format_live_price(price, currency).replace("Unavailable", t("common.unavailable")),
        format_live_change(price, previous_close) or t("homepage.not_available"),
    )


def get_homepage_market_data(selected_countries: list[str]) -> tuple[list, list]:
    if not selected_countries:
        return GLOBAL_MARKET["indexes"], rank_available_stocks(GLOBAL_MARKET["stocks"])

    indexes = []
    stocks = []
    for country in selected_countries:
        market = COUNTRY_MARKETS.get(country)
        if market:
            indexes.extend(market["indexes"])
            stocks.extend(market["stocks"])

    return indexes[:4], rank_available_stocks(stocks)


def get_quick_topic_stocks(topic: str, selected_countries: list[str]) -> list[tuple[str, str, str]]:
    topic_data = QUICK_TOPIC_MARKETS.get(topic)
    if not topic_data:
        return get_homepage_market_data(selected_countries)[1]

    if not selected_countries:
        return rank_available_stocks(topic_data["global"])

    stocks = []
    seen = set()
    for country in selected_countries:
        country_stocks = topic_data["countries"].get(country, [])
        if not country_stocks:
            if topic == "best_etfs":
                country_stocks = COUNTRY_ETFS.get(country, [])
            else:
                country_stocks = TOPIC_FALLBACK_MARKETS.get(topic, {}).get(country, [])
                if not country_stocks:
                    country_stocks = COUNTRY_MARKETS.get(country, {}).get("stocks", [])

        for stock in country_stocks:
            if stock[1] in seen:
                continue
            seen.add(stock[1])
            stocks.append(stock)
    return rank_available_stocks(stocks)


def get_ai_picks(selected_countries: list[str]) -> list[tuple[str, str, str]]:
    picks = get_quick_topic_stocks("ai", selected_countries)
    reason_keys = [
        "homepage.ai_pick_momentum",
        "homepage.ai_pick_growth",
        "homepage.ai_pick_expansion",
    ]
    return [
        (symbol, company_name, t(reason_keys[index % len(reason_keys)]))
        for index, (company_name, symbol, _currency) in enumerate(picks[:3])
    ]
