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
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------
# GLOBAL CSS — responsive, clean dark design
# ------------------------------------------------

st.markdown("""
<style>
/* ── Import font ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg:        #0a0e1a;
    --surface:   #111827;
    --surface2:  #1a2235;
    --border:    #1f2d45;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --accent:    #38bdf8;
    --green:     #22c55e;
    --red:       #ef4444;
    --yellow:    #f59e0b;
    --purple:    #a78bfa;
    --radius:    12px;
    --font:      'DM Sans', sans-serif;
    --mono:      'DM Mono', monospace;
}

/* ── Base resets ── */
html, body, [class*="css"] {
    font-family: var(--font) !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container {
    padding: clamp(1rem, 3vw, 2.5rem) clamp(0.75rem, 3vw, 2rem) !important;
    max-width: 1100px !important;
}

/* ── App header ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0 0 24px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}
.app-header-icon {
    font-size: 2rem;
    line-height: 1;
}
.app-header h1 {
    font-size: clamp(1.3rem, 3vw, 1.75rem) !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    margin: 0 !important;
    padding: 0 !important;
    letter-spacing: -0.02em;
}
.app-header p {
    font-size: 0.85rem;
    color: var(--muted);
    margin: 2px 0 0 0;
}

/* ── Streamlit element overrides ── */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.1) !important;
}
.stTextInput > label { display: none !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    transition: all 0.18s ease !important;
    cursor: pointer !important;
    white-space: nowrap;
}
.stButton > button:hover {
    background: var(--surface2) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #0a0e1a !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    background: #7dd3fc !important;
    border-color: #7dd3fc !important;
    color: #0a0e1a !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
}
.stSelectbox label { color: var(--muted) !important; font-size: 0.8rem !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 14px 18px !important;
}
.streamlit-expanderHeader:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
.streamlit-expanderContent {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius) var(--radius) !important;
    padding: 18px !important;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    color: var(--text) !important;
    font-size: 1.1rem !important;
}
[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: 0.78rem !important;
}

/* ── Alerts ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: var(--radius) !important;
    font-size: 0.9rem !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 24px 0 !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Subheaders / markdown ── */
h2, h3 { color: var(--text) !important; letter-spacing: -0.01em; }

/* ── Link button ── */
.stLinkButton > a {
    background: linear-gradient(135deg, var(--accent), #818cf8) !important;
    border: none !important;
    border-radius: var(--radius) !important;
    color: #0a0e1a !important;
    font-weight: 600 !important;
    font-family: var(--font) !important;
    padding: 10px 22px !important;
    text-decoration: none !important;
    transition: opacity 0.2s !important;
}
.stLinkButton > a:hover { opacity: 0.88 !important; }

/* ── News links ── */
.news-link {
    color: var(--text) !important;
    text-decoration: none !important;
    border-bottom: 1px solid var(--border) !important;
    transition: color 0.15s, border-color 0.15s !important;
}
.news-link:hover {
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ── Responsive columns ── */
@media (max-width: 640px) {
    .metric-row [data-testid="column"] { min-width: 100% !important; }
    .block-container { padding: 1rem 0.75rem !important; }
}

/* ── Caption ── */
.stCaption, caption { color: var(--muted) !important; font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# PERIOD MAP  (period, interval)
# ------------------------------------------------

PERIOD_MAP = {
    "1D":  ("1d",  "5m"),
    "3D":  ("5d",  "30m"),
    "5D":  ("5d",  "1h"),
    "1M":  ("1mo", "1d"),
    "3M":  ("3mo", "1d"),
    "6M":  ("6mo", "1d"),
    "1Y":  ("1y",  "1d"),
    "MAX": ("max", "1wk"),
}
CHART_PERIODS = ["1D", "3D", "5D", "1M", "3M", "6M", "1Y", "MAX"]

# ------------------------------------------------
# SESSION STATE
# ------------------------------------------------

for k, v in {
    "selected_ticker": None,
    "company_name": None,
    "search_results": [],
    "chart_period": "1D",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------------------------------------
# FOREX
# ------------------------------------------------

c = CurrencyRates()

def get_currency_symbol(currency):
    return {
        "USD": "$", "EUR": "€", "INR": "₹", "GBP": "£",
        "JPY": "¥", "CNY": "¥", "AED": "د.إ", "AUD": "A$",
        "CAD": "C$", "CHF": "CHF ", "SGD": "S$"
    }.get(currency, currency + " ")

# ------------------------------------------------
# SAFE LAST CLOSE — fixes ₹nan for Indian stocks
# ------------------------------------------------

def get_last_close(df, stock_info):
    clean = df.dropna(subset=["Close"])
    if not clean.empty:
        val = clean["Close"].iloc[-1]
        if not np.isnan(val):
            return val
    for key in ("regularMarketPrice", "currentPrice", "previousClose", "open"):
        val = stock_info.get(key)
        if val is not None:
            try:
                fval = float(val)
                if not np.isnan(fval):
                    return fval
            except:
                pass
    return float("nan")

# ------------------------------------------------
# NEWS SENTIMENT
# ------------------------------------------------

POSITIVE_WORDS = [
    "beat","beats","surge","surges","rally","gain","gains","growth","profit","profits",
    "record","strong","upgrade","upgraded","outperform","bullish","partnership",
    "expansion","breakthrough","revenue","rises","jumps","soars","climbs","boosts",
    "wins","positive","optimistic","upside","recovery","rebound","dividend",
    "exceeded","exceeds","higher","increase","milestone","opportunity","confident",
    "momentum","demand","innovative","leading","approval","approved","deal",
    "acquisition","buyback","surprise","above"
]
NEGATIVE_WORDS = [
    "loss","losses","crash","crashes","decline","falls","drops","downgrade",
    "downgraded","sell","bearish","fraud","lawsuit","scandal","misses","miss",
    "weak","cut","layoff","layoffs","investigation","recall","plunges","tumbles",
    "slumps","warning","risk","concern","debt","bankrupt","default","disappointing",
    "lower","below","penalty","fine","shortage","inflation","recession",
    "withdrawn","suspended","halt","probe","crisis","conflict","uncertainty",
    "hurt","pressure","fell","sank"
]

def analyze_news_sentiment(news_list):
    if not news_list:
        return 0, "Neutral", []
    total_pos = total_neg = 0
    detail = []
    for a in news_list:
        t = a.get("title","").lower()
        pos = [w for w in POSITIVE_WORDS if w in t]
        neg = [w for w in NEGATIVE_WORDS if w in t]
        entry = {
            "title": a.get("title","")[:100],
            "link":  a.get("link",""),
            "publisher": a.get("publisher",""),
        }
        if pos:
            total_pos += len(pos)
            entry["icon"]    = "✅"
            entry["signal"]  = "positive"
            entry["keywords"] = ", ".join(pos[:3])
        elif neg:
            total_neg += len(neg)
            entry["icon"]    = "🔴"
            entry["signal"]  = "negative"
            entry["keywords"] = ", ".join(neg[:3])
        else:
            entry["icon"]    = "⚪"
            entry["signal"]  = "neutral"
            entry["keywords"] = ""
        detail.append(entry)
    net = total_pos - total_neg
    if net >= 5:    return  2, "Very Positive", detail
    elif net >= 2:  return  1, "Positive",      detail
    elif net <= -5: return -2, "Very Negative", detail
    elif net <= -2: return -1, "Negative",      detail
    else:           return  0, "Neutral",       detail

# ------------------------------------------------
# TECHNICAL INDICATORS
# ------------------------------------------------

def calculate_rsi(s, w=14):
    d = s.diff()
    gain = d.where(d > 0, 0).rolling(w).mean()
    loss = (-d.where(d < 0, 0)).rolling(w).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(s):
    m = s.ewm(span=12,adjust=False).mean() - s.ewm(span=26,adjust=False).mean()
    return m, m.ewm(span=9,adjust=False).mean()

def calculate_bollinger(s, w=20):
    sma = s.rolling(w).mean()
    std = s.rolling(w).std()
    upper = sma + 2*std; lower = sma - 2*std
    return upper, lower, (s - lower)/(upper - lower)

def volume_trend(df):
    if len(df) < 20: return 0
    vs = df["Volume"].iloc[-5:].mean()
    vl = df["Volume"].iloc[-20:].mean()
    pc = df["Close"].iloc[-1] - df["Close"].iloc[-5]
    if vs > vl * 1.2:
        return 1 if pc > 0 else -1
    return 0

# ------------------------------------------------
# MULTI-SIGNAL SCORING ENGINE
# ------------------------------------------------

def generate_recommendation(df, stock_info, news_list):
    signals = []
    clean = df.dropna(subset=["Close"])
    if clean.empty:
        return "HOLD",50,"Medium","Insufficient data.",[],  "Neutral",[],50,None,None,0,0

    close = clean["Close"]
    price = close.iloc[-1]
    has26 = len(close) >= 26

    # RSI
    rsi_s = calculate_rsi(close)
    rsi   = rsi_s.iloc[-1] if not pd.isna(rsi_s.iloc[-1]) else 50
    if   rsi < 30: signals.append(("RSI", 1, 2, f"RSI {rsi:.1f} — oversold, potential buy"))
    elif rsi < 45: signals.append(("RSI", 1, 1, f"RSI {rsi:.1f} — mildly oversold"))
    elif rsi > 70: signals.append(("RSI",-1, 2, f"RSI {rsi:.1f} — overbought, pullback risk"))
    elif rsi > 55: signals.append(("RSI",-1, 1, f"RSI {rsi:.1f} — mildly overbought"))
    else:          signals.append(("RSI", 0, 1, f"RSI {rsi:.1f} — neutral"))

    # SMA cross
    sma20 = sma50 = None
    if has26:
        s20 = close.rolling(20).mean(); s50 = close.rolling(50).mean()
        if not pd.isna(s20.iloc[-1]) and not pd.isna(s50.iloc[-1]):
            sma20 = s20.iloc[-1]; sma50 = s50.iloc[-1]
            d = ((sma20-sma50)/sma50)*100
            if   d >  2: signals.append(("SMA Cross", 1, 2, f"SMA20 {d:.1f}% above SMA50 — golden cross"))
            elif d >  0: signals.append(("SMA Cross", 1, 1, "SMA20 slightly above SMA50 — mild uptrend"))
            elif d < -2: signals.append(("SMA Cross",-1, 2, f"SMA20 {abs(d):.1f}% below SMA50 — death cross"))
            else:        signals.append(("SMA Cross",-1, 1, "SMA20 slightly below SMA50 — mild downtrend"))

    # Price vs SMA20
    if sma20:
        if   price > sma20*1.02: signals.append(("Price vs SMA20", 1, 1, "Price above 20-day avg — short-term strength"))
        elif price < sma20*0.98: signals.append(("Price vs SMA20",-1, 1, "Price below 20-day avg — short-term weakness"))
        else:                    signals.append(("Price vs SMA20", 0, 1, "Price near 20-day avg — no directional signal"))

    # Price vs SMA50
    if sma50:
        if   price > sma50*1.03: signals.append(("Price vs SMA50", 1, 1, "Price above 50-day avg — medium-term uptrend"))
        elif price < sma50*0.97: signals.append(("Price vs SMA50",-1, 1, "Price below 50-day avg — medium-term downtrend"))
        else:                    signals.append(("Price vs SMA50", 0, 1, "Price near 50-day avg — range-bound"))

    # 5-day momentum
    mom5 = 0
    if len(close) >= 6:
        mom5 = ((close.iloc[-1]-close.iloc[-6])/close.iloc[-6])*100
        if   mom5 >  5: signals.append(("5D Momentum", 1, 1, f"+{mom5:.1f}% in 5 days — strong short-term momentum"))
        elif mom5 < -5: signals.append(("5D Momentum",-1, 1, f"{mom5:.1f}% in 5 days — selling pressure"))
        else:           signals.append(("5D Momentum", 0, 1, f"{mom5:.1f}% 5-day change — flat"))

    # 20-day momentum
    if len(close) >= 21:
        m20 = ((close.iloc[-1]-close.iloc[-21])/close.iloc[-21])*100
        if   m20 >  8: signals.append(("20D Momentum", 1, 1, f"+{m20:.1f}% over 20 days — medium-term bullish"))
        elif m20 < -8: signals.append(("20D Momentum",-1, 1, f"{m20:.1f}% over 20 days — medium-term bearish"))
        else:          signals.append(("20D Momentum", 0, 1, f"{m20:.1f}% 20-day change — moderate"))

    # MACD
    if has26:
        ml, ms = calculate_macd(close)
        mv, sv = ml.iloc[-1], ms.iloc[-1]
        if not pd.isna(mv) and not pd.isna(sv):
            diff = mv - sv; thr = price*0.005
            if   diff >  thr: signals.append(("MACD", 1, 2, "MACD above signal — bullish crossover"))
            elif diff >  0:   signals.append(("MACD", 1, 1, "MACD slightly above signal — early bullish"))
            elif diff < -thr: signals.append(("MACD",-1, 2, "MACD below signal — bearish crossover"))
            else:             signals.append(("MACD",-1, 1, "MACD slightly below signal — mild bearish"))

    # Bollinger
    if has26:
        _, _, bp_s = calculate_bollinger(close)
        bp = bp_s.iloc[-1]
        if not pd.isna(bp):
            if   bp < 0.15: signals.append(("Bollinger", 1, 2, "Near lower band — likely oversold"))
            elif bp < 0.35: signals.append(("Bollinger", 1, 1, "Lower half of bands — leaning oversold"))
            elif bp > 0.85: signals.append(("Bollinger",-1, 2, "Near upper band — likely overbought"))
            elif bp > 0.65: signals.append(("Bollinger",-1, 1, "Upper half of bands — leaning overbought"))
            else:           signals.append(("Bollinger", 0, 1, "Mid-band range — balanced"))

    # Volume
    if "Volume" in df.columns and len(clean) >= 20:
        vt = volume_trend(clean)
        if   vt ==  1: signals.append(("Volume", 1, 1, "High volume on up days — buyer conviction"))
        elif vt == -1: signals.append(("Volume",-1, 1, "High volume on down days — seller conviction"))
        else:          signals.append(("Volume", 0, 1, "Normal volume — no unusual activity"))

    # 52-week range
    w52h = stock_info.get("fiftyTwoWeekHigh")
    w52l = stock_info.get("fiftyTwoWeekLow")
    if w52h and w52l and w52h > w52l:
        p52 = (price-w52l)/(w52h-w52l)
        if   p52 < 0.20: signals.append(("52W Range", 1, 2, "Near 52W low — contrarian buy zone"))
        elif p52 < 0.40: signals.append(("52W Range", 1, 1, "Lower 40% of 52W range — relative value"))
        elif p52 > 0.85: signals.append(("52W Range",-1, 2, "Near 52W high — less margin of safety"))
        elif p52 > 0.65: signals.append(("52W Range",-1, 1, "Upper 35% of 52W range — some caution"))
        else:            signals.append(("52W Range", 0, 1, "Mid 52W range — neutral positioning"))

    # News sentiment
    ns, nl, nd = analyze_news_sentiment(news_list)
    nmap = {2:(1,2,"Very positive news — strong tailwind"),
             1:(1,1,"Positive news — mild tailwind"),
             0:(0,1,"Neutral news — no directional signal"),
            -1:(-1,1,"Negative news — mild headwind"),
            -2:(-1,2,"Very negative news — strong headwind")}
    nv,nw,ndesc = nmap[ns]
    signals.append(("News", nv, nw, ndesc))

    # Aggregate
    ws  = sum(v*w for _,v,w,_ in signals)
    mxs = sum(w   for _,_,w,_ in signals)
    pct = (ws/mxs)*100

    rec = "BUY" if pct >= 22 else "SELL" if pct <= -22 else "HOLD"
    conf = min(93, max(51, int(50 + abs(pct)*0.45)))

    buys  = [_ for _ in signals if _[1] == 1]
    sells = [_ for _ in signals if _[1] ==-1]
    nc    = len(signals)
    conflict = min(len(buys),len(sells))/nc if nc else 0

    risk = ("High" if rec=="SELL"
            else "Low–Medium" if rec=="BUY" and conflict<0.2 and conf>72
            else "Medium")

    tb = [d for _,v,w,d in signals if v==1  and w>=2]
    ts = [d for _,v,w,d in signals if v==-1 and w>=2]

    if rec=="BUY":
        summ = f"**{len(buys)} of {nc} signals are bullish.**\n\n" + (tb[0] if tb else "Multiple factors align positively.")
    elif rec=="SELL":
        summ = f"**{len(sells)} of {nc} signals are bearish.**\n\n" + (ts[0] if ts else "Multiple factors point to elevated risk.")
    else:
        summ = f"**Mixed: {len(buys)} bullish, {len(sells)} bearish of {nc} total.**\n\nNo strong directional conviction — holding or waiting is prudent."

    return rec, conf, risk, summ, signals, nl, nd, rsi, sma20, sma50, mom5, pct

# ------------------------------------------------
# DATA LOADERS
# ------------------------------------------------

@st.cache_data(ttl=1800)
def do_search(query):
    return search(query)

@st.cache_data(ttl=300)
def load_chart_data(ticker, period):
    p, i = PERIOD_MAP.get(period, ("1mo","1d"))
    return yf.Ticker(ticker).history(period=p, interval=i)

@st.cache_data(ttl=3600)
def load_analysis_data(ticker):
    return yf.Ticker(ticker).history(period="6mo", interval="1d")

@st.cache_data(ttl=1800)
def load_news(company_name):
    q   = company_name.replace(" ","+")
    url = f"https://news.google.com/rss/search?q={q}+stock"
    feed = feedparser.parse(url)
    return [
        {"title": e.title, "link": e.link,
         "publisher": e.source.title if hasattr(e,"source") else "Google News"}
        for e in feed.entries[:15]
    ]

# ------------------------------------------------
# APP HEADER
# ------------------------------------------------

st.markdown("""
<div class="app-header">
    <div class="app-header-icon">📈</div>
    <div>
        <h1>AI Investment Assistant</h1>
        <p>Multi-signal stock analysis · Beginner friendly · Live data</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# TOP CONTROLS: currency + search on same row
# ------------------------------------------------

# Align currency + search + button on one row with no label gaps
st.markdown("""
<style>
div[data-testid="stSelectbox"] > label { display: none !important; }
div[data-testid="stTextInput"]  > label { display: none !important; }
</style>
""", unsafe_allow_html=True)

col_curr, col_search, col_btn = st.columns([2, 5, 1])
with col_curr:
    currency_option = st.selectbox(
        "Currency",
        ["Original","USD","EUR","INR","GBP","JPY","AUD","CAD","CHF","CNY","SGD","AED"],
        label_visibility="collapsed"
    )
with col_search:
    search_text = st.text_input(
        "Search", placeholder="🔍  Search stock or ETF — e.g. Apple, Nvidia, Reliance…",
        label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("Search 🔍", width='stretch')

# ------------------------------------------------
# EXECUTE SEARCH → store results
# ------------------------------------------------

if search_clicked and search_text:
    with st.spinner("Searching markets…"):
        try:
            res = do_search(search_text)
            quotes = res.get("quotes", [])
            st.session_state.search_results = []
            for q in quotes[:8]:
                sym  = q.get("symbol","")
                name = q.get("shortname") or q.get("longname") or sym
                exch = q.get("exchange","")
                qt   = q.get("quoteType","")
                if sym and name:
                    st.session_state.search_results.append(
                        {"ticker":sym,"name":name,"exchange":exch,"type":qt}
                    )
            st.session_state.selected_ticker = None
            st.session_state.company_name    = None
        except Exception as e:
            st.error(f"Search error: {e}")

# ------------------------------------------------
# STOCK RESULT CARDS
# ------------------------------------------------

if st.session_state.search_results and not st.session_state.selected_ticker:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#94a3b8;font-size:0.82rem;font-weight:500;"
        "letter-spacing:.06em;text-transform:uppercase;margin-bottom:12px'>"
        "Select a stock</p>",
        unsafe_allow_html=True
    )

    TYPE_ICON = {"EQUITY":"📈","ETF":"📊","MUTUALFUND":"🏦","INDEX":"📉","CRYPTOCURRENCY":"₿"}
    EXCH_LABEL = {
        "NSI":"🇮🇳 NSE","BSE":"🇮🇳 BSE","NMS":"🇺🇸 NASDAQ",
        "NYQ":"🇺🇸 NYSE","LSE":"🇬🇧 LSE","TOR":"🇨🇦 TSX",
    }

    results = st.session_state.search_results
    cols = st.columns(2)
    for i, item in enumerate(results):
        icon  = TYPE_ICON.get(item["type"],"📌")
        exch  = EXCH_LABEL.get(item["exchange"], item["exchange"])
        label = f"{icon} **{item['name']}**\n\n`{item['ticker']}` · {exch}"
        with cols[i % 2]:
            if st.button(label, key=f"card_{i}", width='stretch'):
                st.session_state.selected_ticker = item["ticker"]
                st.session_state.company_name    = item["name"]
                st.session_state.search_results  = []
                st.rerun()

# ------------------------------------------------
# CHANGE STOCK BUTTON
# ------------------------------------------------

if st.session_state.selected_ticker:
    if st.button("← Search different stock"):
        st.session_state.selected_ticker = None
        st.session_state.company_name    = None
        st.session_state.search_results  = []
        st.rerun()

# ------------------------------------------------
# MAIN ANALYSIS
# ------------------------------------------------

if st.session_state.selected_ticker:
    try:
        # ── Time period pills ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#94a3b8;font-size:0.78rem;font-weight:500;"
            "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px'>"
            "Time Range</p>",
            unsafe_allow_html=True
        )
        pcols = st.columns(len(CHART_PERIODS))
        for i, p in enumerate(CHART_PERIODS):
            with pcols[i]:
                is_active = st.session_state.chart_period == p
                if st.button(p, key=f"p_{p}", width='stretch',
                              type="primary" if is_active else "secondary"):
                    st.session_state.chart_period = p
                    st.rerun()

        period = st.session_state.chart_period

        with st.spinner("Loading data and running analysis…"):
            stock      = yf.Ticker(st.session_state.selected_ticker)
            info       = stock.info
            orig_curr  = info.get("currency","USD")
            df_chart   = load_chart_data(st.session_state.selected_ticker, period)
            df_analysis= load_analysis_data(st.session_state.selected_ticker)
            news       = load_news(st.session_state.company_name)

        if df_analysis.empty and df_chart.empty:
            st.error("No market data available for this stock.")
            st.stop()

        if df_analysis.empty or len(df_analysis) < 10:
            df_analysis = df_chart

        # ── Price (NaN-safe) ──
        raw_price    = get_last_close(df_analysis, info)
        curr_price   = raw_price
        disp_curr    = orig_curr
        fx_rate      = 1.0

        try:
            if currency_option != "Original" and orig_curr != currency_option and not np.isnan(raw_price):
                fx_rate    = c.get_rate(orig_curr, currency_option)
                curr_price = raw_price * fx_rate
                disp_curr  = currency_option
        except:
            pass

        sym = get_currency_symbol(disp_curr)

        # Day change — convert prev to the same display currency using fx_rate
        raw_prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
        if raw_prev and not np.isnan(curr_price):
            prev_converted = float(raw_prev) * fx_rate
            day_chg     = curr_price - prev_converted
            day_chg_pct = (day_chg / prev_converted) * 100
        else:
            day_chg = day_chg_pct = None

        # ── Analysis ──
        (rec, conf, risk, summ, signals, news_label, news_detail,
         rsi, sma20, sma50, mom5, score_pct
        ) = generate_recommendation(df_analysis, info, news)

        # ── Stock name + ticker header ──
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:4px'>"
            f"<span style='font-size:clamp(1.3rem,3vw,1.6rem);font-weight:700;"
            f"letter-spacing:-0.02em'>{st.session_state.company_name}</span>"
            f"<span style='font-family:var(--mono,monospace);font-size:0.85rem;"
            f"background:#1a2235;border:1px solid #1f2d45;border-radius:6px;"
            f"padding:2px 10px;color:#94a3b8'>{st.session_state.selected_ticker}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        # ── Price row ──
        if not np.isnan(curr_price):
            price_str = f"{sym}{curr_price:,.2f}"
        else:
            price_str = "Price unavailable"

        if day_chg is not None:
            clr   = "#22c55e" if day_chg >= 0 else "#ef4444"
            arrow = "▲" if day_chg >= 0 else "▼"
            st.markdown(
                f"<div style='display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;"
                f"margin-bottom:20px'>"
                f"<span style='font-size:clamp(1.6rem,5vw,2.4rem);font-weight:700;"
                f"font-variant-numeric:tabular-nums;letter-spacing:-0.02em'>{price_str}</span>"
                f"<span style='color:{clr};font-size:clamp(0.85rem,2vw,1.05rem);font-weight:500'>"
                f"{arrow} {sym}{abs(day_chg):,.2f} ({day_chg_pct:+.2f}%)</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='font-size:clamp(1.6rem,5vw,2.4rem);font-weight:700;"
                f"margin-bottom:20px'>{price_str}</div>",
                unsafe_allow_html=True
            )

        # ── Metric cards ──
        rec_clr = {"BUY":"#22c55e","SELL":"#ef4444","HOLD":"#f59e0b"}[rec]
        rec_bg  = {"BUY":"rgba(34,197,94,0.08)","SELL":"rgba(239,68,68,0.08)","HOLD":"rgba(245,158,11,0.08)"}[rec]

        m1, m2, m3 = st.columns(3)
        cards = [
            (m1, "RECOMMENDATION", rec,        rec_clr, rec_bg),
            (m2, "CONFIDENCE",     f"{conf}%", "#38bdf8","rgba(56,189,248,0.08)"),
            (m3, "RISK",           risk,       "#a78bfa","rgba(167,139,250,0.08)"),
        ]
        for col, label, val, color, bg in cards:
            col.markdown(
                f"<div style='background:{bg};border:1px solid {color}33;"
                f"border-left:3px solid {color};padding:18px 16px;"
                f"border-radius:12px;'>"
                f"<div style='color:#64748b;font-size:0.7rem;font-weight:600;"
                f"letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px'>{label}</div>"
                f"<div style='color:{color};font-size:clamp(1.4rem,3vw,1.9rem);"
                f"font-weight:700;letter-spacing:-0.02em'>{val}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Signal score bar ──
        norm  = max(-100, min(100, score_pct))
        bclr  = "#22c55e" if norm > 0 else "#ef4444"
        bw    = abs(norm) / 2
        bside = "left:50%" if norm > 0 else f"right:50%"

        st.markdown(
            f"<div style='margin-bottom:4px'>"
            f"<span style='font-size:0.78rem;font-weight:600;color:#94a3b8;"
            f"letter-spacing:.06em;text-transform:uppercase'>Signal Score</span>"
            f"<span style='font-size:1rem;font-weight:700;color:{bclr};"
            f"margin-left:10px'>{score_pct:.0f} / 100</span>"
            f"</div>"
            f"<div style='background:#111827;border:1px solid #1f2d45;border-radius:8px;"
            f"height:10px;width:100%;position:relative;overflow:hidden;'>"
            f"<div style='position:absolute;left:50%;top:0;height:100%;width:1px;"
            f"background:#334155;z-index:2'></div>"
            f"<div style='position:absolute;{bside};top:0;height:100%;"
            f"width:{bw:.1f}%;background:{bclr};border-radius:4px;"
            f"transition:width 0.4s ease'></div>"
            f"</div>"
            f"<div style='display:flex;justify-content:space-between;"
            f"font-size:0.68rem;color:#475569;margin-top:4px;'>"
            f"<span>◀ SELL</span><span>HOLD</span><span>BUY ▶</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── Chart ──
        df_plot = (df_chart.dropna(subset=["Close"]) if not df_chart.empty
                   else df_analysis.dropna(subset=["Close"]))

        if not df_plot.empty:
            intraday = period in ("1D","3D","5D")
            fig = go.Figure()

            if intraday:
                fig.add_trace(go.Scatter(
                    x=df_plot.index, y=df_plot["Close"], mode="lines",
                    name="Price", line=dict(width=2, color="#38bdf8"),
                    fill="tozeroy", fillcolor="rgba(56,189,248,0.06)"
                ))
            else:
                s20 = df_plot["Close"].rolling(20).mean()
                s50 = df_plot["Close"].rolling(50).mean()
                fig.add_trace(go.Scatter(
                    x=df_plot.index, y=df_plot["Close"],
                    mode="lines", name="Price",
                    line=dict(width=2, color="#38bdf8")
                ))
                fig.add_trace(go.Scatter(
                    x=df_plot.index, y=s20,
                    mode="lines", name="SMA20",
                    line=dict(dash="dash", width=1.2, color="#f59e0b")
                ))
                fig.add_trace(go.Scatter(
                    x=df_plot.index, y=s50,
                    mode="lines", name="SMA50",
                    line=dict(dash="dot", width=1.2, color="#a78bfa")
                ))

            mn  = df_plot["Close"].min()
            mx  = df_plot["Close"].max()
            pad = max((mx-mn)*0.12, 1)
            fig.update_layout(
                height=380,
                hovermode="x unified",
                margin=dict(l=0, r=0, t=8, b=0),
                xaxis_title=None,
                yaxis_title=f"Price ({disp_curr})",
                yaxis=dict(range=[mn-pad, mx+pad]),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(17,24,39,0.6)",
                font=dict(family="DM Sans, sans-serif", color="#94a3b8", size=11),
                xaxis=dict(
                    gridcolor="#1f2d45", gridwidth=1,
                    showline=False, zeroline=False
                ),
                yaxis_gridcolor="#1f2d45",
                hoverlabel=dict(
                    bgcolor="#1a2235",
                    bordercolor="#1f2d45",
                    font=dict(family="DM Mono, monospace", size=12)
                ),
            )

            # Custom legend row above chart — no overlap with zoom controls
            if intraday:
                legend_html = """
                <div style="display:flex;align-items:center;gap:20px;
                            padding:6px 4px 10px 4px;flex-wrap:wrap;">
                    <span style="display:flex;align-items:center;gap:7px;
                                 font-size:0.8rem;color:#94a3b8;font-weight:500">
                        <span style="display:inline-block;width:24px;height:2px;
                                     background:#38bdf8;border-radius:2px"></span>
                        Price
                    </span>
                </div>"""
            else:
                legend_html = """
                <div style="display:flex;align-items:center;gap:20px;
                            padding:6px 4px 10px 4px;flex-wrap:wrap;">
                    <span style="display:flex;align-items:center;gap:7px;
                                 font-size:0.8rem;color:#94a3b8;font-weight:500">
                        <span style="display:inline-block;width:24px;height:2px;
                                     background:#38bdf8;border-radius:2px"></span>
                        Price
                    </span>
                    <span style="display:flex;align-items:center;gap:7px;
                                 font-size:0.8rem;color:#94a3b8;font-weight:500">
                        <span style="display:inline-block;width:24px;height:2px;
                                     background:#f59e0b;border-radius:2px;
                                     border-top:2px dashed #f59e0b;height:0"></span>
                        SMA 20
                    </span>
                    <span style="display:flex;align-items:center;gap:7px;
                                 font-size:0.8rem;color:#94a3b8;font-weight:500">
                        <span style="display:inline-block;width:24px;height:0;
                                     border-top:2px dotted #a78bfa"></span>
                        SMA 50
                    </span>
                </div>"""
            st.markdown(legend_html, unsafe_allow_html=True)
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("Chart data unavailable for selected period.")

        # ── AI Summary ──
        st.markdown(
            "<p style='color:#94a3b8;font-size:0.78rem;font-weight:600;"
            "letter-spacing:.06em;text-transform:uppercase;margin:8px 0 8px 0'>"
            "🤖 AI Summary</p>",
            unsafe_allow_html=True
        )
        if rec == "BUY":    st.success(summ)
        elif rec == "SELL": st.error(summ)
        else:               st.warning(summ)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Signal Breakdown ──
        with st.expander("🔍 Full Signal Breakdown"):
            b_sigs = [(n,d) for n,v,w,d in signals if v== 1]
            s_sigs = [(n,d) for n,v,w,d in signals if v==-1]
            n_sigs = [(n,d) for n,v,w,d in signals if v== 0]

            if b_sigs:
                st.markdown(
                    "<p style='color:#22c55e;font-size:0.8rem;font-weight:600;"
                    "letter-spacing:.05em;text-transform:uppercase'>🟢 Bullish Signals</p>",
                    unsafe_allow_html=True
                )
                for nm,ds in b_sigs:
                    st.markdown(f"- **{nm}**: {ds}")
            if s_sigs:
                st.markdown(
                    "<p style='color:#ef4444;font-size:0.8rem;font-weight:600;"
                    "letter-spacing:.05em;text-transform:uppercase;margin-top:12px'>🔴 Bearish Signals</p>",
                    unsafe_allow_html=True
                )
                for nm,ds in s_sigs:
                    st.markdown(f"- **{nm}**: {ds}")
            if n_sigs:
                st.markdown(
                    "<p style='color:#94a3b8;font-size:0.8rem;font-weight:600;"
                    "letter-spacing:.05em;text-transform:uppercase;margin-top:12px'>⚪ Neutral Signals</p>",
                    unsafe_allow_html=True
                )
                for nm,ds in n_sigs:
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

        # ── News Sentiment ──
        with st.expander(f"📰 News Sentiment — {news_label}"):
            if "Positive" in news_label:   st.success(f"Sentiment: **{news_label}**")
            elif "Negative" in news_label: st.error(f"Sentiment: **{news_label}**")
            else:                          st.info(f"Sentiment: **{news_label}**")
            for item in news_detail:
                icon  = item["icon"]
                title = item["title"]
                link  = item["link"]
                pub   = item["publisher"]
                kw    = item["keywords"]
                kw_html = (f" <span style='font-size:0.72rem;color:#64748b'>— {kw}</span>"
                           if kw else "")
                pub_html = (f" <span style='font-size:0.7rem;color:#475569'>· {pub}</span>"
                            if pub else "")
                if link:
                    title_html = f"<a href='{link}' target='_blank' class='news-link'>{title}</a>"
                else:
                    title_html = title
                st.markdown(
                    f"<div style='padding:8px 0;border-bottom:1px solid #1a2235;"
                    f"font-size:0.85rem;line-height:1.5'>"
                    f"{icon} {title_html}{kw_html}{pub_html}"
                    f"</div>",
                    unsafe_allow_html=True
                )

        # ── Education ──
        with st.expander("📚 What do these indicators mean?"):
            st.markdown("""
**RSI** — Below 30 = oversold (buy signal). Above 70 = overbought (sell risk).

**SMA20 / SMA50** — Moving averages. SMA20 crossing above SMA50 = bullish golden cross.

**MACD** — Momentum. Crossover above signal line = bullish shift.

**Bollinger Bands** — Price near lower band = oversold. Near upper = overbought.

**52-Week Range** — Near yearly low = potential value. Near yearly high = less upside buffer.

**News Sentiment** — Headlines scanned for positive/negative keywords to gauge market mood.
""")

        # ── CTA ──
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:1rem;font-weight:600;margin-bottom:8px'>💼 Start Investing</p>"
            "<p style='color:#94a3b8;font-size:0.85rem;margin-bottom:14px'>"
            "Create an account via the link below to secure a welcome bonus.</p>",
            unsafe_allow_html=True
        )
        st.link_button("Join Trade Republic →", "https://refnocode.trade.re/wnk12lwn")

        # ── Disclaimer ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(
            "⚠️ This tool is for educational and personal research purposes only. "
            "No AI can predict markets perfectly. Always do your own due diligence before investing."
        )

    except Exception as e:
        st.error(f"Error loading stock data: {e}")
        st.exception(e)