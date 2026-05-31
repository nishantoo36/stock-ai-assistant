"""Google Finance-style price chart card."""

from datetime import timedelta
from html import escape
import math

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


def _is_light_theme() -> bool:
    return st.get_option("theme.base") == "light"


def _chart_colors() -> dict[str, str]:
    if _is_light_theme():
        return {
            "paper": "#ffffff",
            "plot": "#ffffff",
            "grid": "rgba(218,220,224,0.55)",
            "axis": "#80868b",
            "tick": "#202124",
            "muted": "#5f6368",
            "hover_bg": "#ffffff",
            "hover_border": "#dadce0",
            "marker_border": "#ffffff",
            "previous": "#777777",
        }

    return {
        "paper": "rgba(0,0,0,0)",
        "plot": "rgba(0,0,0,0)",
        "grid": "rgba(148,163,184,0.18)",
        "axis": "rgba(148,163,184,0.42)",
        "tick": "#e2e8f0",
        "muted": "#94a3b8",
        "hover_bg": "#111827",
        "hover_border": "#334155",
        "marker_border": "#0a0e1a",
        "previous": "#94a3b8",
    }


def render_period_selector() -> str:
    if st.session_state.chart_period not in CHART_PERIODS:
        st.session_state.chart_period = "1D"

    st.markdown(
        """
        <style>
        div[data-testid="stSegmentedControl"] {
            margin: 0;
        }
        div[data-testid="stSegmentedControl"] label {
            color: var(--muted) !important;
            font-weight: 600 !important;
        }
        div[data-testid="stSegmentedControl"] div[role="radiogroup"] {
            background: transparent !important;
            border-color: var(--border) !important;
        }
        div[data-testid="stSegmentedControl"] [aria-checked="true"] {
            color: var(--red) !important;
            border-color: var(--red) !important;
            background: rgba(239, 68, 68, 0.12) !important;
            border-radius: 0 !important;
        }
        div[data-testid="stSegmentedControl"] [aria-checked="true"] * {
            color: var(--red) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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


def _is_valid_number(value) -> bool:
    try:
        return value is not None and not math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def _format_number(value, decimals: int = 2) -> str:
    if not _is_valid_number(value):
        return t("common.unavailable")
    return f"{float(value):,.{decimals}f}"


def _format_compact_number(value) -> str:
    if not _is_valid_number(value):
        return t("common.unavailable")

    value = float(value)
    abs_value = abs(value)
    for suffix, divisor in (("T", 1_000_000_000_000), ("B", 1_000_000_000), ("M", 1_000_000)):
        if abs_value >= divisor:
            return f"{value / divisor:,.2f}{suffix}"
    return f"{value:,.0f}"


def _format_pct(value) -> str:
    if not _is_valid_number(value):
        return t("common.unavailable")

    pct = float(value)
    if abs(pct) <= 1:
        pct *= 100
    return f"{pct:.2f}%"


def _daily_stat(df_plot: pd.DataFrame, column: str):
    if column not in df_plot.columns:
        return None
    values = df_plot[column].dropna()
    return None if values.empty else values.iloc[-1]


def _info_value(info: dict | None, *keys: str):
    if not info:
        return None
    for key in keys:
        value = info.get(key)
        if _is_valid_number(value):
            return value
    return None


def _render_google_stats(df_plot: pd.DataFrame, info: dict | None, previous_close: float | None) -> None:
    open_value = _daily_stat(df_plot, "Open") or _info_value(info, "regularMarketOpen", "open")
    high_value = _daily_stat(df_plot, "High") or _info_value(info, "dayHigh", "regularMarketDayHigh")
    low_value = _daily_stat(df_plot, "Low") or _info_value(info, "dayLow", "regularMarketDayLow")
    dividend_yield = _info_value(info, "dividendYield", "trailingAnnualDividendYield")

    stats = [
        ("Open", _format_number(open_value)),
        ("High", _format_number(high_value)),
        ("Low", _format_number(low_value)),
        ("Mkt cap", _format_compact_number(_info_value(info, "marketCap"))),
        ("P/E ratio", _format_number(_info_value(info, "trailingPE", "forwardPE"))),
        ("Previous close", _format_number(previous_close)),
        ("Dividend", _format_pct(dividend_yield)),
        ("52-wk high", _format_number(_info_value(info, "fiftyTwoWeekHigh"))),
        ("52-wk low", _format_number(_info_value(info, "fiftyTwoWeekLow"))),
    ]

    cells = "".join(
        "<div class='google-stat'>"
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(value)}</strong>"
        "</div>"
        for label, value in stats
    )
    st.markdown(f"<div class='google-chart-stats'>{cells}</div>", unsafe_allow_html=True)


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
                 exchange_timezone: str | None = None,
                 stock_info: dict | None = None,
                 period_change: float | None = None) -> None:
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
    is_positive = period_change >= 0 if period_change is not None else last_close >= reference_close
    line_color = "#22c55e" if is_positive else "#ef4444"
    fill_color = "rgba(34, 197, 94, 0.12)" if is_positive else "rgba(234, 67, 53, 0.12)"
    hover_date = "%-I:%M %p" if intraday else "%b %d, %Y"
    colors = _chart_colors()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_values,
        y=df_plot["Close"],
        mode="lines",
        name=t("chart.price"),
        line=dict(width=3, color=line_color, shape="spline", smoothing=0.45),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate=f"<b>%{{y:,.2f}} {disp_curr}</b><br>%{{x|{hover_date}}}<extra></extra>",
    ))

    if previous_close:
        fig.add_hline(
            y=previous_close,
            line_dash="dot",
            line_width=1.6,
            line_color=colors["previous"],
            opacity=0.75,
            annotation_text=f"Previous close<br>{previous_close:,.2f}",
            annotation_position="right",
            annotation_font=dict(size=12, color=colors["tick"]),
        )

    fig.add_trace(go.Scatter(
        x=[x_clean.iloc[-1]],
        y=[last_close],
        mode="markers",
        name=t("chart.price"),
        marker=dict(size=9, color=line_color, line=dict(width=2, color=colors["marker_border"])),
        hoverinfo="skip",
    ))

    y_points = [df_plot["Close"].min(), df_plot["Close"].max()]
    if previous_close:
        y_points.append(previous_close)
    mn  = min(y_points)
    mx  = max(y_points)
    pad = max((mx - mn) * 0.12, 1)

    if intraday:
        tickformat = "%H:%M"
    elif period in {"3Y", "5Y", "All"}:
        tickformat = "%b %d<br>%Y"
    else:
        tickformat = "%b %d"

    fig.update_layout(
        height=390,
        hovermode="x",
        hoverdistance=80,
        spikedistance=80,
        dragmode=False,
        margin=dict(l=8, r=8, t=10, b=2),
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(
            range=[mn - pad, mx + pad],
            fixedrange=True,
            showgrid=True,
            gridcolor=colors["grid"],
            showticklabels=True,
            ticks="",
            showline=False,
            zeroline=False,
            showspikes=True,
            spikecolor="#9aa0a6",
            spikedash="dot",
            spikethickness=1,
            spikemode="across",
            tickfont=dict(color=colors["tick"], size=12),
            separatethousands=True,
        ),
        showlegend=False,
        paper_bgcolor=colors["paper"],
        plot_bgcolor=colors["plot"],
        font=dict(family="Google Sans, Arial, sans-serif", color=colors["muted"], size=12),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=colors["axis"],
            zeroline=False,
            fixedrange=True,
            range=x_range,
            showticklabels=True,
            ticks="outside",
            tickformat=tickformat,
            tickfont=dict(color=colors["tick"], size=12),
            showspikes=True,
            spikecolor="#9aa0a6",
            spikedash="dot",
            spikethickness=1,
            spikemode="across",
        ),
        hoverlabel=dict(
            bgcolor=colors["hover_bg"],
            bordercolor=colors["hover_border"],
            font=dict(family="Google Sans, Arial, sans-serif", size=13, color=colors["tick"]),
        ),
    )

    st.markdown(
        f"""
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.google-chart-title) {{
            background: var(--surface) !important;
            border-color: var(--border) !important;
            box-shadow: 0 1px 2px rgba(60, 64, 67, 0.12);
        }}
        .google-chart-header {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 180px;
        }}
        .google-chart-title {{
            color: var(--text) !important;
            font: 700 1.12rem Google Sans, Arial, sans-serif;
            letter-spacing: -0.01em;
            margin: 0;
        }}
        .google-chart-subtitle {{
            color: var(--muted) !important;
            font: 600 0.86rem Google Sans, Arial, sans-serif;
            margin: 0;
        }}
        .google-chart-stats {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px 34px;
            padding: 16px 6px 18px;
            margin-bottom: 6px;
            background: var(--surface);
        }}
        .google-stat {{
            display: flex;
            justify-content: space-between;
            gap: 14px;
            color: var(--muted) !important;
            font: 600 0.95rem Google Sans, Arial, sans-serif;
            line-height: 1.35;
            min-width: 0;
        }}
        .google-stat span {{
            color: var(--muted) !important;
        }}
        .google-stat strong {{
            color: var(--text) !important;
            font-weight: 700;
            text-align: right;
            white-space: nowrap;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.google-chart-title)
        div[data-testid="stSegmentedControl"] {{
            margin-top: 4px;
        }}
        @media (max-width: 760px) {{
            .google-chart-stats {{ grid-template-columns: 1fr; gap: 9px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        title_col, selector_col = st.columns([0.9, 2.2], vertical_alignment="center")
        with title_col:
            st.markdown(
                f"""
                <div class="google-chart-header">
                    <div class="google-chart-title">{escape(t('chart.price_history'))}</div>
                    <div class="google-chart-subtitle">{escape(t('chart.price_axis', currency=disp_curr))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with selector_col:
            render_period_selector()
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
        _render_google_stats(df_plot, stock_info, previous_close)
