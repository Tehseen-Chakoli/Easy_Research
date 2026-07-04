"""Centralized CSS for the Easy Answer Streamlit interface."""

APP_STYLES = """
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(124, 58, 237, 0.12), transparent 28%),
            radial-gradient(circle at top right, rgba(14, 165, 233, 0.10), transparent 24%),
            linear-gradient(180deg, #0b0f14 0%, #0f141c 100%);
        color: #e5e7eb;
    }

    .hero-shell {
        background: linear-gradient(180deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.92));
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 22px;
        padding: 24px 26px;
        margin-bottom: 14px;
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.32);
    }

    .hero-kicker {
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 10px;
    }

    .hero-title {
        font-size: 32px;
        font-weight: 800;
        line-height: 1.1;
        color: #f8fafc;
        margin-bottom: 10px;
    }

    .hero-copy {
        color: #cbd5e1;
        font-size: 15px;
        line-height: 1.6;
        max-width: 920px;
    }

    .hero-db {
        color: #e2e8f0;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .section-label {
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 11px;
        font-weight: 700;
        color: #94a3b8;
        margin: 18px 0 8px 2px;
    }

    .question {
        font-weight: 700;
        font-size: 16px;
        margin-bottom: 8px;
        color: #f8fafc;
    }

    .time {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 10px;
    }

    .chat-card-header {
        margin-bottom: 12px;
    }

    .stMarkdown pre {
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.12);
    }

    .stMarkdown code {
        font-size: 0.95rem;
    }

    .panel-heading {
        color: #f8fafc;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .panel-subheading {
        color: #94a3b8;
        font-size: 13px;
        margin-bottom: 16px;
    }

    section[data-testid="stSidebar"] {
        background: #0a0d12;
        border-right: 1px solid rgba(148, 163, 184, 0.10);
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #e5e7eb !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 10px;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(17, 24, 39, 0.95), rgba(15, 23, 42, 0.92));
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div,
    div[data-testid="stMetric"] span {
        color: #e5e7eb !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, rgba(17, 24, 39, 0.94), rgba(15, 23, 42, 0.92));
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 22px;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.24);
    }

    [data-testid="stAppViewContainer"] input,
    [data-testid="stAppViewContainer"] textarea,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: rgba(15, 23, 42, 0.95) !important;
        color: #f8fafc !important;
        border-color: rgba(148, 163, 184, 0.20) !important;
    }

    [data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.95) !important;
        color: #f8fafc !important;
        border-color: rgba(148, 163, 184, 0.20) !important;
    }

    [data-testid="stAppViewContainer"] .stButton button,
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stAppViewContainer"] .stDownloadButton button {
        background: linear-gradient(180deg, #1f2937, #111827);
        color: #f8fafc !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
    }

    [data-testid="stAppViewContainer"] .stButton button:hover,
    [data-testid="stSidebar"] .stButton button:hover,
    [data-testid="stAppViewContainer"] .stDownloadButton button:hover {
        border-color: rgba(124, 58, 237, 0.52) !important;
        transform: translateY(-1px);
    }

    [data-testid="stAlert"] {
        border-radius: 16px;
    }
</style>
"""
