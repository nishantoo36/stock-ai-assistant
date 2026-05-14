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
    padding: 0 0 24px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
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
}
</style>
""", unsafe_allow_html=True)
