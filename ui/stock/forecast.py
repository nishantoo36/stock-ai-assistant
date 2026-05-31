"""
TimesFM forecast panel.
"""

from __future__ import annotations

from html import escape

import plotly.graph_objects as go
import streamlit as st

from utils.market.forex import convert_price
from utils.platform.i18n import t
from utils.analysis.timesfm_forecast import (
    FORECAST_HORIZONS,
    TimesFMForecast,
    normalize_forecast_horizon,
)


def _horizon_label(horizon: int) -> str:
    key = next((label for label, days in FORECAST_HORIZONS.items() if days == horizon), f"{horizon}D")
    return t(f"forecast.horizons.{key.lower()}", days=horizon)


def render_forecast_horizon_selector() -> int:
    horizon = normalize_forecast_horizon(st.session_state.get("forecast_horizon"))
    st.session_state.forecast_horizon = horizon

    st.markdown(
        f"""
        <style>
        .forecast-horizon-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 10px 12px;
            margin: 8px 0 10px;
        }}
        .forecast-horizon-title {{
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 2px;
        }}
        .forecast-horizon-help {{
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.4;
            margin-bottom: 0;
        }}
        @media (max-width: 640px) {{
            .forecast-horizon-card {{
                padding: 8px 10px;
                margin: 4px 0 8px;
            }}
            .forecast-horizon-help {{
                display: none;
            }}
        }}
        </style>
        <div class="forecast-horizon-card">
            <div class="forecast-horizon-title">{t("forecast.horizon_title")}</div>
            <div class="forecast-horizon-help">
                {t("forecast.horizon_help")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected = st.selectbox(
        t("forecast.horizon_selector"),
        list(FORECAST_HORIZONS.values()),
        index=list(FORECAST_HORIZONS.values()).index(horizon),
        format_func=_horizon_label,
        key="forecast_horizon_picker",
        label_visibility="collapsed",
    )
    if selected and selected != st.session_state.forecast_horizon:
        st.session_state.forecast_horizon = selected
        st.rerun()
    return st.session_state.forecast_horizon


def _forecast_message(forecast: TimesFMForecast) -> str:
    if forecast.message_key:
        return t(forecast.message_key, **(forecast.message_params or {}))
    return forecast.message


def _translated_direction(direction: str) -> str:
    return t(f"forecast.directions.{direction.lower()}")


def _conversion_rate(source_currency: str, target_currency: str) -> float:
    _, rate = convert_price(1.0, source_currency, target_currency)
    return rate


def _convert_optional(value: float | None, rate: float) -> float | None:
    if value is None:
        return None
    return float(value) * rate


def _convert_series(values: list[float] | None, rate: float) -> list[float] | None:
    if not values:
        return None
    return [_convert_optional(v, rate) for v in values]


def _fmt_money(value: float | None, symbol: str) -> str:
    return f"{symbol}{value:,.2f}" if value is not None else t("common.unavailable")


def _fmt_pct(value: float | None) -> str:
    return f"{value:+.2f}%" if value is not None else t("common.unavailable")


def _risk_label(risk: str) -> str:
    key = {
        "High": "risk.high",
        "Low-Medium": "risk.low_medium",
        "Low–Medium": "risk.low_medium",
        "Medium": "risk.medium",
    }.get(risk)
    return t(key) if key else risk


def _recommendation_color(rec: str) -> tuple[str, str]:
    return {
        "BUY": ("#22c55e", "rgba(34,197,94,0.08)"),
        "SELL": ("#ef4444", "rgba(239,68,68,0.08)"),
        "HOLD": ("#f59e0b", "rgba(245,158,11,0.08)"),
    }[rec]


def _converted_forecast_values(
    forecast: TimesFMForecast,
    source_currency: str,
    display_currency: str,
) -> dict:
    fx_rate = _conversion_rate(source_currency, display_currency)
    return {
        "model_target": _convert_optional(forecast.model_target, fx_rate),
        "scenario_target": _convert_optional(forecast.scenario_target, fx_rate),
        "scenario_values": _convert_series(forecast.scenario_values, fx_rate),
        "lower_80": _convert_series(forecast.lower_80, fx_rate),
        "upper_80": _convert_series(forecast.upper_80, fx_rate),
    }


def render_ai_outlook_summary(
    rec: str,
    confidence: int,
    risk: str,
    forecast: TimesFMForecast,
    source_currency: str,
    display_currency: str,
    currency_symbol: str,
) -> None:
    rec_color, rec_bg = _recommendation_color(rec)
    rec_label = t(f"recommendations.{rec.lower()}")
    horizon_label = _horizon_label(forecast.horizon)
    direction = _translated_direction(forecast.direction)

    if forecast.available:
        values = _converted_forecast_values(forecast, source_currency, display_currency)
        target = _fmt_money(values["scenario_target"], currency_symbol)
        change = _fmt_pct(forecast.scenario_return_pct)
        reason_key = f"forecast.outlook_reason_{rec.lower()}"
        reason = t(reason_key, direction=direction.lower(), change=change)
    else:
        target = t("common.unavailable")
        change = t("common.unavailable")
        reason = _forecast_message(forecast)

    st.markdown(
        f"""
        <style>
        .ai-outlook-card {{
            background: linear-gradient(135deg, rgba(17,24,39,0.98), rgba(15,23,42,0.92));
            border: 1px solid var(--border);
            border-left: 4px solid {rec_color};
            border-radius: 14px;
            padding: 14px;
            margin: 10px 0 8px;
        }}
        .ai-outlook-top {{
            display: grid;
            grid-template-columns: minmax(170px, 0.42fr) 1fr;
            gap: 12px;
            align-items: center;
        }}
        .ai-outlook-eyebrow {{
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .ai-outlook-rec {{
            color: {rec_color};
            background: {rec_bg};
            border: 1px solid {rec_color}33;
            border-radius: 10px;
            padding: 12px 14px;
            font-size: clamp(1.55rem, 3vw, 2rem);
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1;
        }}
        .ai-outlook-main {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
        }}
        .ai-outlook-kpi {{
            background: rgba(15,23,42,0.72);
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 10px;
            padding: 9px 10px;
            min-height: 64px;
        }}
        .ai-outlook-kpi-label {{
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 700;
            letter-spacing: .06em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .ai-outlook-kpi-value {{
            color: var(--text);
            font-size: clamp(0.98rem, 2vw, 1.16rem);
            font-weight: 750;
            letter-spacing: -0.02em;
        }}
        .ai-outlook-reason {{
            color: #94a3b8;
            font-size: 0.8rem;
            line-height: 1.45;
            margin-top: 8px;
        }}
        @media (max-width: 640px) {{
            .ai-outlook-card {{
                padding: 10px;
                margin-top: 6px;
            }}
            .ai-outlook-top {{
                grid-template-columns: 1fr;
                gap: 8px;
            }}
            .ai-outlook-rec {{
                padding: 10px 12px;
                font-size: 1.55rem;
            }}
            .ai-outlook-main {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 7px;
            }}
            .ai-outlook-kpi {{
                padding: 7px 8px;
                min-height: 54px;
            }}
            .ai-outlook-secondary {{
                display: none;
            }}
            .ai-outlook-reason {{
                display: none;
            }}
        }}
        </style>
        <div class="ai-outlook-card">
            <div class="ai-outlook-top">
                <div>
                    <div class="ai-outlook-eyebrow">{escape(t("forecast.outlook_title"))}</div>
                    <div class="ai-outlook-rec">{escape(rec_label)}</div>
                </div>
                <div>
                    <div class="ai-outlook-main">
                        <div class="ai-outlook-kpi">
                            <div class="ai-outlook-kpi-label">{escape(t("forecast.expected_price", horizon=horizon_label))}</div>
                            <div class="ai-outlook-kpi-value">{escape(target)}</div>
                        </div>
                        <div class="ai-outlook-kpi">
                            <div class="ai-outlook-kpi-label">{escape(t("forecast.expected_change"))}</div>
                            <div class="ai-outlook-kpi-value">{escape(change)}</div>
                        </div>
                        <div class="ai-outlook-kpi ai-outlook-secondary">
                            <div class="ai-outlook-kpi-label">{escape(t("analysis.metric_confidence"))}</div>
                            <div class="ai-outlook-kpi-value">{confidence}%</div>
                        </div>
                        <div class="ai-outlook-kpi ai-outlook-secondary">
                            <div class="ai-outlook-kpi-label">{escape(t("analysis.metric_risk"))}</div>
                            <div class="ai-outlook-kpi-value">{escape(_risk_label(risk))}</div>
                        </div>
                    </div>
                    <div class="ai-outlook-reason">{escape(reason)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_forecast_detail_body(
    forecast: TimesFMForecast,
    source_currency: str,
    display_currency: str,
    currency_symbol: str,
) -> None:
    if not forecast.available:
        _render_unavailable_forecast(forecast)
        return

    values = _converted_forecast_values(forecast, source_currency, display_currency)
    _render_forecast_metrics(forecast, values, currency_symbol)
    fig = _build_forecast_chart(forecast, values, display_currency, currency_symbol)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})
    _render_method_note(forecast)


@st.dialog("Forecast details", width="large")
def _forecast_details_dialog(
    forecast: TimesFMForecast,
    source_currency: str,
    display_currency: str,
    currency_symbol: str,
) -> None:
    _render_forecast_detail_body(forecast, source_currency, display_currency, currency_symbol)


def _render_unavailable_forecast(forecast: TimesFMForecast) -> None:
    st.info(_forecast_message(forecast))
    st.caption(t("forecast.install_note"))


def _render_forecast_metrics(forecast: TimesFMForecast, values: dict, currency_symbol: str) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric(
        t("forecast.scenario_target"),
        _fmt_money(values["scenario_target"], currency_symbol),
        _fmt_pct(forecast.scenario_return_pct),
    )
    c2.metric(
        t("forecast.model_target"),
        _fmt_money(values["model_target"], currency_symbol),
        _fmt_pct(forecast.model_return_pct),
    )
    c3.metric(t("forecast.direction"), _translated_direction(forecast.direction))


def _add_interval_band(fig: go.Figure, forecast: TimesFMForecast, values: dict) -> None:
    if not values["lower_80"] or not values["upper_80"]:
        return

    fig.add_trace(
        go.Scatter(
            x=forecast.dates,
            y=values["upper_80"],
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast.dates,
            y=values["lower_80"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(56,189,248,0.16)",
            line=dict(width=0),
            name=t("forecast.interval"),
            hoverinfo="skip",
        )
    )


def _build_forecast_chart(
    forecast: TimesFMForecast,
    values: dict,
    display_currency: str,
    currency_symbol: str,
) -> go.Figure:
    fig = go.Figure()
    _add_interval_band(fig, forecast, values)
    fig.add_trace(
        go.Scatter(
            x=forecast.dates,
            y=values["scenario_values"],
            mode="lines+markers",
            name=t("forecast.scenario_line"),
            line=dict(width=2.6, color="#38bdf8"),
            marker=dict(size=6, color="#38bdf8"),
            hovertemplate=f"{display_currency} %{{y:,.2f}} | %{{x|%b %d, %Y}}<extra></extra>",
        )
    )
    fig.update_layout(
        height=280,
        margin=dict(l=4, r=4, t=8, b=4),
        hovermode="x",
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#94a3b8", size=11),
        xaxis=dict(showgrid=False, showline=False, fixedrange=True),
        yaxis=dict(showgrid=False, showline=False, fixedrange=True, tickprefix=currency_symbol),
    )
    return fig


def _render_method_note(forecast: TimesFMForecast) -> None:
    st.caption(
        t(
            "forecast.method_note",
            horizon=forecast.horizon,
            news=forecast.news_label,
            trend=_fmt_pct(forecast.trend_return_pct),
        )
    )


def render_timesfm_forecast(
    forecast: TimesFMForecast,
    source_currency: str,
    display_currency: str,
    currency_symbol: str,
) -> None:
    if st.button(t("forecast.view_details"), key=f"forecast_details_{forecast.horizon}", width="stretch"):
        _forecast_details_dialog(forecast, source_currency, display_currency, currency_symbol)
