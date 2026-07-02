
"""
styles.py
Enterprise CSS for the Jubilant FoodWorks Limited
Enterprise Sustainability Analytics Dashboard.

Design direction: modern, minimal, premium — inspired by Microsoft Power BI.
Large KPI cards, rounded corners, soft shadows, gradient header, sticky top
navigation, and subtle hover-lift micro-interactions.

Contains ONLY CSS (as a Python string). No Streamlit calls, no HTML markup.
Colors and design tokens are sourced from config.py so the whole dashboard
stays visually consistent from a single source of truth.
"""

from __future__ import annotations

import config


def load_css() -> str:
    """Return the complete enterprise CSS stylesheet as a raw string."""
    theme = config.THEME

    return f"""
/* =====================================================================
   DESIGN TOKENS
   ===================================================================== */
:root {{
    --primary: {theme.PRIMARY_COLOR};
    --secondary: {theme.SECONDARY_COLOR};
    --success: {theme.SUCCESS_COLOR};
    --warning: {theme.WARNING_COLOR};
    --danger: {theme.DANGER_COLOR};
    --background: {theme.BACKGROUND_COLOR};
    --card: {theme.CARD_COLOR};
    --text: {theme.TEXT_COLOR};
    --sidebar: {theme.SIDEBAR_COLOR};
    --radius: {theme.BORDER_RADIUS};
    --shadow: {theme.CARD_SHADOW};
    --shadow-hover: 0 12px 28px rgba(15, 23, 42, 0.16);
    --font-family: "Segoe UI", "Segoe UI Semibold", -apple-system,
        BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    --transition-fast: 180ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-medium: 320ms cubic-bezier(0.4, 0, 0.2, 1);
}}

/* =====================================================================
   ENTIRE PAGE
   ===================================================================== */
html, body, [data-testid="stAppViewContainer"] {{
    background: var(--background) !important;
    color: var(--text);
    font-family: var(--font-family);
    font-size: 16px;
    line-height: 1.55;
    letter-spacing: 0.1px;
}}

[data-testid="stAppViewContainer"] > .main {{
    padding: 0 2.5rem 3rem 2.5rem;
}}

.block-container {{
    max-width: 100% !important;
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
}}

* {{
    box-sizing: border-box;
}}

::selection {{
    background: var(--primary);
    color: #ffffff;
}}

::-webkit-scrollbar {{
    width: 10px;
    height: 10px;
}}

::-webkit-scrollbar-track {{
    background: transparent;
}}

::-webkit-scrollbar-thumb {{
    background: rgba(15, 23, 42, 0.18);
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: rgba(15, 23, 42, 0.32);
}}

/* =====================================================================
   STICKY GRADIENT HEADER / TOP NAVIGATION
   ===================================================================== */
[data-testid="stHeader"] {{
    position: sticky;
    top: 0;
    z-index: 999;
    height: auto;
    background: linear-gradient(120deg, var(--secondary) 0%, var(--primary) 100%);
    box-shadow: 0 4px 18px rgba(15, 23, 42, 0.22);
    backdrop-filter: blur(6px);
}}

.enterprise-header {{
    position: sticky;
    top: 0;
    z-index: 998;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem 2.5rem;
    margin: 0 -2.5rem 1.75rem -2.5rem;
    background: linear-gradient(120deg, var(--secondary) 0%, var(--primary) 100%);
    color: #ffffff;
    border-radius: 0 0 var(--radius) var(--radius);
    box-shadow: var(--shadow);
}}

.enterprise-header h1 {{
    color: #ffffff !important;
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.2px;
}}

.enterprise-header p {{
    color: rgba(255, 255, 255, 0.82) !important;
    font-size: 0.95rem;
    margin: 0.2rem 0 0 0;
}}

/* =====================================================================
   HEADINGS / SUBHEADER
   ===================================================================== */
h1, h2, h3, h4, h5, h6 {{
    color: var(--text) !important;
    font-family: var(--font-family);
    font-weight: 700;
    letter-spacing: 0.1px;
}}

h1 {{
    font-size: 2.1rem;
    margin-bottom: 0.4rem;
}}

h2 {{
    font-size: 1.5rem;
    margin-top: 1.6rem;
    margin-bottom: 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid rgba(15, 23, 42, 0.08);
}}

h3 {{
    font-size: 1.15rem;
    color: var(--secondary) !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
    margin-top: 1.2rem;
}}

/* =====================================================================
   SIDEBAR
   ===================================================================== */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, var(--sidebar) 0%, #16213a 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}}

[data-testid="stSidebar"] * {{
    color: rgba(255, 255, 255, 0.92) !important;
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
    color: #ffffff !important;
    border-bottom: none;
}}

[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSelectbox label {{
    font-weight: 500;
    opacity: 0.9;
}}

[data-testid="stSidebar"] hr {{
    border-color: rgba(255, 255, 255, 0.12);
}}

/* =====================================================================
   KPI CARDS / METRIC CARDS
   ===================================================================== */
.kpi-card,
[data-testid="stMetric"] {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 1.6rem 1.75rem;
    box-shadow: var(--shadow);
    border: 1px solid rgba(15, 23, 42, 0.05);
    transition: transform var(--transition-fast), box-shadow var(--transition-fast);
    position: relative;
    overflow: hidden;
}}

.kpi-card::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 5px;
    height: 100%;
    background: var(--primary);
    opacity: 0.9;
}}

.kpi-card:hover,
[data-testid="stMetric"]:hover {{
    transform: translateY(-5px);
    box-shadow: var(--shadow-hover);
    border-color: rgba(11, 95, 255, 0.25);
}}

[data-testid="stMetricLabel"] {{
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: rgba(30, 41, 59, 0.62) !important;
}}

[data-testid="stMetricValue"] {{
    font-size: 2.1rem;
    font-weight: 700;
    color: var(--text) !important;
}}

[data-testid="stMetricDelta"] svg {{
    vertical-align: middle;
}}

.kpi-card .kpi-title {{
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: rgba(30, 41, 59, 0.62);
    margin-bottom: 0.5rem;
}}

.kpi-card .kpi-value {{
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.15;
}}

.kpi-card .kpi-unit {{
    font-size: 0.95rem;
    font-weight: 500;
    color: rgba(30, 41, 59, 0.5);
    margin-left: 0.35rem;
}}

.kpi-card .kpi-delta-positive {{
    color: var(--success);
    font-weight: 600;
    font-size: 0.9rem;
}}

.kpi-card .kpi-delta-negative {{
    color: var(--danger);
    font-weight: 600;
    font-size: 0.9rem;
}}

/* =====================================================================
   CHART CONTAINERS
   ===================================================================== */
.chart-container,
[data-testid="stPlotlyChart"] {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 1.25rem 1.25rem 0.5rem 1.25rem;
    box-shadow: var(--shadow);
    border: 1px solid rgba(15, 23, 42, 0.05);
    transition: box-shadow var(--transition-fast), transform var(--transition-fast);
    margin-bottom: 1.5rem;
}}

.chart-container:hover,
[data-testid="stPlotlyChart"]:hover {{
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
}}

/* =====================================================================
   TABLES
   ===================================================================== */
[data-testid="stDataFrame"],
[data-testid="stTable"] {{
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow);
    border: 1px solid rgba(15, 23, 42, 0.06);
}}

[data-testid="stDataFrame"] thead tr th {{
    background: var(--secondary) !important;
    color: #ffffff !important;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.78rem;
    letter-spacing: 0.5px;
}}

[data-testid="stDataFrame"] tbody tr:hover {{
    background: rgba(11, 95, 255, 0.06) !important;
}}

/* =====================================================================
   EXPANDERS
   ===================================================================== */
[data-testid="stExpander"] {{
    background: var(--card);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    border: 1px solid rgba(15, 23, 42, 0.06);
    overflow: hidden;
    margin-bottom: 1rem;
    transition: box-shadow var(--transition-fast);
}}

[data-testid="stExpander"]:hover {{
    box-shadow: var(--shadow-hover);
}}

[data-testid="stExpander"] summary {{
    font-weight: 600;
    color: var(--text);
    padding: 0.9rem 1.2rem;
}}

/* =====================================================================
   BUTTONS
   ===================================================================== */
.stButton > button,
.stDownloadButton > button {{
    background: linear-gradient(120deg, var(--primary) 0%, var(--secondary) 100%);
    color: #ffffff;
    border: none;
    border-radius: var(--radius);
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.2px;
    box-shadow: 0 4px 12px rgba(11, 95, 255, 0.25);
    transition: transform var(--transition-fast), box-shadow var(--transition-fast), opacity var(--transition-fast);
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(11, 95, 255, 0.35);
    opacity: 0.96;
}}

.stButton > button:active,
.stDownloadButton > button:active {{
    transform: translateY(0);
}}

/* =====================================================================
   TABS
   ===================================================================== */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    gap: 0.5rem;
    border-bottom: 2px solid rgba(15, 23, 42, 0.08);
}}

[data-testid="stTabs"] [data-baseweb="tab"] {{
    height: 3rem;
    border-radius: var(--radius) var(--radius) 0 0;
    font-weight: 600;
    color: rgba(30, 41, 59, 0.55);
    transition: color var(--transition-fast), background var(--transition-fast);
}}

[data-testid="stTabs"] [data-baseweb="tab"]:hover {{
    color: var(--primary);
    background: rgba(11, 95, 255, 0.06);
}}

[data-testid="stTabs"] [aria-selected="true"] {{
    color: var(--primary) !important;
    border-bottom: 3px solid var(--primary) !important;
}}

/* =====================================================================
   SELECTBOXES / INPUTS
   ===================================================================== */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
    background: var(--card);
    border-radius: var(--radius);
    border: 1px solid rgba(15, 23, 42, 0.14);
    box-shadow: none;
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover {{
    border-color: var(--primary);
}}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within {{
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(11, 95, 255, 0.15);
}}

/* =====================================================================
   FOOTER
   ===================================================================== */
.enterprise-footer {{
    margin: 3rem -2.5rem 0 -2.5rem;
    padding: 1.5rem 2.5rem;
    background: var(--secondary);
    color: rgba(255, 255, 255, 0.75);
    font-size: 0.85rem;
    text-align: center;
    border-radius: var(--radius) var(--radius) 0 0;
}}

.enterprise-footer a {{
    color: #ffffff;
    text-decoration: none;
    font-weight: 600;
}}

.enterprise-footer a:hover {{
    text-decoration: underline;
}}

/* =====================================================================
   RESPONSIVE LAYOUT
   ===================================================================== */
@media (max-width: 1200px) {{
    [data-testid="stAppViewContainer"] > .main {{
        padding: 0 1.25rem 2rem 1.25rem;
    }}

    .enterprise-header,
    .enterprise-footer {{
        margin-left: -1.25rem;
        margin-right: -1.25rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
    }}
}}

@media (max-width: 768px) {{
    .enterprise-header h1 {{
        font-size: 1.4rem;
    }}

    [data-testid="stMetricValue"],
    .kpi-card .kpi-value {{
        font-size: 1.6rem;
    }}

    h2 {{
        font-size: 1.2rem;
    }}
}}

/* =====================================================================
   REDUCED MOTION
   ===================================================================== */
@media (prefers-reduced-motion: reduce) {{
    * {{
        transition: none !important;
        animation: none !important;
    }}
}}
"""
