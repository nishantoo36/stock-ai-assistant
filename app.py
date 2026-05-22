import streamlit as st
from html import escape
from urllib.parse import urlencode

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from ui.auth import (
    LOGOUT_FLAG,
    OAUTH_VERIFIER_COOKIE,
    is_logged_in,
    persist_current_auth_session,
    restore_auth_session,
    store_auth_session,
)


def _attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _query_param(query_params, name: str) -> str | None:
    value = query_params.get(name)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _set_query_param(name: str, value: str | None) -> None:
    current = _query_param(st.query_params, name)
    if value:
        if current != value:
            st.query_params[name] = value
    elif current is not None:
        st.query_params.pop(name, None)


# ── Handle Supabase auth callbacks ────────────────────────────────────────────
def _handle_auth_callback() -> None:
    """Process auth tokens or OAuth codes from Supabase callback links."""
    query_params = st.query_params
    if not query_params:
        return

    auth_error = _query_param(query_params, "error_description") or _query_param(
        query_params, "error"
    )
    if auth_error:
        st.error(f"Authentication failed: {auth_error}")
        st.query_params.clear()
        return

    access_token = _query_param(query_params, "access_token")
    refresh_token = _query_param(query_params, "refresh_token")
    auth_code = _query_param(query_params, "code")

    if auth_code:
        try:
            from utils.supabase_client import exchange_oauth_code

            code_verifier = st.context.cookies.get(OAUTH_VERIFIER_COOKIE)
            if not code_verifier:
                st.error("Authentication failed: login session expired. Please try signing in again.")
                st.query_params.clear()
                return

            response = exchange_oauth_code(auth_code, code_verifier)
            if store_auth_session(response):
                st.query_params.clear()
                st.rerun()
        except Exception as exc:
            st.error(f"Authentication failed: {exc}")
            st.query_params.clear()
        return

    if access_token:
        st.session_state.pop(LOGOUT_FLAG, None)
        st.session_state.auth_session = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        # Try to get user info from the token
        try:
            from utils.supabase_client import get_user_supabase_client
            client = get_user_supabase_client(access_token)
            user_info = client.auth.get_user(access_token)
            if user_info:
                st.session_state.auth_user = {
                    "id": _attr(user_info.user, "id", ""),
                    "email": _attr(user_info.user, "email", ""),
                    "phone": _attr(user_info.user, "phone", ""),
                }
        except Exception:
            pass  # Continue anyway, user will be authenticated
        
        # Clear the query parameters
        st.query_params.clear()
        st.rerun()

_handle_auth_callback()

from utils.styles  import inject_css
from utils.i18n    import t, set_language, get_current_language, get_available_languages, get_language_flag
from utils.data    import load_live_price
from ui.auth       import render_auth_panel, render_login_section
from ui.alerts     import render_notifications_button
from ui.search     import (
    _execute_search,
    render_no_results,
    render_result_cards,
    render_search_bar,
)
from ui.stock_view import render_stock_view
from ui.user_stocks import render_watchlist_button

inject_css()
restore_auth_session()
persist_current_auth_session()

# ── Always-visible language selector ─────────────────────────────────────────
def render_language_selector() -> None:
    available_langs = get_available_languages()
    lang_options = [
        (f"{get_language_flag(code)} {code.upper()}", code)
        for code in available_langs
    ]
    current_lang = get_current_language()
    current_display = next(
        (display for display, code in lang_options if code == current_lang),
        lang_options[0][0]
    )

    selected_lang_display = st.selectbox(
        t("common.language"),
        [display for display, _ in lang_options],
        index=[display for display, _ in lang_options].index(current_display),
        key="language_selector",
        label_visibility="collapsed",
    )

    selected_lang_code = next(
        (code for display, code in lang_options if display == selected_lang_display),
        "en"
    )
    set_language(selected_lang_code)


# ── Session state defaults ────────────────────────────────────────────────────
for key, default in {
    "selected_ticker":   None,
    "company_name":      None,
    "search_results":    [],
    "chart_period":      "1D",
    "search_no_results": None,
    "show_login":        False,
    "search_query":      "",
    "last_search_query": "",
    "selected_countries": [],
    "countries_url_value": None,
    "quick_topic": "trending",
    "topic_url_value": None,
    "reset_search_query": False,
    "url_selected_stock": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if _query_param(st.query_params, "auth"):
    st.query_params.pop("auth", None)


url_stock = _query_param(st.query_params, "stock")
url_company = _query_param(st.query_params, "company")
if url_stock:
    if st.session_state.selected_ticker != url_stock:
        st.session_state.selected_ticker = url_stock
        st.session_state.company_name = url_company or url_stock
        st.session_state.search_results = []
        st.session_state.search_no_results = None
    st.session_state.url_selected_stock = True
elif st.session_state.get("url_selected_stock"):
    st.session_state.selected_ticker = None
    st.session_state.company_name = None
    st.session_state.search_results = []
    st.session_state.search_no_results = None
    st.session_state.url_selected_stock = False

url_search_query = _query_param(st.query_params, "q")
if not url_stock and url_search_query:
    if (
        st.session_state.get("last_search_query") != url_search_query
        or not st.session_state.search_results
    ):
        st.session_state.search_query = url_search_query
        _execute_search(url_search_query, update_url=False)
elif not url_stock and not url_search_query and st.session_state.get("last_search_query"):
    st.session_state.search_results = []
    st.session_state.search_no_results = None
    st.session_state.reset_search_query = True
    st.session_state.last_search_query = ""

QUICK_TOPIC_KEYS = {"trending", "best_etfs", "dividend", "ai", "undervalued"}
url_topic = _query_param(st.query_params, "topic")
if st.session_state.get("topic_url_value") != url_topic:
    st.session_state.quick_topic = url_topic if url_topic in QUICK_TOPIC_KEYS else "trending"
    st.session_state.topic_url_value = url_topic
    if st.session_state.quick_topic != "trending":
        st.session_state.search_results = []
        st.session_state.search_no_results = None
        st.session_state.search_query = ""
        st.session_state.last_search_query = ""

# ── Header ────────────────────────────────────────────────────────────────────
header_ratio = [1.05, 1.65] if is_logged_in() else [1.45, 1]
header_col, action_col = st.columns(header_ratio, vertical_alignment="center")
with header_col:
    st.markdown("""
    <div class="app-header">
        <div class="app-header-icon">📈</div>
        <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
    </div>
    """.format(title=t("app.title"), subtitle=t("app.subtitle")), unsafe_allow_html=True)

with action_col:
    if is_logged_in():
        lang_col, watch_col, notif_col, account_col = st.columns([1.15, 1.15, 1.15, 1.0])
        with lang_col:
            render_language_selector()
        with watch_col:
            render_watchlist_button()
        with notif_col:
            render_notifications_button()
        with account_col:
            render_auth_panel()
    else:
        lang_col, account_col = st.columns([1.2, 1])
        with lang_col:
            render_language_selector()
        with account_col:
            render_auth_panel()

def set_quick_topic(topic: str) -> None:
    st.session_state.quick_topic = topic
    st.session_state.topic_url_value = topic if topic != "trending" else None
    st.session_state.search_results = []
    st.session_state.search_no_results = None
    st.session_state.reset_search_query = True
    st.session_state.last_search_query = ""
    st.query_params.pop("q", None)
    st.query_params.pop("stock", None)
    st.query_params.pop("company", None)
    _set_query_param("topic", topic if topic != "trending" else None)
    st.rerun()


COUNTRY_MARKETS = {
    "United States": {
        "label": "🇺🇸 United States",
        "indexes": [
            ("S&P 500", "^GSPC", "USD"),
            ("NASDAQ", "^IXIC", "USD"),
        ],
        "stocks": [
            ("Apple", "AAPL", "USD"),
            ("Nvidia", "NVDA", "USD"),
            ("Microsoft", "MSFT", "USD"),
            ("Tesla", "TSLA", "USD"),
        ],
    },
    "India": {
        "label": "🇮🇳 India",
        "indexes": [
            ("NIFTY 50", "^NSEI", "INR"),
            ("SENSEX", "^BSESN", "INR"),
        ],
        "stocks": [
            ("Reliance", "RELIANCE.NS", "INR"),
            ("TCS", "TCS.NS", "INR"),
            ("Infosys", "INFY.NS", "INR"),
            ("HDFC Bank", "HDFCBANK.NS", "INR"),
        ],
    },
    "United Kingdom": {
        "label": "🇬🇧 United Kingdom",
        "indexes": [
            ("FTSE 100", "^FTSE", "GBp"),
            ("FTSE 250", "^FTMC", "GBp"),
        ],
        "stocks": [
            ("AstraZeneca", "AZN.L", "GBp"),
            ("Shell", "SHEL.L", "GBp"),
            ("HSBC", "HSBA.L", "GBp"),
            ("Unilever", "ULVR.L", "GBp"),
        ],
    },
    "Japan": {
        "label": "🇯🇵 Japan",
        "indexes": [
            ("Nikkei 225", "^N225", "JPY"),
            ("TOPIX", "^TOPX", "JPY"),
        ],
        "stocks": [
            ("Toyota", "7203.T", "JPY"),
            ("Sony", "6758.T", "JPY"),
            ("SoftBank", "9984.T", "JPY"),
            ("Nintendo", "7974.T", "JPY"),
        ],
    },
    "Germany": {
        "label": "🇩🇪 Germany",
        "indexes": [
            ("DAX", "^GDAXI", "EUR"),
            ("MDAX", "^MDAXI", "EUR"),
        ],
        "stocks": [
            ("SAP", "SAP.DE", "EUR"),
            ("Siemens", "SIE.DE", "EUR"),
            ("Allianz", "ALV.DE", "EUR"),
            ("Mercedes-Benz", "MBG.DE", "EUR"),
        ],
    },
    "Canada": {
        "label": "🇨🇦 Canada",
        "indexes": [
            ("TSX", "^GSPTSE", "CAD"),
            ("TSX Venture", "^SPCDNX", "CAD"),
        ],
        "stocks": [
            ("Shopify", "SHOP.TO", "CAD"),
            ("Royal Bank", "RY.TO", "CAD"),
            ("Enbridge", "ENB.TO", "CAD"),
            ("Brookfield", "BN.TO", "CAD"),
        ],
    },
}

GLOBAL_MARKET = {
    "indexes": [
        ("S&P 500", "^GSPC", "USD"),
        ("NASDAQ", "^IXIC", "USD"),
        ("Bitcoin", "BTC-USD", "USD"),
        ("Gold", "GC=F", "USD"),
    ],
    "stocks": [
        ("Apple", "AAPL", "USD"),
        ("Nvidia", "NVDA", "USD"),
        ("Reliance", "RELIANCE.NS", "INR"),
        ("Toyota", "7203.T", "JPY"),
    ],
}

QUICK_TOPIC_MARKETS = {
    "best_etfs": {
        "global": [
            ("SPDR S&P 500 ETF", "SPY", "USD"),
            ("Vanguard Total Stock Market ETF", "VTI", "USD"),
            ("Invesco QQQ Trust", "QQQ", "USD"),
            ("iShares MSCI ACWI ETF", "ACWI", "USD"),
        ],
        "countries": {
            "United States": [
                ("SPDR S&P 500 ETF", "SPY", "USD"),
                ("Vanguard Total Stock Market ETF", "VTI", "USD"),
                ("Invesco QQQ Trust", "QQQ", "USD"),
            ],
            "India": [
                ("Nippon India Nifty 50 Bees", "NIFTYBEES.NS", "INR"),
                ("SBI Nifty 50 ETF", "SETFNIF50.NS", "INR"),
                ("ICICI Prudential Nifty ETF", "ICICINIFTY.NS", "INR"),
            ],
            "United Kingdom": [
                ("iShares Core FTSE 100 ETF", "ISF.L", "GBp"),
                ("Vanguard FTSE 100 UCITS ETF", "VUKE.L", "GBp"),
            ],
            "Japan": [
                ("NEXT FUNDS Nikkei 225 ETF", "1321.T", "JPY"),
                ("iShares Core TOPIX ETF", "1475.T", "JPY"),
            ],
            "Germany": [
                ("iShares Core DAX ETF", "EXS1.DE", "EUR"),
                ("Xtrackers DAX UCITS ETF", "DBXD.DE", "EUR"),
            ],
            "Canada": [
                ("iShares S&P/TSX 60 ETF", "XIU.TO", "CAD"),
                ("Vanguard FTSE Canada ETF", "VCE.TO", "CAD"),
            ],
        },
    },
    "dividend": {
        "global": [
            ("Johnson & Johnson", "JNJ", "USD"),
            ("Coca-Cola", "KO", "USD"),
            ("Procter & Gamble", "PG", "USD"),
            ("Royal Bank of Canada", "RY.TO", "CAD"),
        ],
        "countries": {
            "United States": [("Coca-Cola", "KO", "USD"), ("Johnson & Johnson", "JNJ", "USD"), ("Procter & Gamble", "PG", "USD")],
            "India": [("HDFC Bank", "HDFCBANK.NS", "INR"), ("Infosys", "INFY.NS", "INR"), ("ITC", "ITC.NS", "INR")],
            "United Kingdom": [("Shell", "SHEL.L", "GBp"), ("HSBC", "HSBA.L", "GBp"), ("Unilever", "ULVR.L", "GBp")],
            "Japan": [("Toyota", "7203.T", "JPY"), ("Nintendo", "7974.T", "JPY"), ("Sony", "6758.T", "JPY")],
            "Germany": [("Allianz", "ALV.DE", "EUR"), ("Siemens", "SIE.DE", "EUR"), ("Mercedes-Benz", "MBG.DE", "EUR")],
            "Canada": [("Royal Bank", "RY.TO", "CAD"), ("Enbridge", "ENB.TO", "CAD"), ("Brookfield", "BN.TO", "CAD")],
        },
    },
    "ai": {
        "global": [
            ("Nvidia", "NVDA", "USD"),
            ("Microsoft", "MSFT", "USD"),
            ("Alphabet", "GOOGL", "USD"),
            ("Taiwan Semiconductor", "TSM", "USD"),
        ],
        "countries": {
            "United States": [("Nvidia", "NVDA", "USD"), ("Microsoft", "MSFT", "USD"), ("Alphabet", "GOOGL", "USD"), ("AMD", "AMD", "USD")],
            "India": [("TCS", "TCS.NS", "INR"), ("Infosys", "INFY.NS", "INR"), ("HCLTech", "HCLTECH.NS", "INR")],
            "United Kingdom": [("Sage Group", "SGE.L", "GBp"), ("Ocado", "OCDO.L", "GBp"), ("Darktrace", "DARK.L", "GBp")],
            "Japan": [("Sony", "6758.T", "JPY"), ("SoftBank", "9984.T", "JPY"), ("Tokyo Electron", "8035.T", "JPY")],
            "Germany": [("SAP", "SAP.DE", "EUR"), ("Siemens", "SIE.DE", "EUR"), ("Infineon", "IFX.DE", "EUR")],
            "Canada": [("Shopify", "SHOP.TO", "CAD"), ("Constellation Software", "CSU.TO", "CAD"), ("OpenText", "OTEX.TO", "CAD")],
        },
    },
    "undervalued": {
        "global": [
            ("Berkshire Hathaway", "BRK-B", "USD"),
            ("Toyota", "7203.T", "JPY"),
            ("Shell", "SHEL.L", "GBp"),
            ("HDFC Bank", "HDFCBANK.NS", "INR"),
        ],
        "countries": {
            "United States": [("Berkshire Hathaway", "BRK-B", "USD"), ("JPMorgan Chase", "JPM", "USD"), ("Intel", "INTC", "USD")],
            "India": [("HDFC Bank", "HDFCBANK.NS", "INR"), ("Reliance", "RELIANCE.NS", "INR"), ("Infosys", "INFY.NS", "INR")],
            "United Kingdom": [("Shell", "SHEL.L", "GBp"), ("HSBC", "HSBA.L", "GBp"), ("AstraZeneca", "AZN.L", "GBp")],
            "Japan": [("Toyota", "7203.T", "JPY"), ("Sony", "6758.T", "JPY"), ("Nintendo", "7974.T", "JPY")],
            "Germany": [("Mercedes-Benz", "MBG.DE", "EUR"), ("Allianz", "ALV.DE", "EUR"), ("Siemens", "SIE.DE", "EUR")],
            "Canada": [("Royal Bank", "RY.TO", "CAD"), ("Enbridge", "ENB.TO", "CAD"), ("Brookfield", "BN.TO", "CAD")],
        },
    },
}


def _currency_prefix(currency: str) -> str:
    return {
        "USD": "$",
        "EUR": "€",
        "INR": "₹",
        "JPY": "¥",
        "CAD": "C$",
        "GBp": "£",
    }.get(currency, "")


def _format_live_price(price, currency: str) -> str:
    if price is None:
        return "Unavailable"

    try:
        price = float(price)
    except (TypeError, ValueError):
        return "Unavailable"

    if price != price:
        return "Unavailable"

    decimals = 0 if currency in {"", "JPY", "GBp"} else 2
    if currency == "GBp":
        price = price / 100
        decimals = 2
    return f"{_currency_prefix(currency)}{price:,.{decimals}f}"


def _format_live_change(price, previous_close) -> str | None:
    if price is None or previous_close is None:
        return None

    try:
        price = float(price)
        previous_close = float(previous_close)
    except (TypeError, ValueError):
        return None

    if price != price or previous_close != previous_close:
        return None

    if previous_close <= 0:
        return None

    pct = ((price - previous_close) / previous_close) * 100
    return f"{pct:+.2f}%"


def get_live_market_quote(symbol: str, currency: str) -> tuple[str, str]:
    try:
        live = load_live_price(symbol)
    except Exception:
        return t("common.unavailable"), t("homepage.not_available")

    price = live.get("price")
    previous_close = live.get("previous_close")
    return (
        _format_live_price(price, currency).replace("Unavailable", t("common.unavailable")),
        _format_live_change(price, previous_close) or t("homepage.not_available"),
    )


def get_homepage_market_data(selected_countries: list[str]) -> tuple[list, list]:
    if not selected_countries:
        return GLOBAL_MARKET["indexes"], GLOBAL_MARKET["stocks"]

    indexes = []
    stocks = []
    for country in selected_countries:
        market = COUNTRY_MARKETS.get(country)
        if market:
            indexes.extend(market["indexes"])
            stocks.extend(market["stocks"])

    return indexes[:4], stocks[:5]


def get_quick_topic_stocks(topic: str, selected_countries: list[str]) -> list[tuple[str, str, str]]:
    topic_data = QUICK_TOPIC_MARKETS.get(topic)
    if not topic_data:
        return get_homepage_market_data(selected_countries)[1]

    if not selected_countries:
        return topic_data["global"][:5]

    stocks = []
    seen = set()
    for country in selected_countries:
        for stock in topic_data["countries"].get(country, []):
            if stock[1] in seen:
                continue
            seen.add(stock[1])
            stocks.append(stock)
            if len(stocks) >= 5:
                return stocks
    return stocks


def get_ai_picks(selected_countries: list[str]) -> list[tuple[str, str, str]]:
    picks = get_quick_topic_stocks("ai", selected_countries)
    reason_keys = [
        "homepage.ai_pick_momentum",
        "homepage.ai_pick_growth",
        "homepage.ai_pick_expansion",
    ]
    return [
        (symbol, company_name, t(reason_keys[index % len(reason_keys)]))
        for index, (company_name, symbol, _currency) in enumerate(picks[:3])
    ]


def _countries_from_query(country_options: list[str]) -> list[str]:
    countries_value = _query_param(st.query_params, "countries")
    if st.session_state.get("countries_url_value") == countries_value:
        return st.session_state.selected_countries

    selected = []
    if countries_value:
        selected = [
            country
            for country in countries_value.split(",")
            if country in country_options
        ][:5]

    st.session_state.selected_countries = selected
    st.session_state.countries_url_value = countries_value
    return selected


def _sync_countries_to_url(selected_countries: list[str]) -> None:
    countries_value = ",".join(selected_countries[:5])
    _set_query_param("countries", countries_value or None)
    st.session_state.countries_url_value = countries_value or None


def stock_url(ticker: str, company_name: str) -> str:
    params = {}
    for key in ("lang", "q", "countries"):
        value = _query_param(st.query_params, key)
        if value:
            params[key] = value
    topic = _query_param(st.query_params, "topic")
    if topic and topic != "trending":
        params["topic"] = topic
    params["stock"] = ticker
    params["company"] = company_name
    return f"?{urlencode(params)}"


if st.session_state.get("show_login") and not is_logged_in():
    render_login_section()

# ── Search ────────────────────────────────────────────────────────────────────
currency_option = render_search_bar()
render_no_results()
render_result_cards()


# ── Homepage widgets (only show when no stock or search results displayed) ────
if not st.session_state.selected_ticker and not st.session_state.search_results:
    st.markdown("""
    <style>
    .stock-card {
        display: block;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        color: var(--text) !important;
        text-decoration: none !important;
        font-size: 0.9rem;
        line-height: 1.45;
    }
    .stock-card:hover {
        border-color: var(--accent);
        color: var(--accent) !important;
    }
    .stock-card b {
        color: inherit;
    }
    .stock-card .positive {
        color: var(--green);
        font-family: var(--mono);
    }
    .stock-card .negative {
        color: var(--red);
        font-family: var(--mono);
    }
    .stock-card .neutral {
        color: var(--muted);
        font-family: var(--mono);
    }
    .ai-pick-link {
        display: block;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        color: var(--text) !important;
        text-decoration: none !important;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .ai-pick-link:hover {
        border-color: var(--accent);
        color: var(--accent) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"### 🚀 {t('homepage.quick_explore')}")

    country_options = list(COUNTRY_MARKETS.keys())
    _countries_from_query(country_options)
    selected_countries = st.multiselect(
        t("homepage.country"),
        country_options,
        format_func=lambda country: t(f"homepage.countries.{country}"),
        key="selected_countries",
        placeholder=t("homepage.country_placeholder"),
        max_selections=5,
    )
    _sync_countries_to_url(selected_countries)

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        if st.button(t("homepage.best_etfs"), use_container_width=True):
            set_quick_topic("best_etfs")

    with q2:
        if st.button(t("homepage.dividend_stocks"), use_container_width=True):
            set_quick_topic("dividend")

    with q3:
        if st.button(t("homepage.ai_stocks"), use_container_width=True):
            set_quick_topic("ai")

    with q4:
        if st.button(t("homepage.undervalued_stocks"), use_container_width=True):
            set_quick_topic("undervalued")

    market_indexes, trending_stocks = get_homepage_market_data(selected_countries)
    quick_topic = st.session_state.get("quick_topic", "trending")
    display_stocks = (
        trending_stocks
        if quick_topic == "trending"
        else get_quick_topic_stocks(quick_topic, selected_countries)
    )

    # Market Snapshot
    snapshot_title = (
        f"### 📊 {t('homepage.global_market_snapshot')}"
        if not selected_countries
        else f"### 📊 {t('homepage.selected_country_markets')}"
    )
    st.markdown(snapshot_title)

    snapshot_cols = st.columns(4)
    for i, (label, symbol, market_currency) in enumerate(market_indexes):
        value, delta = get_live_market_quote(symbol, market_currency)
        with snapshot_cols[i % 4]:
            st.metric(label, value, delta)


    # Main content
    left, right = st.columns([2, 1])

    with left:
        if quick_topic == "trending":
            section_title = (
                f"### 🔥 {t('homepage.global_trending_stocks')}"
                if not selected_countries
                else f"### 🔥 {t('homepage.trending_stocks_by_country')}"
            )
        else:
            title_by_topic = {
                "best_etfs": t("homepage.best_etfs"),
                "dividend": t("homepage.dividend_stocks"),
                "ai": t("homepage.ai_stocks"),
                "undervalued": t("homepage.undervalued_stocks"),
            }
            section_title = f"### 🔎 {title_by_topic.get(quick_topic, t('homepage.global_trending_stocks'))}"
        st.markdown(section_title)

        for stock, symbol, stock_currency in display_stocks:
            price, change = get_live_market_quote(symbol, stock_currency)
            change_class = "positive" if change.startswith("+") else "negative" if change.startswith("-") else "neutral"
            st.markdown(f"""
            <a class="stock-card" href="{stock_url(symbol, stock)}">
                <b>{escape(stock)}</b> <span style="color:#64748b;font-family:var(--mono);font-size:0.78rem">{escape(symbol)}</span><br>
                {t("homepage.price")}: {price}<br>
                {t("homepage.change")}: <span class="{change_class}">{change}</span>
            </a>
            """, unsafe_allow_html=True)

    with right:
        st.markdown(f"### 🤖 {t('homepage.ai_picks_today')}")

        ai_picks = get_ai_picks(selected_countries)

        for ticker, company_name, reason in ai_picks:
            st.markdown(
                f'<a class="ai-pick-link" href="{stock_url(ticker, company_name)}">'
                f'{ticker} → {reason}</a>',
                unsafe_allow_html=True,
            )


    # Educational section
    st.markdown(f"### 📚 {t('homepage.learn_before_invest')}")

    e1, e2, e3 = st.columns(3)

    with e1:
        with st.expander(t("homepage.analyze_stock_title")):
            st.markdown(t("homepage.analyze_stock_body"))

    with e2:
        with st.expander(t("homepage.etf_basics_title")):
            st.markdown(t("homepage.etf_basics_body"))

    with e3:
        with st.expander(t("homepage.risk_management_title")):
            st.markdown(t("homepage.risk_management_body"))

# ── Stock view ────────────────────────────────────────────────────────────────
if st.session_state.selected_ticker:
    render_stock_view(currency_option)
