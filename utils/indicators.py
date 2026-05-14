"""
Technical indicator calculations.
All functions accept a pandas Series of closing prices
and return a Series (or tuple of Series).
"""

import pandas as pd
import numpy as np


def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(window).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Returns (macd_line, signal_line)."""
    macd   = series.ewm(span=12, adjust=False).mean() - series.ewm(span=26, adjust=False).mean()
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def calculate_bollinger(series: pd.Series, window: int = 20) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (upper_band, lower_band, band_position 0–1)."""
    sma   = series.rolling(window).mean()
    std   = series.rolling(window).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    pos   = (series - lower) / (upper - lower)
    return upper, lower, pos


def volume_trend(df: pd.DataFrame) -> int:
    """
    +1 = high volume on up days (bullish conviction)
    -1 = high volume on down days (bearish conviction)
     0 = normal / no signal
    """
    if len(df) < 20:
        return 0
    avg_recent = df["Volume"].iloc[-5:].mean()
    avg_long   = df["Volume"].iloc[-20:].mean()
    price_chg  = df["Close"].iloc[-1] - df["Close"].iloc[-5]
    if avg_recent > avg_long * 1.2:
        return 1 if price_chg > 0 else -1
    return 0


def get_last_close(df: pd.DataFrame, stock_info: dict) -> float:
    """
    NaN-safe last close price.
    Falls back to stock_info fields if the DataFrame contains NaNs.
    """
    clean = df.dropna(subset=["Close"])
    if not clean.empty:
        val = clean["Close"].iloc[-1]
        if not np.isnan(val):
            return val
    for key in ("regularMarketPrice", "currentPrice", "previousClose", "open"):
        val = stock_info.get(key)
        if val is not None:
            try:
                fval = float(val)
                if not np.isnan(fval):
                    return fval
            except Exception:
                pass
    return float("nan")
