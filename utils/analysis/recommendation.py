"""
Recommendation integration.

The public repository delegates proprietary BUY/HOLD/SELL scoring to a private
analysis service. This module preserves the UI-facing return contract.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pandas as pd

from services.analysis_engine import AnalysisEngineError, dataframe_payload, post_engine
from utils.analysis.timesfm_forecast import TimesFMForecast


RecommendationResult = tuple[
    str,
    int,
    str,
    str,
    list,
    str,
    list,
    float,
    float | None,
    float | None,
    float,
    float,
]


def _fallback_result(reason: str) -> RecommendationResult:
    summary = (
        "Private analysis engine is not configured or unavailable.\n\n"
        f"{reason}\n\n"
        "Configure STOCK_AI_ENGINE_URL and STOCK_AI_ENGINE_TOKEN to enable live recommendations."
    )
    return "HOLD", 50, "Medium", summary, [], "Neutral", [], 50.0, None, None, 0.0, 0.0


def _coerce_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _coerce_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _result_from_response(data: dict[str, Any]) -> RecommendationResult:
    rec = str(data.get("rec") or data.get("recommendation") or "HOLD").upper()
    if rec not in {"BUY", "HOLD", "SELL"}:
        rec = "HOLD"

    return (
        rec,
        int(_coerce_float(data.get("confidence"), 50)),
        str(data.get("risk") or "Medium"),
        str(data.get("summary") or "Private analysis engine returned no summary."),
        data.get("signals") if isinstance(data.get("signals"), list) else [],
        str(data.get("news_label") or "Neutral"),
        data.get("news_detail") if isinstance(data.get("news_detail"), list) else [],
        _coerce_float(data.get("rsi"), 50.0),
        _coerce_optional_float(data.get("sma20")),
        _coerce_optional_float(data.get("sma50")),
        _coerce_float(data.get("mom5"), 0.0),
        _coerce_float(data.get("score_pct"), 0.0),
    )


def generate_recommendation(
    df: pd.DataFrame,
    stock_info: dict,
    news_list: list,
    forecast: TimesFMForecast | None = None,
) -> RecommendationResult:
    payload = {
        "history": dataframe_payload(df),
        "stock_info": stock_info,
        "news": news_list,
        "forecast": asdict(forecast) if forecast else None,
    }

    try:
        response = post_engine("/recommendation", payload)
    except AnalysisEngineError as exc:
        return _fallback_result(str(exc))

    return _result_from_response(response)
