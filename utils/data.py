"""
Data loaders — cache-first, yfinance fallback.
All loaders use the shared SQLite cache so Yahoo Finance
is hit once per ticker per TTL window across all users.
"""

import io
import time
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import pandas as pd
import yfinance as yf
import feedparser
import streamlit as st
from yahooquery import search

from utils.cache import (
    cache_get, cache_get_stale, cache_set,
    fetch_in_background,
    TTL_INFO, TTL_HISTORY, TTL_NEWS, TTL_SEARCH,
)

PERIOD_MAP = {
    "1D":  ("1d",  "5m"),
    "3D":  ("5d",  "30m"),
    "5D":  ("5d",  "1h"),
    "1M":  ("1mo", "1d"),
    "3M":  ("3mo", "1d"),
    "6M":  ("6mo", "1d"),
    "1Y":  ("1y",  "1d"),
    "MAX": ("max", "1wk"),
}
CHART_PERIODS = ["1D", "3D", "5D", "1M", "3M", "6M", "1Y", "MAX"]


# ── Search ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=TTL_SEARCH)
def do_search(query: str) -> dict:
    return search(query)


# ── Stock info ────────────────────────────────────────────────────────────────

def _yf_fetch_info(ticker: str) -> dict:
    """Fetch stock.info with retry/backoff."""
    for delay in [2, 5, 10]:
        try:
            info = yf.Ticker(ticker).info
            if info and len(info) > 5:
                return info
        except Exception:
            pass
        time.sleep(delay)
    return yf.Ticker(ticker).info   # final attempt — may raise


def load_stock_info(ticker: str) -> dict:
    """
    Stale-while-revalidate:
    1. Fresh cache  → return immediately.
    2. Stale cache  → return stale data, refresh in background.
    3. No cache     → fetch synchronously (first ever load).
    """
    key    = f"info:{ticker}"
    cached = cache_get(key, TTL_INFO)
    if cached:
        return cached

    stale = cache_get_stale(key)
    if stale:
        fetch_in_background(_yf_fetch_info, key, ticker)
        return stale

    info = _yf_fetch_info(ticker)
    cache_set(key, info)
    return info


# ── Live price ───────────────────────────────────────────────────────────────

TTL_LIVE = 60   # 60-second TTL — fast_info is lightweight, keep it fresh

def _yf_fetch_live(ticker: str) -> dict:
    fi = yf.Ticker(ticker).fast_info
    return {
        "price":          getattr(fi, "last_price",     None),
        "previous_close": getattr(fi, "previous_close", None),
    }


def load_live_price(ticker: str) -> dict:
    """Return {price, previous_close} with a 60-second cache."""
    key    = f"live:{ticker}"
    cached = cache_get(key, TTL_LIVE)
    if cached:
        return cached
    stale = cache_get_stale(key)
    if stale:
        fetch_in_background(_yf_fetch_live, key, ticker)
        return stale
    data = _yf_fetch_live(ticker)
    cache_set(key, data)
    return data


# ── Price history ─────────────────────────────────────────────────────────────

def _yf_fetch_history(ticker: str, period: str, interval: str):
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        return None
    df = df.reset_index()
    df.index = df.index.astype(str)
    return df.to_json()


def _load_history_cached(ticker: str, period: str, interval: str, ttl: int) -> pd.DataFrame:
    key    = f"hist:{ticker}:{period}:{interval}"
    cached = cache_get(key, ttl)
    if cached:
        try:
            return pd.read_json(io.StringIO(cached))
        except Exception:
            pass

    stale = cache_get_stale(key)
    if stale:
        fetch_in_background(_yf_fetch_history, key, ticker, period, interval)
        try:
            stale_str = stale if isinstance(stale, str) else json.dumps(stale)
            return pd.read_json(io.StringIO(stale_str))
        except Exception:
            pass

    raw = _yf_fetch_history(ticker, period, interval)
    if raw:
        cache_set(key, raw)
        return pd.read_json(io.StringIO(raw))
    return pd.DataFrame()


def load_chart_data(ticker: str, period: str) -> pd.DataFrame:
    p, i = PERIOD_MAP.get(period, ("1mo", "1d"))
    return _load_history_cached(ticker, p, i, TTL_HISTORY)


def load_analysis_data(ticker: str) -> pd.DataFrame:
    return _load_history_cached(ticker, "6mo", "1d", TTL_INFO)


# ── News ──────────────────────────────────────────────────────────────────────

_NEWS_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
}


def _format_news_date(entry) -> str:
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    if not published:
        return ""

    try:
        dt = parsedate_to_datetime(published)
        if dt:
            return dt.strftime("%b %d, %Y").replace(" 0", " ")
    except Exception:
        pass

    try:
        parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if parsed:
            return datetime(*parsed[:6]).strftime("%b %d, %Y").replace(" 0", " ")
    except Exception:
        pass

    return published


def _format_unix_news_date(timestamp) -> str:
    if not timestamp:
        return ""

    try:
        return datetime.fromtimestamp(int(timestamp)).strftime("%b %d, %Y").replace(" 0", " ")
    except Exception:
        return ""


def _fetch_news_rss(query: str) -> list[dict]:
    encoded_query = quote_plus(f"{query} stock")
    url = (
        "https://news.google.com/rss/search"
        f"?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )
    feed = feedparser.parse(url, request_headers=_NEWS_REQUEST_HEADERS)
    if getattr(feed, "bozo", False) and not feed.entries:
        return []

    return [
        {
            "title":     e.title,
            "link":      e.link,
            "publisher": e.source.title if hasattr(e, "source") else "Google News",
            "published": _format_news_date(e),
        }
        for e in feed.entries[:15]
    ]


def _fetch_news_yfinance(ticker: str) -> list[dict]:
    if not ticker:
        return []

    try:
        items = yf.Ticker(ticker).news or []
    except Exception:
        return []

    results: list[dict] = []
    for item in items[:15]:
        content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}
        canonical_url = content.get("canonicalUrl", {})
        if not isinstance(canonical_url, dict):
            canonical_url = {}
        provider = content.get("provider", {})
        if not isinstance(provider, dict):
            provider = {}

        title = item.get("title") or content.get("title") or ""
        link = item.get("link") or canonical_url.get("url", "")
        publisher = (
            item.get("publisher")
            or provider.get("displayName")
            or provider.get("name")
            or "Yahoo Finance"
        )
        published = (
            item.get("providerPublishTime")
            or item.get("pubDate")
            or content.get("pubDate")
            or content.get("displayTime")
        )

        if not title:
            continue

        results.append(
            {
                "title": title,
                "link": link,
                "publisher": publisher,
                "published": (
                    _format_unix_news_date(published)
                    if isinstance(published, (int, float, str)) and str(published).isdigit()
                    else str(published or "")
                ),
            }
        )

    return results


@st.cache_data(ttl=TTL_NEWS)
def load_news(company_name: str, ticker: str = "") -> list[dict]:
    queries = [company_name, ticker, ticker.split(".")[0] if ticker else ""]
    seen: set[str] = set()

    for query in queries:
        query = (query or "").strip()
        if not query or query.lower() in seen:
            continue
        seen.add(query.lower())
        results = _fetch_news_rss(query)
        if results:
            return results

    return _fetch_news_yfinance(ticker)
