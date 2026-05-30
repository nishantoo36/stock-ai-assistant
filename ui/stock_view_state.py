"""
Pure helpers for stock detail screen state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from utils.forex import convert_price, get_currency_symbol
from utils.indicators import get_last_close


@dataclass(frozen=True)
class DisplayPriceState:
    current_price: float
    day_change: float | None
    day_change_pct: float | None
    previous_close: float | None
    display_currency: str
    currency_symbol: str
    fx_rate: float


def has_price_data(df: pd.DataFrame) -> bool:
    """Return True only if the DataFrame has a usable Close column with real values."""
    return (
        df is not None
        and not df.empty
        and "Close" in df.columns
        and df["Close"].notna().any()
    )


def analysis_frame(df_analysis: pd.DataFrame, df_chart: pd.DataFrame) -> pd.DataFrame:
    if df_analysis.empty or len(df_analysis) < 10:
        return df_chart
    return df_analysis


def _previous_close(info: dict, live: dict):
    return (
        live.get("previous_close")
        or info.get("previousClose")
        or info.get("regularMarketPreviousClose")
    )


def _period_change(
    df_chart: pd.DataFrame,
    current_price: float,
    fx_rate: float,
    info: dict,
    live: dict,
    period: str,
) -> tuple[float | None, float | None]:
    if np.isnan(current_price):
        return None, None

    def _change_from_base(base_raw):
        base = float(base_raw) * fx_rate
        if base <= 0:
            return None, None
        change = current_price - base
        return change, (change / base) * 100

    if period == "1D":
        prev = _previous_close(info, live)
        return _change_from_base(prev) if prev else (None, None)

    clean = df_chart.dropna(subset=["Close"]) if not df_chart.empty else pd.DataFrame()
    if len(clean) >= 2:
        first_raw = float(clean["Close"].iloc[0])
        if not np.isnan(first_raw) and first_raw > 0:
            return _change_from_base(first_raw)

    prev = _previous_close(info, live)
    return _change_from_base(prev) if prev else (None, None)


def build_display_price_state(
    df_chart: pd.DataFrame,
    df_analysis: pd.DataFrame,
    info: dict,
    live: dict,
    source_currency: str,
    selected_currency: str,
    period: str,
) -> DisplayPriceState:
    raw_price = live.get("price")
    if not raw_price or np.isnan(float(raw_price)):
        raw_price = get_last_close(df_analysis, info)

    current_price, fx_rate = convert_price(float(raw_price), source_currency, selected_currency)
    display_currency = selected_currency if selected_currency != "CurrencySelector" else source_currency
    currency_symbol = get_currency_symbol(display_currency)
    day_change, day_change_pct = _period_change(
        df_chart,
        current_price,
        fx_rate,
        info,
        live,
        period,
    )

    prev_raw = _previous_close(info, live)
    previous_close = None
    if prev_raw:
        previous_close, _ = convert_price(float(prev_raw), source_currency, selected_currency)

    return DisplayPriceState(
        current_price=current_price,
        day_change=day_change,
        day_change_pct=day_change_pct,
        previous_close=previous_close,
        display_currency=display_currency,
        currency_symbol=currency_symbol,
        fx_rate=fx_rate,
    )
