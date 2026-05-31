"""
Local development stub for the private analysis engine.

This server intentionally contains no proprietary recommendation or forecasting
logic. It only implements the API contract so the public Streamlit app can run
locally without connection errors.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


HOST = "localhost"
PORT = 8000


def _last_close(history: list[dict[str, Any]]) -> float:
    for row in reversed(history or []):
        value = row.get("Close")
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return 0.0


def _horizon_return_pct(horizon: int) -> float:
    """Deterministic demo-only movement so timeframe changes are visible."""
    if horizon <= 1:
        return 0.15
    if horizon <= 3:
        return 0.45
    if horizon <= 5:
        return 0.8
    if horizon <= 12:
        return 1.6
    if horizon <= 21:
        return 2.4
    return 6.0


def _forecast(payload: dict[str, Any]) -> dict[str, Any]:
    horizon = int(payload.get("horizon") or 12)
    last_price = _last_close(payload.get("history") or [])
    return_pct = _horizon_return_pct(horizon) if last_price else 0.0
    target_price = last_price * (1 + return_pct / 100) if last_price else 0.0
    dates = [
        (datetime.today() + timedelta(days=offset)).strftime("%Y-%m-%d")
        for offset in range(1, horizon + 1)
    ]
    values = [
        last_price + ((target_price - last_price) * step / horizon)
        for step in range(1, horizon + 1)
    ] if last_price else []

    return {
        "available": bool(last_price),
        "message": "Local development engine returned a horizon-aware demo forecast.",
        "horizon": horizon,
        "last_price": last_price or None,
        "model_target": target_price or None,
        "scenario_target": target_price or None,
        "model_return_pct": return_pct,
        "scenario_return_pct": return_pct,
        "trend_return_pct": 0.0,
        "news_label": "Neutral",
        "direction": "Bullish" if return_pct >= 1 else "Neutral",
        "dates": dates,
        "model_values": values,
        "scenario_values": values,
        "lower_80": [value * 0.98 for value in values],
        "upper_80": [value * 1.02 for value in values],
    }


def _recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    forecast = payload.get("forecast") if isinstance(payload.get("forecast"), dict) else {}
    return_pct = float(forecast.get("scenario_return_pct") or 0)
    recommendation = "BUY" if return_pct >= 5 else "HOLD"
    confidence = 62 if recommendation == "BUY" else 50
    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "risk": "Medium",
        "summary": (
            "Local development engine is running. This is a demo stub response "
            "and does not include proprietary analysis logic."
        ),
        "signals": [
            [
                "Development Forecast",
                1 if recommendation == "BUY" else 0,
                1,
                f"Demo forecast return for this horizon is {return_pct:+.2f}%.",
            ]
        ],
        "news_label": "Neutral",
        "news_detail": [],
        "rsi": 50.0,
        "sma20": None,
        "sma50": None,
        "mom5": 0.0,
        "score_pct": return_pct,
    }


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, status=400)
            return

        if self.path == "/forecast":
            self._send_json(_forecast(payload))
            return

        if self.path == "/recommendation":
            self._send_json(_recommendation(payload))
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"ok": True})
            return
        self._send_json({"error": "Not found"}, status=404)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Development analysis engine running at http://{HOST}:{PORT}")
    print("Endpoints: POST /forecast, POST /recommendation, GET /health")
    server.serve_forever()


if __name__ == "__main__":
    main()
