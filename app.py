import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
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
def load_stock_data(ticker):

    stock = yf.Ticker(ticker)

    return stock.history(period="1y")

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

selected_ticker = None

company_name = None

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

            selected_ticker = (
                stock_options[selected_stock]["ticker"]
            )

            company_name = (
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

if selected_ticker:

    try:

        # ------------------------------------------------
        # LOAD DATA
        # ------------------------------------------------

        with st.spinner("Loading market data..."):

            stock = yf.Ticker(selected_ticker)

            stock_info = stock.info

            original_currency = stock_info.get(
                "currency",
                "USD"
            )

            df = load_stock_data(selected_ticker)

            news = load_stock_news(company_name)

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

        if len(df) > 30:

            recent_change = (
                (
                    df["Close"].iloc[-1]
                    - df["Close"].iloc[-30]
                )
                / df["Close"].iloc[-30]
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

        # BUY SIGNAL

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

• RSI is low ({rsi:.1f}), meaning the stock recently dropped heavily.

• Short-term trend is improving.

• Investors may have overreacted recently.

• This sometimes creates attractive buying opportunities.
"""

            beginner_tip = (
                "Consider investing gradually instead "
                "of investing everything at once."
            )

        # SELL SIGNAL

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

• RSI is high ({rsi:.1f}), meaning investors may be overly excited.

• The stock rose {recent_change:.1f}% recently.

• Stocks that rise too quickly sometimes fall later.

• Risk currently appears elevated.
"""

            beginner_tip = (
                "Avoid emotional buying after large price increases."
            )

        # HOLD SIGNAL

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

• No strong buy or sell signal detected.

• Market behaviour currently appears relatively stable.

• Waiting may reduce unnecessary risk.
"""

            beginner_tip = (
                "This may be a good time to monitor the stock "
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

        st.subheader("📈 Price Trend")

        chart_df = df[[
            "Close",
            "SMA20",
            "SMA50"
        ]]

        st.line_chart(chart_df)

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

• 30-Day Price Change: {recent_change:.1f}%

• Original Currency: {original_currency}

• Display Currency: {display_currency}

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