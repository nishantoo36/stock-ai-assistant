"""
Price chart with SMA20/SMA50 overlay and custom HTML legend.
"""

from datetime import timedelta

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.platform.i18n import t

CHART_PERIODS = ["1D", "1W", "1M", "3M", "6M", "1Y", "3Y", "5Y", "All"]
INTRADAY      = {"1D", "1W"}
X_WINDOWS = {
    "1D":  (timedelta(hours=24),  timedelta(hours=3)),
    "1W":  (timedelta(days=7),    timedelta(days=1)),
    "1M":  (timedelta(days=30),   timedelta(days=3)),
    "3M":  (timedelta(days=90),   timedelta(days=7)),
    "6M":  (timedelta(days=180),  timedelta(days=14)),
    "1Y":  (timedelta(days=365),  timedelta(days=30)),
    "3Y":  (timedelta(days=365 * 3), timedelta(days=90)),
    "5Y":  (timedelta(days=365 * 5), timedelta(days=120)),
}


def render_period_selector() -> str:
    if st.session_state.chart_period not in CHART_PERIODS:
        st.session_state.chart_period = "1D"

    current = st.segmented_control(
        t("analysis.time_range"),
        CHART_PERIODS,
        default=st.session_state.chart_period,
        key="chart_period_picker",
        label_visibility="collapsed",
        width="stretch",
    )
    if current and current != st.session_state.chart_period:
        st.session_state.chart_period = current
        st.rerun()

    return st.session_state.chart_period


def _x_values(df_plot: pd.DataFrame, exchange_timezone: str | None = None) -> pd.Series:
    for column in ("Datetime", "Date"):
        if column in df_plot.columns:
            values = pd.to_datetime(df_plot[column], errors="coerce")
            if values.notna().any():
                break
    else:
        values = pd.Series(pd.to_datetime(df_plot.index, errors="coerce"), index=df_plot.index)

    if exchange_timezone:
        try:
            if getattr(values.dt, "tz", None) is not None:
                values = values.dt.tz_convert(exchange_timezone).dt.tz_localize(None)
        except Exception:
            pass

    return values if isinstance(values, pd.Series) else pd.Series(values, index=df_plot.index)


def _filter_window(df_plot: pd.DataFrame, x_values: pd.Series, period: str) -> tuple[pd.DataFrame, pd.Series]:
    if period not in X_WINDOWS:
        return df_plot, x_values

    clean = x_values.dropna()
    if clean.empty:
        return df_plot, x_values

    window, _ = X_WINDOWS[period]
    start = clean.max() - window
    mask = x_values >= start
    if not mask.any():
        return df_plot, x_values

    return df_plot.loc[mask].copy(), x_values.loc[mask]


def _x_axis_range(x_values: pd.Series, period: str) -> list | None:
    clean = x_values.dropna()
    if clean.empty:
        return None

    _, margin = X_WINDOWS.get(period, (None, None))
    if margin is None:
        return None

    start = clean.min() - margin
    end = clean.max() + margin
    return [start, end]


def render_chart(df_chart: pd.DataFrame, df_analysis: pd.DataFrame,
                 period: str, disp_curr: str,
                 previous_close: float | None = None,
                 exchange_timezone: str | None = None) -> None:
    intraday = period in INTRADAY
    df_plot  = (
        df_chart.dropna(subset=["Close"]) if not df_chart.empty
        else df_analysis.dropna(subset=["Close"])
    )
    if df_plot.empty:
        st.warning(t("chart.data_unavailable"))
        return

    x_values = _x_values(df_plot, exchange_timezone)
    df_plot, x_values = _filter_window(df_plot, x_values, period)
    x_range = _x_axis_range(x_values, period)
    close_values = df_plot["Close"].dropna()
    x_clean = x_values.dropna()
    if close_values.empty or x_clean.empty:
        st.warning(t("chart.data_unavailable"))
        return

    first_close = float(close_values.iloc[0])
    last_close = float(close_values.iloc[-1])
    reference_close = previous_close if previous_close else first_close
    line_color = "#22c55e" if last_close >= reference_close else "#ef4444"
    if "show_sma_hover" not in st.session_state:
        st.session_state.show_sma_hover = False
    show_sma_hover = bool(st.session_state.show_sma_hover)

    fig = go.Figure()

    if intraday:
        fig.add_trace(go.Scatter(
            x=x_values, y=df_plot["Close"],
            mode="lines+markers", name=t("chart.price"),
            line=dict(width=2.6, color=line_color),
            marker=dict(size=9, color=line_color, opacity=0),
            hovertemplate=f"{disp_curr} %{{y:,.2f}} | %{{x|%-I:%M %p}}<extra></extra>",
        ))
    else:
        s20 = df_plot["Close"].rolling(20).mean()
        s50 = df_plot["Close"].rolling(50).mean()
        s20_hover = (
            {"hovertemplate": f"{disp_curr} %{{y:,.2f}} | %{{x|%b %d, %Y}}<extra>SMA 20</extra>"}
            if show_sma_hover else {"hoverinfo": "skip"}
        )
        s50_hover = (
            {"hovertemplate": f"{disp_curr} %{{y:,.2f}} | %{{x|%b %d, %Y}}<extra>SMA 50</extra>"}
            if show_sma_hover else {"hoverinfo": "skip"}
        )
        fig.add_trace(go.Scatter(
            x=x_values, y=df_plot["Close"],
            mode="lines+markers", name=t("chart.price"),
            line=dict(width=2.6, color=line_color),
            marker=dict(size=9, color=line_color, opacity=0),
            hovertemplate=f"{disp_curr} %{{y:,.2f}} | %{{x|%b %d, %Y}}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=x_values, y=s20,
            mode="lines", name="SMA20",
            line=dict(dash="dash", width=1.2, color="#f59e0b"),
            **s20_hover,
        ))
        fig.add_trace(go.Scatter(
            x=x_values, y=s50,
            mode="lines", name="SMA50",
            line=dict(dash="dot", width=1.2, color="#a78bfa"),
            **s50_hover,
        ))

    if previous_close:
        fig.add_hline(
            y=previous_close,
            line_dash="dot",
            line_width=1.2,
            line_color="#64748b",
            opacity=0.85,
        )

    fig.add_trace(go.Scatter(
        x=[x_clean.iloc[-1]],
        y=[last_close],
        mode="markers",
        name=t("chart.price"),
        marker=dict(size=8, color=line_color, line=dict(width=1.5, color="#0a0e1a")),
        hoverinfo="skip",
    ))

    y_points = [df_plot["Close"].min(), df_plot["Close"].max()]
    if previous_close:
        y_points.append(previous_close)
    mn  = min(y_points)
    mx  = max(y_points)
    pad = max((mx - mn) * 0.12, 1)

    fig.update_layout(
        height=430,
        hovermode="x",
        hoverdistance=80,
        spikedistance=80,
        dragmode=False,
        margin=dict(l=4, r=4, t=14, b=10),
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(
            range=[mn - pad, mx + pad],
            fixedrange=True,
            showgrid=False,
            showticklabels=False,
            ticks="",
            showline=False,
            zeroline=False,
            showspikes=True,
            spikecolor="rgba(148,163,184,0.55)",
            spikedash="dot",
            spikethickness=1,
            spikemode="across",
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#94a3b8", size=11),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor="rgba(148,163,184,0.42)",
            zeroline=False,
            fixedrange=True,
            range=x_range,
            showticklabels=False,
            ticks="",
            showspikes=True,
            spikecolor="rgba(148,163,184,0.55)",
            spikedash="solid",
            spikethickness=1,
            spikemode="across",
        ),
        hoverlabel=dict(
            bgcolor="#0a0e1a",
            bordercolor="rgba(148,163,184,0.20)",
            font=dict(family="DM Sans, sans-serif", size=13, color="#e2e8f0"),
        ),
    )

    # Custom HTML legend above chart — no overlap with Plotly zoom controls
    if intraday:
        legend_html = f"""
        <div class="chart-legend">
            <span class="chart-legend-item">
                <span class="chart-line-swatch" style="background:{line_color}"></span>
                {t('chart.price_history')}
            </span>
            <span class="chart-legend-meta">{t('chart.price_axis', currency=disp_curr)}</span>
        </div>"""
    else:
        legend_html = f"""
        <div class="chart-legend">
            <span class="chart-legend-item">
                <span class="chart-line-swatch" style="background:{line_color}"></span>
                {t('chart.price_history')}
            </span>
            <span class="chart-legend-item">
                <span class="chart-line-swatch chart-line-swatch-dash"></span>
                {t('chart.sma_20')}
            </span>
            <span class="chart-legend-item">
                <span class="chart-line-swatch chart-line-swatch-dot"></span>
                {t('chart.sma_50')}
            </span>
            <span class="chart-legend-meta">{t('chart.price_axis', currency=disp_curr)}</span>
        </div>"""

    st.markdown(legend_html, unsafe_allow_html=True)
    if not intraday:
        st.toggle(t("chart.sma_hover"), key="show_sma_hover")
    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "scrollZoom": False,
            "doubleClick": False,
            "displayModeBar": False,
            "responsive": True,
        },
    )
