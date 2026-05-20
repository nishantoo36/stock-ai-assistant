import streamlit as st

def inject_css():
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
    padding: 0 0 18px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 22px;
}
.app-header-icon { font-size: 2rem; line-height: 1; }
.app-header h1 {
    font-size: clamp(1.3rem, 3vw, 1.75rem) !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    margin: 0 !important;
    padding: 0 !important;
    letter-spacing: -0.02em;
}
.app-header p { font-size: 0.85rem; color: var(--muted); margin: 2px 0 0 0; }

/* ── Text input ── */
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
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.78rem !important; }

/* ── Alerts ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: var(--radius) !important;
    font-size: 0.9rem !important;
}

/* ── Misc ── */
hr { border-color: var(--border) !important; margin: 24px 0 !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
h2, h3 { color: var(--text) !important; letter-spacing: -0.01em; }
.stCaption, caption { color: var(--muted) !important; font-size: 0.78rem !important; }

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
.news-link:hover { color: var(--accent) !important; border-color: var(--accent) !important; }
.stock-title-row {
    display: flex;
    align-items: baseline;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.chart-legend {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 4px 2px 8px 2px;
    flex-wrap: wrap;
}
.chart-legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    color: var(--text);
    font-weight: 600;
}
.chart-legend-meta {
    color: var(--muted);
    font-size: 0.78rem;
    font-family: var(--mono);
}
.chart-line-swatch {
    display: inline-block;
    width: 28px;
    height: 2px;
    background: var(--accent);
    border-radius: 2px;
}
.chart-line-swatch-dash {
    background: transparent;
    border-top: 2px dashed var(--yellow);
}
.chart-line-swatch-dot {
    background: transparent;
    border-top: 2px dotted var(--purple);
}
[data-testid="stSegmentedControl"] {
    margin: 8px 0 18px 0;
}
[data-testid="stSegmentedControl"] div[role="radiogroup"] {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
}
[data-testid="stSegmentedControl"] button {
    min-width: 62px;
    min-height: 46px;
    border-radius: 999px !important;
    border: 1.5px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}
[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    border-color: var(--text) !important;
    background: var(--surface2) !important;
    color: var(--text) !important;
}
.news-item {
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.88rem;
    line-height: 1.45;
}
.news-keywords {
    font-size: 0.72rem;
    color: var(--muted);
}
.news-meta {
    margin-top: 4px;
    font-size: 0.72rem;
    color: var(--muted);
}

/* ── Top actions and dialogs ── */
.top-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    align-items: center;
}
/* Ensure top action columns' inner content stretches and aligns */
.top-actions [data-testid="column"] {
    display: flex !important;
    align-items: center !important;
    gap: 6px;
}
/* Make header action buttons fill their column and match widths */
.top-actions .stButton > button,
.top-actions .stLinkButton > a,
.top-actions .stSelectbox > div > div {
    width: 100% !important;
}
.list-row-title {
    color: var(--text);
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.35;
}
.list-row-meta {
    color: var(--muted);
    font-family: var(--mono);
    font-size: 0.76rem;
    margin-top: 2px;
}
.notification-message {
    color: var(--text);
    font-size: 0.86rem;
    margin-top: 6px;
    line-height: 1.45;
}
.list-row-divider {
    height: 1px;
    background: var(--border);
    margin: 12px 0;
}
.login-section {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin: 0 0 20px 0;
    background: var(--surface);
}
.login-link {
    display: block;
    color: var(--accent) !important;
    text-decoration: none !important;
    border: 1px solid rgba(56,189,248,0.28);
    border-radius: 8px;
    padding: 12px 14px;
    background: rgba(56,189,248,0.08);
    line-height: 1.4;
}
.login-link:hover {
    border-color: var(--accent);
    background: rgba(56,189,248,0.13);
}
.compact-login-link {
    font-size: 0.84rem;
    padding: 10px 12px;
}
div[data-testid="stPopover"] {
    z-index: 9999;
    min-width: 0;
}
div[data-testid="stPopover"] button {
    min-width: 104px;
    white-space: normal;
}
/* Make popover trigger fill its column when used inside header/actions */
div[data-testid="stPopover"] > button {
    width: 100% !important;
}
div[data-testid="stPopoverBody"],
div[data-testid="stPopoverContent"] {
    min-width: min(320px, calc(100vw - 36px)) !important;
    max-width: min(360px, calc(100vw - 36px)) !important;
    padding: 16px !important;
}
div[data-testid="stPopoverBody"] div[data-testid="stNumberInput"],
div[data-testid="stPopoverBody"] div[data-testid="stSelectbox"],
div[data-testid="stPopoverContent"] div[data-testid="stNumberInput"],
div[data-testid="stPopoverContent"] div[data-testid="stSelectbox"] {
    width: 100% !important;
    min-width: 0 !important;
}
div[data-testid="stPopoverBody"] input,
div[data-testid="stPopoverContent"] input {
    min-width: 0 !important;
}
div[data-testid="stPopover"] + div button,
div[data-testid="stPopover"] button,
.stButton > button {
    min-height: 48px;
    align-items: center;
}
div[data-testid="stSelectbox"] {
    min-width: 120px;
}
div[data-testid="stDialog"] div[role="dialog"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    max-width: min(860px, calc(100vw - 32px)) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ── Light mode ── */
@media (prefers-color-scheme: light) {
    :root {
        --bg: #f8fafc; --surface: #ffffff; --surface2: #f1f5f9;
        --border: #e2e8f0; --text: #0f172a; --muted: #64748b;
    }
}
[data-theme="light"] {
    --bg: #f8fafc !important; --surface: #ffffff !important;
    --surface2: #f1f5f9 !important; --border: #e2e8f0 !important;
    --text: #0f172a !important; --muted: #64748b !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div,
div[data-baseweb="select"] * {
    color: var(--text) !important;
    background: var(--surface) !important;
    border-color: var(--border) !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--muted) !important;
    opacity: 1 !important;
}

/* ── Responsive ── */
@media (max-width: 640px) {
    .metric-row [data-testid="column"] { min-width: 100% !important; }
    .block-container { padding: 1rem 0.75rem !important; }
    .app-header {
        border-bottom: none;
        margin-bottom: 8px;
        padding-bottom: 4px;
    }
    .app-header p { display: none; }
    div[data-testid="column"] {
        min-width: 100% !important;
    }
    .stock-title-row {
        margin-bottom: 6px;
    }
    .chart-legend {
        gap: 10px;
    }
    [data-testid="stSegmentedControl"] div[role="radiogroup"] {
        justify-content: flex-start;
        flex-wrap: nowrap;
        overflow-x: auto;
        padding: 2px 0 8px 0;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
    }
    [data-testid="stSegmentedControl"] div[role="radiogroup"]::-webkit-scrollbar {
        display: none;
    }
    [data-testid="stSegmentedControl"] button {
        min-width: 58px;
        min-height: 44px;
        flex: 0 0 auto;
    }
    div[data-testid="stDialog"] div[role="dialog"] {
        width: 100vw !important;
        max-width: 100vw !important;
        height: 100vh !important;
        max-height: 100vh !important;
        border-radius: 0 !important;
        margin: 0 !important;
    }
}
</style>
""", unsafe_allow_html=True)
