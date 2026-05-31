"""
Public-safe market data helpers.

Technical analysis logic is provided by the private analysis service.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def get_last_close(df: pd.DataFrame, stock_info: dict) -> float:
    for key in ("regularMarketPrice", "currentPrice"):
        value = stock_info.get(key)
        if value is None:
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if not np.isnan(parsed) and parsed > 0:
            return parsed

    if df is not None and not df.empty and "Close" in df.columns:
        clean = df.dropna(subset=["Close"])
        if not clean.empty:
            value = clean["Close"].iloc[-1]
            if not np.isnan(value):
                return float(value)

    for key in ("previousClose", "open"):
        value = stock_info.get(key)
        if value is None:
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if not np.isnan(parsed):
            return parsed

    return float("nan")
