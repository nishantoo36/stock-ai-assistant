"""
TimesFM forecast panel.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from utils.forex import convert_price
from utils.i18n import t
from utils.timesfm_forecast import TimesFMForecast


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


def render_timesfm_forecast(
    forecast: TimesFMForecast,
    source_currency: str,
    display_currency: str,
    currency_symbol: str,
) -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(t("forecast.title"), expanded=forecast.available):
        if not forecast.available:
            st.info(forecast.message)
            st.caption(t("forecast.install_note"))
            return

        fx_rate = _conversion_rate(source_currency, display_currency)
        model_target = _convert_optional(forecast.model_target, fx_rate)
        scenario_target = _convert_optional(forecast.scenario_target, fx_rate)
        scenario_values = _convert_series(forecast.scenario_values, fx_rate)
        lower_80 = _convert_series(forecast.lower_80, fx_rate)
        upper_80 = _convert_series(forecast.upper_80, fx_rate)

        c1, c2, c3 = st.columns(3)
        c1.metric(t("forecast.scenario_target"), _fmt_money(scenario_target, currency_symbol), _fmt_pct(forecast.scenario_return_pct))
        c2.metric(t("forecast.model_target"), _fmt_money(model_target, currency_symbol), _fmt_pct(forecast.model_return_pct))
        c3.metric(t("forecast.direction"), forecast.direction)

        fig = go.Figure()
        if lower_80 and upper_80:
            fig.add_trace(
                go.Scatter(
                    x=forecast.dates,
                    y=upper_80,
                    mode="lines",
                    line=dict(width=0),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=forecast.dates,
                    y=lower_80,
                    mode="lines",
                    fill="tonexty",
                    fillcolor="rgba(56,189,248,0.16)",
                    line=dict(width=0),
                    name=t("forecast.interval"),
                    hoverinfo="skip",
                )
            )

        fig.add_trace(
            go.Scatter(
                x=forecast.dates,
                y=scenario_values,
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
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})

        st.caption(
            t(
                "forecast.method_note",
                horizon=forecast.horizon,
                news=forecast.news_label,
                trend=_fmt_pct(forecast.trend_return_pct),
            )
        )
