import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from yahooquery import search

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(
    page_title="AI Investment Assistant",
    layout="wide"
)

# ------------------------------------------------
# HEADER
# ------------------------------------------------

st.title("📈 AI Investment Assistant")

st.markdown(
    """
    Simple AI-powered investment guidance.

    Search any stock, ETF, or company name
    to get beginner-friendly BUY / HOLD / SELL suggestions.
    """
)

# ------------------------------------------------
# SEARCH
# ------------------------------------------------

search_text = st.text_input(
    "🔍 Search stock or ETF",
    "Nvidia"
)

selected_ticker = None

if search_text:

    try:

        results = search(search_text)

        quotes = results.get("quotes", [])

        stock_options = {}

        for q in quotes[:10]:

            symbol = q.get("symbol", "")
            name = q.get("shortname", symbol)
            exchange = q.get("exchange", "")

            display_name = f"{name} ({symbol}) - {exchange}"

            stock_options[display_name] = symbol

        if stock_options:

            selected_stock = st.selectbox(
                "Select investment",
                list(stock_options.keys())
            )

            selected_ticker = stock_options[selected_stock]

        else:
            st.error("No matching investments found")
            st.stop()

    except Exception as e:
        st.error(f"Search error: {e}")
        st.stop()

# ------------------------------------------------
# ANALYSIS
# ------------------------------------------------

if selected_ticker:

    try:

        stock = yf.Ticker(selected_ticker)

        df = stock.history(period="1y")

        if df.empty:
            st.error("No market data available")
            st.stop()

        # ------------------------------------------------
        # TECHNICAL INDICATORS
        # ------------------------------------------------

        df["RSI"] = ta.rsi(df["Close"], length=14)
        df["SMA20"] = ta.sma(df["Close"], length=20)
        df["SMA50"] = ta.sma(df["Close"], length=50)

        latest = df.iloc[-1]

        current_price = latest["Close"]
        rsi = latest["RSI"]
        sma20 = latest["SMA20"]
        sma50 = latest["SMA50"]

        info = stock.info

        company_name = info.get("longName", selected_ticker)

        # ------------------------------------------------
        # PRICE TREND
        # ------------------------------------------------

        recent_change = (
            (df["Close"].iloc[-1] - df["Close"].iloc[-30])
            / df["Close"].iloc[-30]
        ) * 100

        # ------------------------------------------------
        # AI RECOMMENDATION LOGIC
        # ------------------------------------------------

        recommendation = "HOLD"
        confidence = 65
        risk = "Medium"

        summary = ""
        detailed_reason = ""
        beginner_tip = ""

        # STRONG BUY
        if rsi < 35 and sma20 > sma50:

            recommendation = "BUY"
            confidence = 84
            risk = "Medium"

            summary = (
                "The stock looks potentially undervalued "
                "and may be starting to recover."
            )

            detailed_reason = f"""
            Why BUY?

            • RSI is low ({rsi:.1f}), meaning the stock recently dropped heavily.

            • Short-term trend is improving.

            • Investors may have overreacted recently.

            • This sometimes creates good long-term buying opportunities.
            """

            beginner_tip = (
                "Instead of investing all money at once, "
                "consider investing gradually over time."
            )

        # STRONG SELL
        elif rsi > 70 and recent_change > 15:

            recommendation = "SELL"
            confidence = 83
            risk = "High"

            summary = (
                "The stock price increased very quickly recently "
                "which may increase short-term risk."
            )

            detailed_reason = f"""
            Why SELL?

            • RSI is high ({rsi:.1f}), meaning investors may be too excited.

            • The stock rose {recent_change:.1f}% recently.

            • Stocks that rise too quickly sometimes fall back later.

            • Risk currently appears elevated.
            """

            beginner_tip = (
                "Avoid emotional buying after large price increases or hype."
            )

        # HOLD
        else:

            recommendation = "HOLD"
            confidence = 68
            risk = "Medium"

            summary = (
                "The stock currently looks relatively balanced "
                "without strong buy or sell signals."
            )

            detailed_reason = f"""
            Why HOLD?

            • RSI is currently {rsi:.1f}, which is within a more normal range.

            • No strong overbuying or overselling signals detected.

            • Market behaviour currently appears relatively stable.

            • Waiting may reduce unnecessary risk.
            """

            beginner_tip = (
                "This could be a good time to research the company further "
                "before making a decision."
            )

        # ------------------------------------------------
        # HEADER
        # ------------------------------------------------

        st.header(f"📊 {company_name}")

        # ------------------------------------------------
        # METRICS
        # ------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Current Price",
            f"${current_price:.2f}"
        )

        col2.metric(
            "Recommendation",
            recommendation
        )

        col3.metric(
            "Confidence",
            f"{confidence}%"
        )

        col4.metric(
            "Risk",
            risk
        )

        # ------------------------------------------------
        # CHART
        # ------------------------------------------------

        st.subheader("📈 Price Trend")

        chart_df = df[["Close", "SMA20", "SMA50"]]

        st.line_chart(chart_df)

        # ------------------------------------------------
        # MAIN SUMMARY
        # ------------------------------------------------

        st.subheader("🤖 AI Summary")

        if recommendation == "BUY":
            st.success(summary)

        elif recommendation == "SELL":
            st.error(summary)

        else:
            st.warning(summary)

        # ------------------------------------------------
        # MORE INSIGHTS
        # ------------------------------------------------

        with st.expander("🔍 More Insights"):

            st.subheader("🧠 Why This Recommendation?")

            st.write(detailed_reason)

            st.subheader("📚 Beginner Guidance")

            st.info(beginner_tip)

            st.subheader("⚠️ Important Reminder")

            st.write(
                """
                No AI can predict the market perfectly.

                This tool should support your decisions,
                not replace your own research.
                """
            )

            st.subheader("📋 Market Snapshot")

            st.write(f"""
            • Current RSI: {rsi:.1f}

            • 30-Day Price Change: {recent_change:.1f}%

            • Short-Term Trend: {'Positive' if sma20 > sma50 else 'Weak'}
            """)

    except Exception as e:
        st.error(f"Error loading stock data: {e}")