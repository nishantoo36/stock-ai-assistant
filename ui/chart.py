"""
Price chart with SMA20/SMA50 overlay and custom HTML legend.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.i18n import t

CHART_PERIODS = ["1D", "3D", "5D", "1M", "3M", "6M", "1Y", "MAX"]
INTRADAY      = {"1D", "3D", "5D"}


def render_period_selector() -> str:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:#94a3b8;font-size:0.78rem;font-weight:500;"
        f"letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px'>"
        f"{t('analysis.time_range')}</p>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(CHART_PERIODS))
    for i, p in enumerate(CHART_PERIODS):
        with cols[i]:
            is_active = st.session_state.chart_period == p
            if st.button(
                p, key=f"p_{p}", width="stretch",
                type="primary" if is_active else "secondary",
            ):
                st.session_state.chart_period = p
                st.rerun()
    return st.session_state.chart_period


def render_chart(df_chart: pd.DataFrame, df_analysis: pd.DataFrame,
                 period: str, disp_curr: str) -> None:
    intraday = period in INTRADAY
    df_plot  = (
        df_chart.dropna(subset=["Close"]) if not df_chart.empty
        else df_analysis.dropna(subset=["Close"])
    )
    if df_plot.empty:
        st.warning(t("chart.data_unavailable"))
        return

    fig = go.Figure()

    if intraday:
        fig.add_trace(go.Scatter(
            x=df_plot.index, y=df_plot["Close"],
            mode="lines", name=t("chart.price"),
            line=dict(width=2, color="#38bdf8"),
            fill="tozeroy", fillcolor="rgba(56,189,248,0.06)",
        ))
    else:
        s20 = df_plot["Close"].rolling(20).mean()
        s50 = df_plot["Close"].rolling(50).mean()
        fig.add_trace(go.Scatter(
            x=df_plot.index, y=df_plot["Close"],
            mode="lines", name=t("chart.price"),
            line=dict(width=2, color="#38bdf8"),
        ))
        fig.add_trace(go.Scatter(
            x=df_plot.index, y=s20,
            mode="lines", name="SMA20",
            line=dict(dash="dash", width=1.2, color="#f59e0b"),
        ))
        fig.add_trace(go.Scatter(
            x=df_plot.index, y=s50,
            mode="lines", name="SMA50",
            line=dict(dash="dot", width=1.2, color="#a78bfa"),
        ))

    mn  = df_plot["Close"].min()
    mx  = df_plot["Close"].max()
    pad = max((mx - mn) * 0.12, 1)

    fig.update_layout(
        height=380,
        hovermode="x unified",
        margin=dict(l=0, r=0, t=8, b=0),
        xaxis_title=None,
        yaxis_title=t("chart.price_axis", currency=disp_curr),
        yaxis=dict(range=[mn - pad, mx + pad]),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.6)",
        font=dict(family="DM Sans, sans-serif", color="#94a3b8", size=11),
        xaxis=dict(gridcolor="#1f2d45", gridwidth=1, showline=False, zeroline=False),
        yaxis_gridcolor="#1f2d45",
        hoverlabel=dict(
            bgcolor="#1a2235", bordercolor="#1f2d45",
            font=dict(family="DM Mono, monospace", size=12),
        ),
    )

    # Custom HTML legend above chart — no overlap with Plotly zoom controls
    if intraday:
        legend_html = f"""
        <div style="display:flex;align-items:center;gap:20px;padding:6px 4px 10px 4px;flex-wrap:wrap;">
            <span style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#94a3b8;font-weight:500">
                <span style="display:inline-block;width:24px;height:2px;background:#38bdf8;border-radius:2px"></span>
                {t('chart.price_history')}
            </span>
        </div>"""
    else:
        legend_html = f"""
        <div style="display:flex;align-items:center;gap:20px;padding:6px 4px 10px 4px;flex-wrap:wrap;">
            <span style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#94a3b8;font-weight:500">
                <span style="display:inline-block;width:24px;height:2px;background:#38bdf8;border-radius:2px"></span>
                {t('chart.price_history')}
            </span>
            <span style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#94a3b8;font-weight:500">
                <span style="display:inline-block;width:24px;height:0;border-top:2px dashed #f59e0b"></span>
                {t('chart.sma_20')}
            </span>
            <span style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#94a3b8;font-weight:500">
                <span style="display:inline-block;width:24px;height:0;border-top:2px dotted #a78bfa"></span>
                {t('chart.sma_50')}
            </span>
        </div>"""

    st.markdown(legend_html, unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch")
