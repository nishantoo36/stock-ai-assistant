import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0a0e1a;
            --surface: #111827;
            --surface2: #1a2235;
            --border: #1f2d45;
            --text: #e2e8f0;
            --muted: #64748b;
            --accent: #38bdf8;
            --green: #22c55e;
            --red: #ef4444;
            --yellow: #f59e0b;
            --purple: #a78bfa;
            --mono: "DM Mono", monospace;
        }

        @media (prefers-color-scheme: light) {
            :root {
                --bg: #f8fafc;
                --surface: #ffffff;
                --surface2: #eef2f7;
                --border: #d7dee9;
                --text: #0f172a;
                --muted: #475569;
                --accent: #64748b;
            }
        }

        [data-theme="light"] {
            --bg: #f8fafc !important;
            --surface: #ffffff !important;
            --surface2: #eef2f7 !important;
            --border: #d7dee9 !important;
            --text: #0f172a !important;
            --muted: #475569 !important;
            --accent: #64748b !important;
        }

        [data-theme="light"] html,
        [data-theme="light"] body,
        [data-theme="light"] .stApp,
        [data-theme="light"] .main {
            color-scheme: light !important;
        }

        html, body, [class*="css"] {
            background-color: var(--bg) !important;
            color: var(--text) !important;
        }

        .app-header {
            display: flex;
            align-items: center;
            gap: 14px;
            margin: 0 0 18px 0;
            padding: 0 0 14px 0;
        }

        .app-header-icon {
            font-size: 2.6rem;
            line-height: 1;
            flex: 0 0 auto;
        }

        .app-header h1 {
            margin: 0;
            padding: 0;
            font-size: 2rem;
            line-height: 1.05;
            font-weight: 700;
            color: var(--text) !important;
            letter-spacing: 0;
        }

        .app-header p {
            margin: 4px 0 0 0;
            color: var(--muted) !important;
            font-size: 0.9rem;
            line-height: 1.35;
        }

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {
            background: var(--surface) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: var(--muted) !important;
            opacity: 1 !important;
        }

        .stSelectbox div[data-baseweb="select"] * {
            color: var(--text) !important;
        }

        .stock-card {
            background: #0B1428;
            padding: 18px;
            border-radius: 14px;
            border: 1px solid #1B2B4A;
            margin-bottom: 12px;
            color: white;
        }

        [data-testid="metric-container"] {
            background: #0B1428;
            border: 1px solid #1B2B4A;
            padding: 18px;
            border-radius: 14px;
        }

        .stock-card,
        .ai-pick-link,
        .result-card-link {
            display: block;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text) !important;
        }

        div[data-testid="stButton"] button,
        button[kind="secondary"],
        button[kind="primary"],
        button[kind="tertiary"] {
            background-color: var(--surface) !important;
            background-image: none !important;
            color: var(--text) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            border: 1px solid var(--border) !important;
            width: 100%;
            min-height: 38px !important;
            padding: 5px 10px !important;
            white-space: pre-line;
            line-height: 1.03;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            font-size: 0.8rem;
            box-shadow: none !important;
            -webkit-appearance: none !important;
            appearance: none !important;
        }

        div[data-testid="stButton"] button:hover,
        button[kind="secondary"]:hover,
        button[kind="primary"]:hover,
        button[kind="tertiary"]:hover {
            background-color: var(--surface2) !important;
            border-color: var(--accent) !important;
            color: var(--text) !important;
        }

        div[data-testid="stButton"] button:disabled,
        button[kind="secondary"]:disabled,
        button[kind="primary"]:disabled,
        button[kind="tertiary"]:disabled {
            opacity: 0.72;
        }

        div[data-testid="stButton"] button p,
        button[kind="secondary"] p,
        button[kind="primary"] p,
        button[kind="tertiary"] p {
            margin: 0 !important;
            color: inherit !important;
        }

        .google-auth-link,
        .stLinkButton > a {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            min-height: 48px;
            padding: 0 16px;
            background: var(--surface) !important;
            color: var(--text) !important;
            border-radius: 10px;
            text-decoration: none !important;
            font-weight: 600;
            border: 1px solid var(--border) !important;
            box-sizing: border-box;
        }

        .google-auth-link:hover,
        .stLinkButton > a:hover {
            background: var(--surface2) !important;
            border-color: var(--accent) !important;
            color: var(--text) !important;
        }

        .google-auth-link span,
        .google-auth-link *,
        .stLinkButton > a span,
        .stLinkButton > a * {
            color: inherit !important;
        }

        .google-auth-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.05rem;
            line-height: 1;
        }

        @media (max-width: 640px) {
            .app-header {
                gap: 10px;
                margin-bottom: 14px;
            }

            .app-header-icon {
                font-size: 2.2rem;
            }

            .app-header h1 {
                font-size: 1.55rem;
            }
        }

        .stExpanderHeader,
        .streamlit-expanderHeader {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            color: var(--text) !important;
        }

        .streamlit-expanderContent {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-top: none !important;
            border-radius: 0 0 8px 8px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
