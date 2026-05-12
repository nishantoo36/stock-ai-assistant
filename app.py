import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
import plotly.graph_objects as go

from yahooquery import search
from forex_python.converter import CurrencyRates

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(
    page_title="AI Investment Assistant",
    layout="wide"
)

# ------------------------------------------------
# SESSION STATE
# ------------------------------------------------

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None

if "company_name" not in st.session_state:
    st.session_state.company_name = None

# ------------------------------------------------
# FOREX
# ------------------------------------------------

c = CurrencyRates()

# ------------------------------------------------
# CURRENCY SYMBOLS
# ------------------------------------------------

def get_currency_symbol(currency):

    symbols = {
        "USD": "$",
        "EUR": "€",
        "INR": "₹",
        "GBP": "£",
        "JPY": "¥",
        "CNY": "¥",
        "AED": "د.إ",
        "AUD": "A$",
        "CAD": "C$",
        "CHF": "CHF ",
        "SGD": "S$"
    }

    return symbols.get(currency, currency + " ")

# ------------------------------------------------
# CACHE STOCK SEARCH
# ------------------------------------------------

@st.cache_data(ttl=1800)
def search_stocks(query):

    return search(query)

# ------------------------------------------------
# CACHE STOCK DATA
# ------------------------------------------------

@st.cache_data(ttl=3600)
def load_stock_data(ticker, period):

    stock = yf.Ticker(ticker)

    period_mapping = {
        "3D": "5d",
        "5D": "5d",
        "1M": "1mo",
        "3M": "3mo",
        "6M": "6mo",
        "1Y": "1y",
        "5Y": "5y",
        "MAX": "max"
    }

    yf_period = period_mapping.get(period, "5d")

    return stock.history(period=yf_period)

# ------------------------------------------------
# GOOGLE NEWS RSS
# ------------------------------------------------

@st.cache_data(ttl=1800)
def load_stock_news(company_name):

    query = company_name.replace(" ", "+")

    url = (
        f"https://news.google.com/rss/search?q={query}+stock"
    )

    feed = feedparser.parse(url)

    news_list = []

    for entry in feed.entries[:10]:

        news_list.append({

            "title": entry.title,

            "link": entry.link,

            "publisher": (
                entry.source.title
                if hasattr(entry, "source")
                else "Google News"
            )
        })

    return news_list

# ------------------------------------------------
# RSI CALCULATION
# ------------------------------------------------

def calculate_rsi(data, window=14):

    delta = data.diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window).mean()

    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# ------------------------------------------------
# HEADER
# ------------------------------------------------

st.title("📈 AI Investment Assistant")

st.markdown("""
Simple AI-powered stock guidance.

Search stocks, ETFs, or companies
to receive beginner-friendly investment insights.
""")

# ------------------------------------------------
# CURRENCY SELECTOR
# ------------------------------------------------

currency_options = [
    "Original",
    "USD",
    "EUR",
    "INR",
    "GBP",
    "JPY",
    "AUD",
    "CAD",
    "CHF",
    "CNY",
    "SGD",
    "AED"
]

currency_option = st.selectbox(
    "💱 Display Currency",
    currency_options
)

# ------------------------------------------------
# SEARCH FORM
# ------------------------------------------------

with st.form("stock_search_form"):

    search_text = st.text_input(
        "🔍 Search stock or ETF",
        "Nvidia"
    )

    search_clicked = st.form_submit_button(
        "Search"
    )

# ------------------------------------------------
# SEARCH EXECUTION
# ------------------------------------------------

if search_clicked and search_text:

    try:

        with st.spinner("Searching investments..."):

            results = search_stocks(search_text)

        quotes = results.get("quotes", [])

        stock_options = {}

        for q in quotes[:10]:

            symbol = q.get("symbol", "")

            name = q.get("shortname", symbol)

            exchange = q.get("exchange", "")

            if symbol and name:

                display_name = (
                    f"{name} ({symbol}) - {exchange}"
                )

                stock_options[display_name] = {
                    "ticker": symbol,
                    "name": name
                }

        if stock_options:

            selected_stock = st.selectbox(
                "Select investment",
                list(stock_options.keys())
            )

            st.session_state.selected_ticker = (
                stock_options[selected_stock]["ticker"]
            )

            st.session_state.company_name = (
                stock_options[selected_stock]["name"]
            )

        else:

            st.error("No matching investments found")

            st.stop()

    except Exception as e:

        st.error(f"Search error: {e}")

        st.stop()

# ------------------------------------------------
# STOCK ANALYSIS
# ------------------------------------------------

if st.session_state.selected_ticker:

    try:

        # ------------------------------------------------
        # CHART PERIOD
        # ------------------------------------------------

        chart_period = st.selectbox(
            "📅 Chart Time Range",
            [
                "3D",
                "5D",
                "1M",
                "3M",
                "6M",
                "1Y",
                "5Y",
                "MAX"
            ],
            index=0
        )

        # ------------------------------------------------
        # LOAD DATA
        # ------------------------------------------------

        with st.spinner("Loading market data..."):

            stock = yf.Ticker(
                st.session_state.selected_ticker
            )

            stock_info = stock.info

            original_currency = stock_info.get(
                "currency",
                "USD"
            )

            df = load_stock_data(
                st.session_state.selected_ticker,
                chart_period
            )

            news = load_stock_news(
                st.session_state.company_name
            )

        if df.empty:

            st.error("No market data available")

            st.stop()

        # ------------------------------------------------
        # INDICATORS
        # ------------------------------------------------

        df["RSI"] = calculate_rsi(df["Close"])

        df["SMA20"] = (
            df["Close"]
            .rolling(window=20)
            .mean()
        )

        df["SMA50"] = (
            df["Close"]
            .rolling(window=50)
            .mean()
        )

        latest = df.iloc[-1]

        original_price = latest["Close"]

        current_price = original_price

        display_currency = original_currency

        # ------------------------------------------------
        # CURRENCY CONVERSION
        # ------------------------------------------------

        try:

            if (
                currency_option != "Original"
                and original_currency != currency_option
            ):

                conversion_rate = c.get_rate(
                    original_currency,
                    currency_option
                )

                current_price = (
                    original_price
                    * conversion_rate
                )

                display_currency = currency_option

        except:

            current_price = original_price

            display_currency = original_currency

        rsi = latest["RSI"]

        sma20 = latest["SMA20"]

        sma50 = latest["SMA50"]

        # ------------------------------------------------
        # PRICE CHANGE
        # ------------------------------------------------

        if len(df) > 2:

            recent_change = (
                (
                    df["Close"].iloc[-1]
                    - df["Close"].iloc[0]
                )
                / df["Close"].iloc[0]
            ) * 100

        else:

            recent_change = 0

        # ------------------------------------------------
        # AI RECOMMENDATION LOGIC
        # ------------------------------------------------

        recommendation = "HOLD"

        confidence = 65

        risk = "Medium"

        summary = ""

        detailed_reason = ""

        beginner_tip = ""

        if rsi < 35 and sma20 > sma50:

            recommendation = "BUY"

            confidence = 84

            risk = "Medium"

            summary = (
                "The stock looks potentially undervalued "
                "and may be recovering."
            )

            detailed_reason = f"""
Why BUY?

• RSI is low ({rsi:.1f})

• Short-term trend is improving

• Investors may have overreacted recently

• This sometimes creates buying opportunities
"""

            beginner_tip = (
                "Consider investing gradually instead "
                "of investing everything at once."
            )

        elif rsi > 70 and recent_change > 15:

            recommendation = "SELL"

            confidence = 83

            risk = "High"

            summary = (
                "The stock increased very quickly recently "
                "which may increase short-term risk."
            )

            detailed_reason = f"""
Why SELL?

• RSI is high ({rsi:.1f})

• Stock rose {recent_change:.1f}% recently

• Stocks that rise too quickly can fall later

• Risk currently appears elevated
"""

            beginner_tip = (
                "Avoid emotional buying after large price increases."
            )

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

• RSI is currently {rsi:.1f}

• No strong buy or sell signal detected

• Market behaviour appears stable

• Waiting may reduce unnecessary risk
"""

            beginner_tip = (
                "This may be a good time to monitor the stock "
                "before making a decision."
            )

        # ------------------------------------------------
        # HEADER
        # ------------------------------------------------

        st.header(
            f"📊 {st.session_state.company_name}"
        )

        # ------------------------------------------------
        # METRICS
        # ------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Current Price",
            f"{get_currency_symbol(display_currency)}"
            f"{current_price:.2f}"
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

        st.subheader(
            f"📈 Price Trend ({chart_period})"
        )

        chart_df = df[[
            "Close",
            "SMA20",
            "SMA50"
        ]].copy()

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df["Close"],
                mode="lines",
                name="Price"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df["SMA20"],
                mode="lines",
                name="SMA20"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df["SMA50"],
                mode="lines",
                name="SMA50"
            )
        )

        min_price = chart_df["Close"].min()
        max_price = chart_df["Close"].max()

        padding = (
            (max_price - min_price) * 0.15
        )

        if padding < 1:
            padding = 1

        fig.update_layout(

            height=500,

            hovermode="x unified",

            xaxis_title="Date",

            yaxis_title=(
                f"Price ({display_currency})"
            ),

            yaxis=dict(
                range=[
                    min_price - padding,
                    max_price + padding
                ]
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ------------------------------------------------
        # EDUCATION SECTION
        # ------------------------------------------------

        with st.expander("📚 What do RSI, SMA20 and SMA50 mean?"):

            st.write("""
### RSI (Relative Strength Index)

RSI helps understand whether a stock may have risen or fallen too quickly.

• Low RSI → stock may be undervalued

• High RSI → stock may be overbought

---

### SMA20 (Simple Moving Average 20)

Average stock price over the last 20 days.

This helps identify short-term trend direction.

---

### SMA50 (Simple Moving Average 50)

Average stock price over the last 50 days.

This helps identify longer-term market direction.

---

Investors use these indicators to better understand stock momentum and trend behaviour.
""")

        # ------------------------------------------------
        # TRADE REPUBLIC CTA
        # ------------------------------------------------

        st.subheader("💼 Start Investing")

        st.write("""
The smartest way to invest, spend and bank.

Create an account via the link below
to secure a welcome bonus.
""")

        st.link_button(
            "Join Trade Republic",
            "https://refnocode.trade.re/wnk12lwn"
        )

        # ------------------------------------------------
        # AI SUMMARY
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

            st.subheader("📋 Market Snapshot")

            st.write(f"""
• Current RSI: {rsi:.1f}

• Price Change: {recent_change:.1f}%

• Original Currency: {original_currency}

• Display Currency: {display_currency}

• Analysis Timeframe: {chart_period}

• Short-Term Trend:
{'Positive' if sma20 > sma50 else 'Weak'}
""")

            st.subheader("⚠️ Important Reminder")

            st.write("""
No AI can predict stock markets perfectly.

This tool should support your decisions,
not replace your own research.
""")

            # ------------------------------------------------
            # RECENT NEWS
            # ------------------------------------------------

            st.subheader("📰 Recent Market News")

            if news:

                for article in news:

                    title = article.get("title", "")

                    link = article.get("link", "")

                    publisher = article.get(
                        "publisher",
                        "Google News"
                    )

                    st.markdown(
                        f"• [{title}]({link})"
                    )

                    st.caption(publisher)

            else:

                st.write(
                    "No recent market news available."
                )

    except Exception as e:

        st.error(f"Error loading stock data: {e}")