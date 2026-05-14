"""
Analysis panel — everything rendered after price/chart:
metric cards, signal score bar, signal breakdown expander,
news sentiment expander, education expander, CTA, disclaimer.
"""

import numpy as np
import streamlit as st


# ── Rate-limit error ──────────────────────────────────────────────────────────

def render_rate_limit_error() -> None:
    st.markdown(
        "<div style='padding:20px 22px;background:rgba(239,68,68,0.08);"
        "border:1px solid rgba(239,68,68,0.3);border-left:3px solid #ef4444;"
        "border-radius:12px;margin-top:12px'>"
        "<div style='font-size:1rem;font-weight:600;margin-bottom:6px'>"
        "🚦 Market Data Temporarily Unavailable</div>"
        "<div style='font-size:0.875rem;color:#94a3b8;line-height:1.6'>"
        "Yahoo Finance is rate-limiting requests from this server — this happens when many "
        "users are active at the same time on shared cloud deployments.<br><br>"
        "✅ <strong>Please wait 2 minutes and try again.</strong><br>"
        "If the issue persists, try searching a different stock first, then come back."
        "</div></div>",
        unsafe_allow_html=True,
    )


# ── Stock header ─────────────────────────────────────────────────────────────

def render_stock_header(company_name: str, ticker: str) -> None:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:4px'>"
        f"<span style='font-size:clamp(1.3rem,3vw,1.6rem);font-weight:700;"
        f"letter-spacing:-0.02em'>{company_name}</span>"
        f"<span style='font-family:var(--mono,monospace);font-size:0.85rem;"
        f"background:#1a2235;border:1px solid #1f2d45;border-radius:6px;"
        f"padding:2px 10px;color:#94a3b8'>{ticker}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── Price row ────────────────────────────────────────────────────────────────

def render_price(curr_price: float, day_chg, day_chg_pct, sym: str) -> None:
    price_str = f"{sym}{curr_price:,.2f}" if not np.isnan(curr_price) else "Price unavailable"

    if day_chg is not None:
        clr   = "#22c55e" if day_chg >= 0 else "#ef4444"
        arrow = "▲" if day_chg >= 0 else "▼"
        st.markdown(
            f"<div style='display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:20px'>"
            f"<span style='font-size:clamp(1.6rem,5vw,2.4rem);font-weight:700;"
            f"font-variant-numeric:tabular-nums;letter-spacing:-0.02em'>{price_str}</span>"
            f"<span style='color:{clr};font-size:clamp(0.85rem,2vw,1.05rem);font-weight:500'>"
            f"{arrow} {sym}{abs(day_chg):,.2f} ({day_chg_pct:+.2f}%)</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='font-size:clamp(1.6rem,5vw,2.4rem);font-weight:700;"
            f"margin-bottom:20px'>{price_str}</div>",
            unsafe_allow_html=True,
        )


# ── Metric cards ─────────────────────────────────────────────────────────────

def render_metric_cards(rec: str, conf: int, risk: str) -> None:
    rec_clr = {"BUY": "#22c55e", "SELL": "#ef4444", "HOLD": "#f59e0b"}[rec]
    rec_bg  = {
        "BUY":  "rgba(34,197,94,0.08)",
        "SELL": "rgba(239,68,68,0.08)",
        "HOLD": "rgba(245,158,11,0.08)",
    }[rec]

    m1, m2, m3 = st.columns(3)
    for col, label, val, color, bg in [
        (m1, "RECOMMENDATION", rec,        rec_clr,   rec_bg),
        (m2, "CONFIDENCE",     f"{conf}%", "#38bdf8", "rgba(56,189,248,0.08)"),
        (m3, "RISK",           risk,       "#a78bfa", "rgba(167,139,250,0.08)"),
    ]:
        col.markdown(
            f"<div style='background:{bg};border:1px solid {color}33;"
            f"border-left:3px solid {color};padding:18px 16px;border-radius:12px'>"
            f"<div style='color:#64748b;font-size:0.7rem;font-weight:600;"
            f"letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px'>{label}</div>"
            f"<div style='color:{color};font-size:clamp(1.4rem,3vw,1.9rem);"
            f"font-weight:700;letter-spacing:-0.02em'>{val}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ── Signal score bar ─────────────────────────────────────────────────────────

def render_score_bar(score_pct: float) -> None:
    norm  = max(-100, min(100, score_pct))
    bclr  = "#22c55e" if norm > 0 else "#ef4444"
    bw    = abs(norm) / 2
    bside = "left:50%" if norm > 0 else "right:50%"

    st.markdown(
        f"<div style='margin-bottom:4px'>"
        f"<span style='font-size:0.78rem;font-weight:600;color:#94a3b8;"
        f"letter-spacing:.06em;text-transform:uppercase'>Signal Score</span>"
        f"<span style='font-size:1rem;font-weight:700;color:{bclr};"
        f"margin-left:10px'>{score_pct:.0f} / 100</span>"
        f"</div>"
        f"<div style='background:#111827;border:1px solid #1f2d45;border-radius:8px;"
        f"height:10px;width:100%;position:relative;overflow:hidden'>"
        f"<div style='position:absolute;left:50%;top:0;height:100%;width:1px;"
        f"background:#334155;z-index:2'></div>"
        f"<div style='position:absolute;{bside};top:0;height:100%;"
        f"width:{bw:.1f}%;background:{bclr};border-radius:4px;"
        f"transition:width 0.4s ease'></div>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;"
        f"font-size:0.68rem;color:#475569;margin-top:4px'>"
        f"<span>◀ SELL</span><span>HOLD</span><span>BUY ▶</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── AI summary ───────────────────────────────────────────────────────────────

def render_ai_summary(rec: str, summary: str) -> None:
    st.markdown(
        "<p style='color:#94a3b8;font-size:0.78rem;font-weight:600;"
        "letter-spacing:.06em;text-transform:uppercase;margin:8px 0 8px 0'>"
        "🤖 AI Summary</p>",
        unsafe_allow_html=True,
    )
    if rec == "BUY":    st.success(summary)
    elif rec == "SELL": st.error(summary)
    else:               st.warning(summary)


# ── Signal breakdown expander ────────────────────────────────────────────────

def render_signal_breakdown(signals: list, rsi: float, mom5: float,
                             sym: str, info: dict) -> None:
    with st.expander("🔍 Full Signal Breakdown"):
        b_sigs = [(n, d) for n, v, w, d in signals if v ==  1]
        s_sigs = [(n, d) for n, v, w, d in signals if v == -1]
        n_sigs = [(n, d) for n, v, w, d in signals if v ==  0]

        for sigs, color, label in [
            (b_sigs, "#22c55e", "🟢 Bullish Signals"),
            (s_sigs, "#ef4444", "🔴 Bearish Signals"),
            (n_sigs, "#94a3b8", "⚪ Neutral Signals"),
        ]:
            if sigs:
                st.markdown(
                    f"<p style='color:{color};font-size:0.8rem;font-weight:600;"
                    f"letter-spacing:.05em;text-transform:uppercase;margin-top:12px'>{label}</p>",
                    unsafe_allow_html=True,
                )
                for nm, ds in sigs:
                    st.markdown(f"- **{nm}**: {ds}")

        st.markdown("<hr>", unsafe_allow_html=True)
        ca, cb, cc, cd = st.columns(4)
        ca.metric("RSI (14)", f"{rsi:.1f}")
        cb.metric("5D Return", f"{mom5:.1f}%")
        if w52h := info.get("fiftyTwoWeekHigh"):
            cc.metric("52W High", f"{sym}{w52h:,.2f}")
        if w52l := info.get("fiftyTwoWeekLow"):
            cd.metric("52W Low",  f"{sym}{w52l:,.2f}")
        st.caption("⚠️ No algorithm predicts markets perfectly. Use this to support your own research.")


# ── News sentiment expander ──────────────────────────────────────────────────

def render_news(news_label: str, news_detail: list) -> None:
    with st.expander(f"📰 News Sentiment — {news_label}"):
        if "Positive" in news_label:   st.success(f"Sentiment: **{news_label}**")
        elif "Negative" in news_label: st.error(f"Sentiment: **{news_label}**")
        else:                          st.info(f"Sentiment: **{news_label}**")

        for item in news_detail:
            kw_html  = (f" <span style='font-size:0.72rem;color:#64748b'>— {item['keywords']}</span>"
                        if item["keywords"] else "")
            pub_html = (f" <span style='font-size:0.7rem;color:#475569'>· {item['publisher']}</span>"
                        if item["publisher"] else "")
            title_html = (
                f"<a href='{item['link']}' target='_blank' class='news-link'>{item['title']}</a>"
                if item["link"] else item["title"]
            )
            st.markdown(
                f"<div style='padding:8px 0;border-bottom:1px solid #1a2235;"
                f"font-size:0.85rem;line-height:1.5'>"
                f"{item['icon']} {title_html}{kw_html}{pub_html}"
                f"</div>",
                unsafe_allow_html=True,
            )


# ── Education expander ───────────────────────────────────────────────────────

def render_education() -> None:
    with st.expander("📚 What do these indicators mean?"):
        st.markdown("""
**RSI** — Below 30 = oversold (buy signal). Above 70 = overbought (sell risk).

**SMA20 / SMA50** — Moving averages. SMA20 crossing above SMA50 = bullish golden cross.

**MACD** — Momentum. Crossover above signal line = bullish shift.

**Bollinger Bands** — Price near lower band = oversold. Near upper = overbought.

**52-Week Range** — Near yearly low = potential value. Near yearly high = less upside buffer.

**News Sentiment** — Headlines scanned for positive/negative keywords to gauge market mood.
""")


# ── CTA + disclaimer ─────────────────────────────────────────────────────────

def render_cta() -> None:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:1rem;font-weight:600;margin-bottom:8px'>💼 Start Investing</p>"
        "<p style='color:#94a3b8;font-size:0.85rem;margin-bottom:14px'>"
        "Create an account via the link below to secure a welcome bonus.</p>",
        unsafe_allow_html=True,
    )
    st.link_button("Join Trade Republic →", "https://refnocode.trade.re/wnk12lwn")
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(
        "⚠️ This tool is for educational and personal research purposes only. "
        "No AI can predict markets perfectly. Always do your own due diligence before investing."
    )
