"""
Multi-signal recommendation engine.
Combines RSI, SMA cross, MACD, Bollinger, volume, 52W range,
momentum, and news sentiment into a single BUY / HOLD / SELL call.

Note: Signal descriptions are keys that will be translated in the UI layer.
"""

import pandas as pd
import numpy as np

from utils.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger,
    volume_trend,
)
from utils.sentiment import analyze_news_sentiment
from utils.i18n import t


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
        return "HOLD", 50, "Medium", t("summary.insufficient_data"), [], "Neutral", [], 50, None, None, 0, 0

    close  = clean["Close"]
    price  = close.iloc[-1]
    has26  = len(close) >= 26

    # ── RSI ──────────────────────────────────────────
    rsi_s = calculate_rsi(close)
    rsi   = rsi_s.iloc[-1] if not pd.isna(rsi_s.iloc[-1]) else 50

    if   rsi < 30: signals.append(("RSI",  1, 2, ("signals.rsi_oversold", {"value": f"{rsi:.1f}"})))
    elif rsi < 45: signals.append(("RSI",  1, 1, ("signals.rsi_mild_oversold", {"value": f"{rsi:.1f}"})))
    elif rsi > 70: signals.append(("RSI", -1, 2, ("signals.rsi_overbought", {"value": f"{rsi:.1f}"})))
    elif rsi > 55: signals.append(("RSI", -1, 1, ("signals.rsi_mild_overbought", {"value": f"{rsi:.1f}"})))
    else:          signals.append(("RSI",  0, 1, ("signals.rsi_neutral", {"value": f"{rsi:.1f}"})))

    # ── SMA cross ────────────────────────────────────
    sma20 = sma50 = None
    if has26:
        s20 = close.rolling(20).mean()
        s50 = close.rolling(50).mean()
        if not pd.isna(s20.iloc[-1]) and not pd.isna(s50.iloc[-1]):
            sma20, sma50 = s20.iloc[-1], s50.iloc[-1]
            d = ((sma20 - sma50) / sma50) * 100
            if   d >  2: signals.append(("SMA Cross",  1, 2, ("signals.sma_golden_cross", {"diff": f"{d:.1f}"})))
            elif d >  0: signals.append(("SMA Cross",  1, 1, ("signals.sma_above", {})))
            elif d < -2: signals.append(("SMA Cross", -1, 2, ("signals.sma_death_cross", {"diff": f"{abs(d):.1f}"})))
            else:        signals.append(("SMA Cross", -1, 1, ("signals.sma_below", {})))

    # ── Price vs SMA20 / SMA50 ───────────────────────
    if sma20:
        if   price > sma20 * 1.02: signals.append(("Price vs SMA20",  1, 1, ("signals.price_above_sma20", {})))
        elif price < sma20 * 0.98: signals.append(("Price vs SMA20", -1, 1, ("signals.price_below_sma20", {})))
        else:                      signals.append(("Price vs SMA20",  0, 1, ("signals.price_near_sma20", {})))

    if sma50:
        if   price > sma50 * 1.03: signals.append(("Price vs SMA50",  1, 1, ("signals.price_above_sma50", {})))
        elif price < sma50 * 0.97: signals.append(("Price vs SMA50", -1, 1, ("signals.price_below_sma50", {})))
        else:                      signals.append(("Price vs SMA50",  0, 1, ("signals.price_near_sma50", {})))

    # ── Momentum ─────────────────────────────────────
    mom5 = 0.0
    if len(close) >= 6:
        mom5 = ((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6]) * 100
        if   mom5 >  5: signals.append(("5D Momentum",  1, 1, ("signals.momentum_5d_strong", {"pct": f"{mom5:.1f}"})))
        elif mom5 < -5: signals.append(("5D Momentum", -1, 1, ("signals.momentum_5d_weak", {"pct": f"{mom5:.1f}"})))
        else:           signals.append(("5D Momentum",  0, 1, ("signals.momentum_5d_flat", {"pct": f"{mom5:.1f}"})))

    if len(close) >= 21:
        m20 = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100
        if   m20 >  8: signals.append(("20D Momentum",  1, 1, ("signals.momentum_20d_bullish", {"pct": f"{m20:.1f}"})))
        elif m20 < -8: signals.append(("20D Momentum", -1, 1, ("signals.momentum_20d_bearish", {"pct": f"{m20:.1f}"})))
        else:          signals.append(("20D Momentum",  0, 1, ("signals.momentum_20d_moderate", {"pct": f"{m20:.1f}"})))

    # ── MACD ─────────────────────────────────────────
    if has26:
        ml, ms = calculate_macd(close)
        mv, sv = ml.iloc[-1], ms.iloc[-1]
        if not pd.isna(mv) and not pd.isna(sv):
            diff = mv - sv
            thr  = price * 0.005
            if   diff >  thr: signals.append(("MACD",  1, 2, ("signals.macd_bullish", {})))
            elif diff >  0:   signals.append(("MACD",  1, 1, ("signals.macd_early_bullish", {})))
            elif diff < -thr: signals.append(("MACD", -1, 2, ("signals.macd_bearish", {})))
            else:             signals.append(("MACD", -1, 1, ("signals.macd_mild_bearish", {})))

    # ── Bollinger ────────────────────────────────────
    if has26:
        _, _, bp_s = calculate_bollinger(close)
        bp = bp_s.iloc[-1]
        if not pd.isna(bp):
            if   bp < 0.15: signals.append(("Bollinger",  1, 2, ("signals.bollinger_lower", {})))
            elif bp < 0.35: signals.append(("Bollinger",  1, 1, ("signals.bollinger_lower_half", {})))
            elif bp > 0.85: signals.append(("Bollinger", -1, 2, ("signals.bollinger_upper", {})))
            elif bp > 0.65: signals.append(("Bollinger", -1, 1, ("signals.bollinger_upper_half", {})))
            else:           signals.append(("Bollinger",  0, 1, ("signals.bollinger_midband", {})))

    # ── Volume ───────────────────────────────────────
    if "Volume" in df.columns and len(clean) >= 20:
        vt = volume_trend(clean)
        if   vt ==  1: signals.append(("Volume",  1, 1, ("signals.volume_up", {})))
        elif vt == -1: signals.append(("Volume", -1, 1, ("signals.volume_down", {})))
        else:          signals.append(("Volume",  0, 1, ("signals.volume_normal", {})))

    # ── 52-week range ────────────────────────────────
    w52h = stock_info.get("fiftyTwoWeekHigh")
    w52l = stock_info.get("fiftyTwoWeekLow")
    if w52h and w52l and w52h > w52l:
        p52 = (price - w52l) / (w52h - w52l)
        if   p52 < 0.20: signals.append(("52W Range",  1, 2, ("signals.range_52w_low", {})))
        elif p52 < 0.40: signals.append(("52W Range",  1, 1, ("signals.range_52w_lower", {})))
        elif p52 > 0.85: signals.append(("52W Range", -1, 2, ("signals.range_52w_high", {})))
        elif p52 > 0.65: signals.append(("52W Range", -1, 1, ("signals.range_52w_upper", {})))
        else:            signals.append(("52W Range",  0, 1, ("signals.range_52w_mid", {})))

    # ── News sentiment ───────────────────────────────
    ns, news_label, news_detail = analyze_news_sentiment(news_list)
    _news_map = {
         2: ( 1, 2, ("signals.news_very_positive", {})),
         1: ( 1, 1, ("signals.news_positive", {})),
         0: ( 0, 1, ("signals.news_neutral", {})),
        -1: (-1, 1, ("signals.news_negative", {})),
        -2: (-1, 2, ("signals.news_very_negative", {})),
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

    def _render_desc(d):
        # d can be a plain string or a tuple (key, params)
        if isinstance(d, tuple) and len(d) == 2:
            key, params = d
            try:
                return t(key, **params) if params else t(key)
            except Exception:
                return str(d)
        return str(d)

    if rec == "BUY":
        top_text = _render_desc(top_bull[0]) if top_bull else t("summary.buy_fallback")
        summary = t("summary.buy", bullish=len(buys), total=nc, detail=top_text)
    elif rec == "SELL":
        top_text = _render_desc(top_bear[0]) if top_bear else t("summary.sell_fallback")
        summary = t("summary.sell", bearish=len(sells), total=nc, detail=top_text)
    else:
        summary = t("summary.hold", bullish=len(buys), bearish=len(sells), total=nc)

    return rec, conf, risk, summary, signals, news_label, news_detail, rsi, sma20, sma50, mom5, score_pct
