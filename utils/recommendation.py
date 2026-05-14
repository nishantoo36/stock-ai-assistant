"""
Multi-signal recommendation engine.
Combines RSI, SMA cross, MACD, Bollinger, volume, 52W range,
momentum, and news sentiment into a single BUY / HOLD / SELL call.
"""

import pandas as pd
import numpy as np

from utils.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger,
    volume_trend,
)
from utils.sentiment import analyze_news_sentiment


def generate_recommendation(
    df: pd.DataFrame,
    stock_info: dict,
    news_list: list,
) -> tuple:
    """
    Returns:
        rec         : "BUY" | "HOLD" | "SELL"
        confidence  : int (51–93)
        risk        : str
        summary     : str (markdown)
        signals     : list of (name, value, weight, description)
        news_label  : str
        news_detail : list of dicts
        rsi         : float
        sma20       : float | None
        sma50       : float | None
        mom5        : float
        score_pct   : float
    """
    signals: list[tuple] = []
    clean = df.dropna(subset=["Close"])

    if clean.empty:
        return "HOLD", 50, "Medium", "Insufficient data.", [], "Neutral", [], 50, None, None, 0, 0

    close  = clean["Close"]
    price  = close.iloc[-1]
    has26  = len(close) >= 26

    # ── RSI ──────────────────────────────────────────
    rsi_s = calculate_rsi(close)
    rsi   = rsi_s.iloc[-1] if not pd.isna(rsi_s.iloc[-1]) else 50

    if   rsi < 30: signals.append(("RSI",  1, 2, f"RSI {rsi:.1f} — oversold, potential buy"))
    elif rsi < 45: signals.append(("RSI",  1, 1, f"RSI {rsi:.1f} — mildly oversold"))
    elif rsi > 70: signals.append(("RSI", -1, 2, f"RSI {rsi:.1f} — overbought, pullback risk"))
    elif rsi > 55: signals.append(("RSI", -1, 1, f"RSI {rsi:.1f} — mildly overbought"))
    else:          signals.append(("RSI",  0, 1, f"RSI {rsi:.1f} — neutral"))

    # ── SMA cross ────────────────────────────────────
    sma20 = sma50 = None
    if has26:
        s20 = close.rolling(20).mean()
        s50 = close.rolling(50).mean()
        if not pd.isna(s20.iloc[-1]) and not pd.isna(s50.iloc[-1]):
            sma20, sma50 = s20.iloc[-1], s50.iloc[-1]
            d = ((sma20 - sma50) / sma50) * 100
            if   d >  2: signals.append(("SMA Cross",  1, 2, f"SMA20 {d:.1f}% above SMA50 — golden cross"))
            elif d >  0: signals.append(("SMA Cross",  1, 1, "SMA20 slightly above SMA50 — mild uptrend"))
            elif d < -2: signals.append(("SMA Cross", -1, 2, f"SMA20 {abs(d):.1f}% below SMA50 — death cross"))
            else:        signals.append(("SMA Cross", -1, 1, "SMA20 slightly below SMA50 — mild downtrend"))

    # ── Price vs SMA20 / SMA50 ───────────────────────
    if sma20:
        if   price > sma20 * 1.02: signals.append(("Price vs SMA20",  1, 1, "Price above 20-day avg — short-term strength"))
        elif price < sma20 * 0.98: signals.append(("Price vs SMA20", -1, 1, "Price below 20-day avg — short-term weakness"))
        else:                      signals.append(("Price vs SMA20",  0, 1, "Price near 20-day avg — no directional signal"))

    if sma50:
        if   price > sma50 * 1.03: signals.append(("Price vs SMA50",  1, 1, "Price above 50-day avg — medium-term uptrend"))
        elif price < sma50 * 0.97: signals.append(("Price vs SMA50", -1, 1, "Price below 50-day avg — medium-term downtrend"))
        else:                      signals.append(("Price vs SMA50",  0, 1, "Price near 50-day avg — range-bound"))

    # ── Momentum ─────────────────────────────────────
    mom5 = 0.0
    if len(close) >= 6:
        mom5 = ((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6]) * 100
        if   mom5 >  5: signals.append(("5D Momentum",  1, 1, f"+{mom5:.1f}% in 5 days — strong short-term momentum"))
        elif mom5 < -5: signals.append(("5D Momentum", -1, 1, f"{mom5:.1f}% in 5 days — selling pressure"))
        else:           signals.append(("5D Momentum",  0, 1, f"{mom5:.1f}% 5-day change — flat"))

    if len(close) >= 21:
        m20 = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100
        if   m20 >  8: signals.append(("20D Momentum",  1, 1, f"+{m20:.1f}% over 20 days — medium-term bullish"))
        elif m20 < -8: signals.append(("20D Momentum", -1, 1, f"{m20:.1f}% over 20 days — medium-term bearish"))
        else:          signals.append(("20D Momentum",  0, 1, f"{m20:.1f}% 20-day change — moderate"))

    # ── MACD ─────────────────────────────────────────
    if has26:
        ml, ms = calculate_macd(close)
        mv, sv = ml.iloc[-1], ms.iloc[-1]
        if not pd.isna(mv) and not pd.isna(sv):
            diff = mv - sv
            thr  = price * 0.005
            if   diff >  thr: signals.append(("MACD",  1, 2, "MACD above signal — bullish crossover"))
            elif diff >  0:   signals.append(("MACD",  1, 1, "MACD slightly above signal — early bullish"))
            elif diff < -thr: signals.append(("MACD", -1, 2, "MACD below signal — bearish crossover"))
            else:             signals.append(("MACD", -1, 1, "MACD slightly below signal — mild bearish"))

    # ── Bollinger ────────────────────────────────────
    if has26:
        _, _, bp_s = calculate_bollinger(close)
        bp = bp_s.iloc[-1]
        if not pd.isna(bp):
            if   bp < 0.15: signals.append(("Bollinger",  1, 2, "Near lower band — likely oversold"))
            elif bp < 0.35: signals.append(("Bollinger",  1, 1, "Lower half of bands — leaning oversold"))
            elif bp > 0.85: signals.append(("Bollinger", -1, 2, "Near upper band — likely overbought"))
            elif bp > 0.65: signals.append(("Bollinger", -1, 1, "Upper half of bands — leaning overbought"))
            else:           signals.append(("Bollinger",  0, 1, "Mid-band range — balanced"))

    # ── Volume ───────────────────────────────────────
    if "Volume" in df.columns and len(clean) >= 20:
        vt = volume_trend(clean)
        if   vt ==  1: signals.append(("Volume",  1, 1, "High volume on up days — buyer conviction"))
        elif vt == -1: signals.append(("Volume", -1, 1, "High volume on down days — seller conviction"))
        else:          signals.append(("Volume",  0, 1, "Normal volume — no unusual activity"))

    # ── 52-week range ────────────────────────────────
    w52h = stock_info.get("fiftyTwoWeekHigh")
    w52l = stock_info.get("fiftyTwoWeekLow")
    if w52h and w52l and w52h > w52l:
        p52 = (price - w52l) / (w52h - w52l)
        if   p52 < 0.20: signals.append(("52W Range",  1, 2, "Near 52W low — contrarian buy zone"))
        elif p52 < 0.40: signals.append(("52W Range",  1, 1, "Lower 40% of 52W range — relative value"))
        elif p52 > 0.85: signals.append(("52W Range", -1, 2, "Near 52W high — less margin of safety"))
        elif p52 > 0.65: signals.append(("52W Range", -1, 1, "Upper 35% of 52W range — some caution"))
        else:            signals.append(("52W Range",  0, 1, "Mid 52W range — neutral positioning"))

    # ── News sentiment ───────────────────────────────
    ns, news_label, news_detail = analyze_news_sentiment(news_list)
    _news_map = {
         2: ( 1, 2, "Very positive news — strong tailwind"),
         1: ( 1, 1, "Positive news — mild tailwind"),
         0: ( 0, 1, "Neutral news — no directional signal"),
        -1: (-1, 1, "Negative news — mild headwind"),
        -2: (-1, 2, "Very negative news — strong headwind"),
    }
    nv, nw, _ = _news_map[ns]
    signals.append(("News", nv, nw, _news_map[ns][2]))

    # ── Aggregate ────────────────────────────────────
    weighted_sum = sum(v * w for _, v, w, _ in signals)
    max_sum      = sum(w     for _, _, w, _ in signals)
    score_pct    = (weighted_sum / max_sum) * 100

    rec  = "BUY" if score_pct >= 22 else "SELL" if score_pct <= -22 else "HOLD"
    conf = min(93, max(51, int(50 + abs(score_pct) * 0.45)))

    buys     = [s for s in signals if s[1] ==  1]
    sells    = [s for s in signals if s[1] == -1]
    nc       = len(signals)
    conflict = min(len(buys), len(sells)) / nc if nc else 0

    risk = (
        "High"       if rec == "SELL" else
        "Low–Medium" if rec == "BUY" and conflict < 0.2 and conf > 72 else
        "Medium"
    )

    top_bull = [d for _, v, w, d in signals if v ==  1 and w >= 2]
    top_bear = [d for _, v, w, d in signals if v == -1 and w >= 2]

    if rec == "BUY":
        summary = (f"**{len(buys)} of {nc} signals are bullish.**\n\n"
                   + (top_bull[0] if top_bull else "Multiple factors align positively."))
    elif rec == "SELL":
        summary = (f"**{len(sells)} of {nc} signals are bearish.**\n\n"
                   + (top_bear[0] if top_bear else "Multiple factors point to elevated risk."))
    else:
        summary = (f"**Mixed: {len(buys)} bullish, {len(sells)} bearish of {nc} total.**\n\n"
                   "No strong directional conviction — holding or waiting is prudent.")

    return rec, conf, risk, summary, signals, news_label, news_detail, rsi, sma20, sma50, mom5, score_pct
