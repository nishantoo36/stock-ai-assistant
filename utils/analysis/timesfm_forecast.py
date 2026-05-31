"""
TimesFM-based stock forecasting.

TimesFM forecasts the univariate price series. News sentiment and recent trend are
applied as a small scenario tilt on top of the model baseline because TimesFM does
not directly consume raw news text.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from utils.analysis.sentiment import analyze_news_sentiment


MIN_CONTEXT_POINTS = 32
DEFAULT_HORIZON = 12
FORECAST_HORIZONS = {
    "1D": 1,
    "3D": 3,
    "1W": 5,
    "12D": 12,
    "1M": 21,
    "1Y": 252,
}
MAX_CONTEXT = 1024
MODEL_ID = "google/timesfm-2.5-200m-pytorch"


@dataclass(frozen=True)
class TimesFMForecast:
    available: bool
    message: str
    message_key: str | None = None
    message_params: dict | None = None
    horizon: int = DEFAULT_HORIZON
    last_price: float | None = None
    model_target: float | None = None
    scenario_target: float | None = None
    model_return_pct: float | None = None
    scenario_return_pct: float | None = None
    trend_return_pct: float | None = None
    news_label: str = "Neutral"
    direction: str = "Neutral"
    dates: list[pd.Timestamp] | None = None
    model_values: list[float] | None = None
    scenario_values: list[float] | None = None
    lower_80: list[float] | None = None
    upper_80: list[float] | None = None


def _unavailable(message_key: str, fallback: str, **params) -> TimesFMForecast:
    return TimesFMForecast(False, fallback, message_key, params or None)


def _is_forecast_enabled() -> bool:
    return os.getenv("TIMESFM_ENABLED", "true").strip().lower() not in {"0", "false", "no"}


def normalize_forecast_horizon(horizon: int | str | None) -> int:
    try:
        parsed = int(horizon) if horizon is not None else DEFAULT_HORIZON
    except (TypeError, ValueError):
        parsed = DEFAULT_HORIZON

    valid = set(FORECAST_HORIZONS.values())
    return parsed if parsed in valid else DEFAULT_HORIZON


def _history_close(df: pd.DataFrame) -> tuple[pd.Series, pd.Timestamp | None]:
    if df is None or df.empty or "Close" not in df.columns:
        return pd.Series(dtype="float64"), None

    clean = df.copy()
    date_col = "Date" if "Date" in clean.columns else "Datetime" if "Datetime" in clean.columns else None
    if date_col:
        clean[date_col] = pd.to_datetime(clean[date_col], errors="coerce")
        clean = clean.dropna(subset=[date_col]).sort_values(date_col)
        last_date = clean[date_col].iloc[-1] if not clean.empty else None
    else:
        idx = pd.to_datetime(clean.index, errors="coerce")
        clean = clean.loc[idx.notna()].copy()
        clean.index = idx[idx.notna()]
        clean = clean.sort_index()
        last_date = clean.index[-1] if not clean.empty else None

    close = pd.to_numeric(clean["Close"], errors="coerce").replace([np.inf, -np.inf], np.nan)
    close = close.ffill().dropna()
    close = close[close > 0]
    return close.astype("float32"), pd.Timestamp(last_date) if last_date is not None else None


def _recent_trend_pct(close: pd.Series) -> float:
    if len(close) < 21:
        return 0.0

    base = float(close.iloc[-21])
    latest = float(close.iloc[-1])
    if base <= 0:
        return 0.0
    return ((latest - base) / base) * 100


def _scenario_adjustment_pct(news_score: int, trend_return_pct: float) -> float:
    news_tilt = news_score * 0.4
    trend_tilt = float(np.clip(trend_return_pct * 0.15, -1.5, 1.5))
    return float(np.clip(news_tilt + trend_tilt, -2.5, 2.5))


def _return_pct(target: float, base: float) -> float:
    return ((target - base) / base) * 100 if base > 0 else 0.0


def _direction_from_return(return_pct: float) -> str:
    if return_pct >= 1:
        return "Bullish"
    if return_pct <= -1:
        return "Bearish"
    return "Neutral"


def _future_business_dates(last_date: pd.Timestamp | None, horizon: int) -> list[pd.Timestamp]:
    start_date = (last_date or pd.Timestamp.today()).normalize()
    return list(pd.bdate_range(start=start_date + pd.offsets.BDay(1), periods=horizon))


def _quantile_band(quantiles: np.ndarray) -> tuple[list[float] | None, list[float] | None]:
    if quantiles.ndim != 2 or quantiles.shape[1] <= 9:
        return None, None
    return quantiles[:, 1].tolist(), quantiles[:, 9].tolist()


def _build_scenario(point: np.ndarray, news_list: list[dict], close: pd.Series) -> tuple:
    news_score, news_label, _ = analyze_news_sentiment(news_list)
    trend_return_pct = _recent_trend_pct(close)
    adjustment_pct = _scenario_adjustment_pct(news_score, trend_return_pct)
    ramp = np.linspace(adjustment_pct / len(point), adjustment_pct, len(point)) / 100
    scenario = point * (1 + ramp)
    return scenario, news_label, trend_return_pct


@st.cache_resource(show_spinner=False)
def _load_timesfm_model():
    import torch
    import timesfm

    torch.set_float32_matmul_precision("high")
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(MODEL_ID)
    model.compile(
        timesfm.ForecastConfig(
            max_context=MAX_CONTEXT,
            max_horizon=256,
            normalize_inputs=True,
            use_continuous_quantile_head=True,
            force_flip_invariance=True,
            infer_is_positive=True,
            fix_quantile_crossing=True,
        )
    )
    return model


def _run_timesfm(context: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray] | TimesFMForecast:
    try:
        model = _load_timesfm_model()
        point_forecast, quantile_forecast = model.forecast(
            horizon=horizon,
            inputs=[context],
        )
    except ModuleNotFoundError as exc:
        return _unavailable(
            "forecast.messages.missing_dependency",
            f"Missing TimesFM dependency: {exc.name}. Install with `pip install 'timesfm[torch]'`.",
            dependency=exc.name or "unknown",
        )
    except Exception as exc:
        return _unavailable(
            "forecast.messages.failed",
            f"TimesFM forecast failed: {exc}",
            error=str(exc),
        )

    return np.asarray(point_forecast[0], dtype=float), np.asarray(quantile_forecast[0], dtype=float)


def build_timesfm_forecast(
    df: pd.DataFrame,
    news_list: list[dict],
    horizon: int = DEFAULT_HORIZON,
) -> TimesFMForecast:
    horizon = normalize_forecast_horizon(horizon)

    if not _is_forecast_enabled():
        return _unavailable(
            "forecast.messages.disabled",
            "TimesFM forecasting is disabled by TIMESFM_ENABLED.",
        )

    close, last_date = _history_close(df)
    if len(close) < MIN_CONTEXT_POINTS:
        return _unavailable(
            "forecast.messages.insufficient_data",
            f"Need at least {MIN_CONTEXT_POINTS} valid daily closes for TimesFM; found {len(close)}.",
            required=MIN_CONTEXT_POINTS,
            found=len(close),
        )

    context = close.tail(MAX_CONTEXT).to_numpy(dtype=np.float32)
    model_result = _run_timesfm(context, horizon)
    if isinstance(model_result, TimesFMForecast):
        return model_result

    point, quantiles = model_result
    if point.shape[0] != horizon or np.isnan(point).any():
        return _unavailable(
            "forecast.messages.invalid_output",
            "TimesFM returned an invalid forecast shape or NaN values.",
        )

    last_price = float(close.iloc[-1])
    model_target = float(point[-1])
    model_return_pct = _return_pct(model_target, last_price)

    scenario, news_label, trend_return_pct = _build_scenario(point, news_list, close)
    scenario_target = float(scenario[-1])
    scenario_return_pct = _return_pct(scenario_target, last_price)
    lower_80, upper_80 = _quantile_band(quantiles)


    return TimesFMForecast(
        available=True,
        message="TimesFM 2.5 forecast generated from daily close history.",
        message_key="forecast.messages.ready",
        horizon=horizon,
        last_price=last_price,
        model_target=model_target,
        scenario_target=scenario_target,
        model_return_pct=float(model_return_pct),
        scenario_return_pct=float(scenario_return_pct),
        trend_return_pct=float(trend_return_pct),
        news_label=news_label,
        direction=_direction_from_return(scenario_return_pct),
        dates=_future_business_dates(last_date, horizon),
        model_values=point.tolist(),
        scenario_values=scenario.tolist(),
        lower_80=lower_80,
        upper_80=upper_80,
    )
