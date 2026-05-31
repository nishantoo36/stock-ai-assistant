"""
Client for the private stock analysis engine.

The public app intentionally keeps proprietary scoring and forecasting logic out
of this repository. Configure STOCK_AI_ENGINE_URL and STOCK_AI_ENGINE_TOKEN to
enable the private service.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


ENGINE_URL_ENV = "STOCK_AI_ENGINE_URL"
ENGINE_TOKEN_ENV = "STOCK_AI_ENGINE_TOKEN"
ENGINE_TIMEOUT_SECONDS = 45


class AnalysisEngineError(RuntimeError):
    """Raised when the private analysis engine is not configured or unavailable."""


def _setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        import streamlit as st

        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def _engine_url() -> str:
    return _setting(ENGINE_URL_ENV).rstrip("/")


def is_engine_configured() -> bool:
    return bool(_engine_url())


def dataframe_payload(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []

    payload = df.reset_index().copy()
    for column in payload.columns:
        if pd.api.types.is_datetime64_any_dtype(payload[column]):
            payload[column] = payload[column].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return payload.where(pd.notna(payload), None).to_dict(orient="records")


def post_engine(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    base_url = _engine_url()
    if not base_url:
        raise AnalysisEngineError(
            f"Private analysis engine is not configured. Set {ENGINE_URL_ENV}."
        )

    token = _setting(ENGINE_TOKEN_ENV)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(payload, default=str).encode("utf-8")
    request = Request(f"{base_url}/{path.lstrip('/')}", data=body, headers=headers, method="POST")

    try:
        with urlopen(request, timeout=ENGINE_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AnalysisEngineError(f"Private analysis engine returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AnalysisEngineError(f"Private analysis engine is unavailable: {exc.reason}") from exc
    except TimeoutError as exc:
        raise AnalysisEngineError("Private analysis engine timed out.") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnalysisEngineError("Private analysis engine returned invalid JSON.") from exc

    if not isinstance(parsed, dict):
        raise AnalysisEngineError("Private analysis engine returned an invalid response.")
    return parsed
