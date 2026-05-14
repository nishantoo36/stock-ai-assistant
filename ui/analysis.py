"""
Analysis panel — everything rendered after price/chart:
metric cards, signal score bar, signal breakdown expander,
news sentiment expander, education expander, CTA, disclaimer.
"""

import numpy as np
import streamlit as st
from utils.i18n import t

SIGNAL_NAME_KEYS = {
    "RSI": "signals.names.rsi",
    "SMA Cross": "signals.names.sma_cross",
    "Price vs SMA20": "signals.names.price_vs_sma20",
    "Price vs SMA50": "signals.names.price_vs_sma50",
    "5D Momentum": "signals.names.momentum_5d",
    "20D Momentum": "signals.names.momentum_20d",
    "MACD": "signals.names.macd",
    "Bollinger": "signals.names.bollinger",
    "Volume": "signals.names.volume",
    "52W Range": "signals.names.range_52w",
    "News": "signals.names.news",
}

RISK_TRANSLATION_KEYS = {
    "High": "risk.high",
    "Low-Medium": "risk.low_medium",
    "Low–Medium": "risk.low_medium",
    "Medium": "risk.medium",
}


def _translated_signal_name(name: str) -> str:
    key = SIGNAL_NAME_KEYS.get(name)
    return t(key) if key else name


def _translated_signal_desc(desc) -> str:
    if isinstance(desc, tuple) and len(desc) == 2:
        key, params = desc
        return t(key, **params) if params else t(key)
    return str(desc)


def _translated_risk(risk: str) -> str:
    key = RISK_TRANSLATION_KEYS.get(risk)
    return t(key) if key else risk


# ── Rate-limit error ──────────────────────────────────────────────────────────

def render_rate_limit_error() -> None:
    st.markdown(
        "<div style='padding:20px 22px;background:rgba(239,68,68,0.08);"
        "border:1px solid rgba(239,68,68,0.3);border-left:3px solid #ef4444;"
        "border-radius:12px;margin-top:12px'>"
        "<div style='font-size:1rem;font-weight:600;margin-bottom:6px'>"
        f"{t('stock_view.rate_limit_title')}</div>"
        "<div style='font-size:0.875rem;color:#94a3b8;line-height:1.6'>"
        f"{t('stock_view.rate_limit_message')}<br><br>"
        f"<strong>{t('stock_view.rate_limit_action')}</strong><br>"
        f"{t('stock_view.rate_limit_help')}"
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

def render_price(curr_price: float, day_chg, day_chg_pct, sym: str, period: str = "1D") -> None:
    price_str = f"{sym}{curr_price:,.2f}" if not np.isnan(curr_price) else t("stock_view.price_unavailable")

    if day_chg is not None:
        clr   = "#22c55e" if day_chg >= 0 else "#ef4444"
        arrow = "▲" if day_chg >= 0 else "▼"
        st.markdown(
            f"<div style='display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:20px'>"
            f"<span style='font-size:clamp(1.6rem,5vw,2.4rem);font-weight:700;"
            f"font-variant-numeric:tabular-nums;letter-spacing:-0.02em'>{price_str}</span>"
            f"<span style='color:{clr};font-size:clamp(0.85rem,2vw,1.05rem);font-weight:500'>"
            f"{arrow} {sym}{abs(day_chg):,.2f} ({day_chg_pct:+.2f}%)</span>"
            f"<span style='color:#475569;font-size:0.78rem;font-weight:500'>{period}</span>"
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

    rec_label = t(f"recommendations.{rec.lower()}")
    m1, m2, m3 = st.columns(3)
    for col, label, val, color, bg in [
        (m1, t("analysis.metric_recommendation"), rec_label, rec_clr, rec_bg),
        (m2, t("analysis.metric_confidence"), f"{conf}%", "#38bdf8", "rgba(56,189,248,0.08)"),
        (m3, t("analysis.metric_risk"), _translated_risk(risk), "#a78bfa", "rgba(167,139,250,0.08)"),
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
        f"letter-spacing:.06em;text-transform:uppercase'>{t('analysis.signal_score')}</span>"
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
        f"<span>{t('analysis.signal_buy')}</span><span>{t('analysis.signal_hold')}</span><span>{t('analysis.signal_sell')}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── AI summary ───────────────────────────────────────────────────────────────

def render_ai_summary(rec: str, summary: str) -> None:
    st.markdown(
        f"<p style='color:#94a3b8;font-size:0.78rem;font-weight:600;"
        f"letter-spacing:.06em;text-transform:uppercase;margin:8px 0 8px 0'>"
        f"{t('analysis.ai_summary')}</p>",
        unsafe_allow_html=True,
    )
    if rec == "BUY":    st.success(summary)
    elif rec == "SELL": st.error(summary)
    else:               st.warning(summary)


# ── Signal breakdown expander ────────────────────────────────────────────────

def render_signal_breakdown(signals: list, rsi: float, mom5: float,
                             sym: str, info: dict) -> None:
    with st.expander(t("analysis.signal_breakdown")):
        b_sigs = [(n, d) for n, v, w, d in signals if v ==  1]
        s_sigs = [(n, d) for n, v, w, d in signals if v == -1]
        n_sigs = [(n, d) for n, v, w, d in signals if v ==  0]

        for sigs, color, label in [
            (b_sigs, "#22c55e", t("analysis.bullish_signals", count=len(b_sigs))),
            (s_sigs, "#ef4444", t("analysis.bearish_signals", count=len(s_sigs))),
            (n_sigs, "#94a3b8", f"⚪ {t('analysis.neutral_signals')}"),
        ]:
            if sigs:
                st.markdown(
                    f"<p style='color:{color};font-size:0.8rem;font-weight:600;"
                    f"letter-spacing:.05em;text-transform:uppercase;margin-top:12px'>{label}</p>",
                    unsafe_allow_html=True,
                )
                for nm, ds in sigs:
                    st.markdown(f"- **{_translated_signal_name(nm)}**: {_translated_signal_desc(ds)}")

        st.markdown("<hr>", unsafe_allow_html=True)
        ca, cb, cc, cd = st.columns(4)
        ca.metric("RSI (14)", f"{rsi:.1f}")
        cb.metric(t("analysis.return_5d"), f"{mom5:.1f}%")
        if w52h := info.get("fiftyTwoWeekHigh"):
            cc.metric(t("analysis.high_52w"), f"{sym}{w52h:,.2f}")
        if w52l := info.get("fiftyTwoWeekLow"):
            cd.metric(t("analysis.low_52w"),  f"{sym}{w52l:,.2f}")
        st.caption(t("analysis.disclaimer_note"))


# ── News sentiment expander ──────────────────────────────────────────────────

def render_news(news_label: str, news_detail: list) -> None:
    # Translate basic sentiment labels when possible
    translated_label = news_label
    if news_label.lower().startswith("positive"):
        translated_label = t("analysis.sentiment_positive")
    elif news_label.lower().startswith("negative"):
        translated_label = t("analysis.sentiment_negative")
    elif news_label.lower().startswith("neutral"):
        translated_label = t("analysis.sentiment_neutral")

    with st.expander(f"{t('analysis.news_sentiment')} — {translated_label}"):
        sentiment_text = t("analysis.sentiment_status", sentiment=translated_label)
        if news_label.lower().startswith("positive"):   st.success(f"**{sentiment_text}**")
        elif news_label.lower().startswith("negative"): st.error(f"**{sentiment_text}**")
        else:                                            st.info(f"**{sentiment_text}**")

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
    with st.expander(t("analysis.education")):
        st.markdown(t("analysis.education_content"))


# ── CTA + disclaimer ─────────────────────────────────────────────────────────

def render_cta() -> None:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:1rem;font-weight:600;margin-bottom:8px'>{t('analysis.cta_title')}</p>"
        f"<p style='color:#94a3b8;font-size:0.85rem;margin-bottom:14px'>"
        f"{t('analysis.cta_description')}</p>",
        unsafe_allow_html=True,
    )
    st.link_button(t("analysis.cta_button"), "https://refnocode.trade.re/wnk12lwn")
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(t("analysis.cta_disclaimer"))
