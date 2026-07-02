"""
styles.py
Enterprise-grade visual theme for the Sustainability Analytics Dashboard.
Pure presentation only — no data, no business logic.
"""


def load_css() -> str:
    return """
/* ============================================================
   DESIGN TOKENS
   ============================================================ */
:root {
    --jfw-navy:        #0B2545;
    --jfw-blue-deep:   #0E4B8C;
    --jfw-blue:        #1565D8;
    --jfw-blue-light:  #4C9AFF;
    --jfw-green-deep:  #0F7A5C;
    --jfw-green:       #16A876;
    --jfw-green-light: #4FD1A5;
    --jfw-bg:          #F4F7FB;
    --jfw-surface:     #FFFFFF;
    --jfw-border:      rgba(15, 35, 64, 0.08);
    --jfw-text:        #14213D;
    --jfw-text-muted:  rgba(20, 33, 61, 0.58);
    --jfw-positive:    #0F9D6B;
    --jfw-negative:    #E14F4F;
    --jfw-radius-lg:   18px;
    --jfw-radius-md:   14px;
    --jfw-radius-sm:   10px;
    --jfw-shadow-sm:   0 1px 3px rgba(15, 35, 64, 0.06), 0 1px 2px rgba(15, 35, 64, 0.04);
    --jfw-shadow-md:   0 6px 20px rgba(15, 35, 64, 0.08), 0 2px 6px rgba(15, 35, 64, 0.04);
    --jfw-shadow-lg:   0 16px 40px rgba(15, 35, 64, 0.14), 0 4px 12px rgba(15, 35, 64, 0.06);
    --jfw-font: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ============================================================
   GLOBAL / LAYOUT
   ============================================================ */
html, body, [class*="css"] {
    font-family: var(--jfw-font) !important;
    color: var(--jfw-text);
}

.stApp {
    background: linear-gradient(180deg, #EEF3FA 0%, #F4F7FB 220px, #F4F7FB 100%);
}

.block-container {
    padding-top: 1.4rem !important;
    padding-bottom: 3rem !important;
    max-width: 1600px !important;
}

h1, h2, h3, h4, h5 {
    font-family: var(--jfw-font) !important;
    color: var(--jfw-navy) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}

h2 { margin-top: 2.2rem !important; margin-bottom: 1rem !important; font-size: 1.35rem !important; }
h3 { font-size: 1.12rem !important; }
h4, h5 { color: var(--jfw-blue-deep) !important; }

hr {
    border: none !important;
    border-top: 1px solid var(--jfw-border) !important;
    margin: 1.8rem 0 !important;
}

/* Scrollbar polish */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(15, 35, 64, 0.18);
    border-radius: 20px;
    border: 2px solid transparent;
    background-clip: content-box;
}
::-webkit-scrollbar-thumb:hover { background: rgba(15, 35, 64, 0.3); background-clip: content-box; }

/* ============================================================
   HEADER
   ============================================================ */
.enterprise-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    background: linear-gradient(120deg, var(--jfw-navy) 0%, var(--jfw-blue-deep) 55%, var(--jfw-green-deep) 130%);
    color: #fff;
    padding: 1.6rem 2.2rem;
    border-radius: var(--jfw-radius-lg);
    box-shadow: var(--jfw-shadow-lg);
    margin-bottom: 1.8rem;
    position: relative;
    overflow: hidden;
}

.enterprise-header::after {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 85% -10%, rgba(79, 209, 165, 0.35), transparent 55%),
        radial-gradient(circle at 10% 120%, rgba(76, 154, 255, 0.25), transparent 50%);
    pointer-events: none;
}

.enterprise-header h1 {
    color: #fff !important;
    font-size: 1.55rem !important;
    font-weight: 800 !important;
    margin: 0 !important;
    letter-spacing: -0.02em;
}

.enterprise-header p {
    color: rgba(255, 255, 255, 0.82) !important;
    margin: 0.15rem 0 !important;
    font-size: 0.88rem;
}

.enterprise-header strong { color: #fff; font-weight: 700; }

/* ============================================================
   SIDEBAR
   ============================================================ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--jfw-navy) 0%, #0F3260 100%) !important;
    border-right: none !important;
}

section[data-testid="stSidebar"] * {
    color: rgba(255, 255, 255, 0.92) !important;
}

section[data-testid="stSidebar"] h2 {
    color: #fff !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em;
}

section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {
    color: rgba(255, 255, 255, 0.55) !important;
}

section[data-testid="stSidebar"] hr {
    border-top: 1px solid rgba(255, 255, 255, 0.12) !important;
    margin: 1.1rem 0 !important;
}

/* Sidebar radio nav -> pill-style menu */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 0.35rem;
    display: flex;
    flex-direction: column;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding: 0.62rem 0.9rem;
    border-radius: var(--jfw-radius-sm);
    transition: background 0.18s ease, transform 0.18s ease;
    cursor: pointer;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateX(2px);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(76, 154, 255, 0.25), rgba(79, 209, 165, 0.18));
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.15);
}

section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    background: linear-gradient(120deg, var(--jfw-blue) 0%, var(--jfw-green) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--jfw-radius-sm) !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    box-shadow: var(--jfw-shadow-sm);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

section[data-testid="stSidebar"] .stButton button:hover {
    transform: translateY(-1px);
    box-shadow: var(--jfw-shadow-md);
}

/* ============================================================
   KPI CARDS
   ============================================================ */
.kpi-card {
    background: linear-gradient(160deg, #FFFFFF 0%, #F7FAFF 100%);
    border: 1px solid var(--jfw-border);
    border-radius: var(--jfw-radius-md);
    padding: 1.15rem 1.3rem;
    box-shadow: var(--jfw-shadow-sm);
    height: 100%;
    min-height: 128px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s cubic-bezier(0.2, 0.8, 0.2, 1),
                box-shadow 0.2s cubic-bezier(0.2, 0.8, 0.2, 1),
                border-color 0.2s ease;
    animation: jfw-card-in 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.kpi-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3.5px;
    background: linear-gradient(90deg, var(--jfw-blue) 0%, var(--jfw-green) 100%);
    opacity: 0.85;
}

.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--jfw-shadow-lg);
    border-color: rgba(21, 101, 216, 0.25);
}

.kpi-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--jfw-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.5rem;
}

.kpi-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--jfw-navy);
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
    animation: jfw-count-pop 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.kpi-unit {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--jfw-text-muted);
    margin-left: 0.3rem;
}

.kpi-delta-positive {
    color: var(--jfw-positive);
    background: rgba(15, 157, 107, 0.1);
    padding: 0.16rem 0.55rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
}

.kpi-delta-negative {
    color: var(--jfw-negative);
    background: rgba(225, 79, 79, 0.1);
    padding: 0.16rem 0.55rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
}

@keyframes jfw-card-in {
    from { opacity: 0; transform: translateY(10px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes jfw-count-pop {
    0%   { opacity: 0; transform: scale(0.85); }
    60%  { opacity: 1; transform: scale(1.03); }
    100% { opacity: 1; transform: scale(1); }
}

/* ============================================================
   TABS / EXPANDERS / INPUTS
   ============================================================ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.3rem;
    background: var(--jfw-surface);
    padding: 0.35rem;
    border-radius: var(--jfw-radius-md);
    box-shadow: var(--jfw-shadow-sm);
    border: 1px solid var(--jfw-border);
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--jfw-radius-sm) !important;
    font-weight: 600 !important;
    color: var(--jfw-text-muted) !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.18s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(120deg, var(--jfw-blue) 0%, var(--jfw-green) 100%) !important;
    color: #fff !important;
    box-shadow: var(--jfw-shadow-sm);
}

.streamlit-expanderHeader {
    background: var(--jfw-surface) !important;
    border-radius: var(--jfw-radius-sm) !important;
    border: 1px solid var(--jfw-border) !important;
    font-weight: 600 !important;
    color: var(--jfw-navy) !important;
    box-shadow: var(--jfw-shadow-sm);
}

.streamlit-expanderContent {
    background: var(--jfw-surface) !important;
    border-radius: 0 0 var(--jfw-radius-sm) var(--jfw-radius-sm) !important;
    border: 1px solid var(--jfw-border) !important;
    border-top: none !important;
}

.stTextInput input {
    border-radius: var(--jfw-radius-sm) !important;
    border: 1px solid var(--jfw-border) !important;
    box-shadow: none !important;
}

.stTextInput input:focus {
    border-color: var(--jfw-blue) !important;
    box-shadow: 0 0 0 3px rgba(21, 101, 216, 0.12) !important;
}

/* Radio (page nav) input dots */
div[role="radiogroup"] label span:first-child {
    border-color: rgba(255, 255, 255, 0.5) !important;
}

/* ============================================================
   DATAFRAMES / TABLES
   ============================================================ */
[data-testid="stDataFrame"] {
    border-radius: var(--jfw-radius-sm) !important;
    overflow: hidden;
    border: 1px solid var(--jfw-border) !important;
    box-shadow: var(--jfw-shadow-sm);
}

/* ============================================================
   PLOTLY CONTAINERS
   ============================================================ */
[data-testid="stPlotlyChart"] {
    background: var(--jfw-surface);
    border-radius: var(--jfw-radius-md);
    padding: 0.9rem;
    border: 1px solid var(--jfw-border);
    box-shadow: var(--jfw-shadow-sm);
    transition: box-shadow 0.2s ease;
}

[data-testid="stPlotlyChart"]:hover {
    box-shadow: var(--jfw-shadow-md);
}

/* ============================================================
   ALERT / INFO / WARNING BOXES
   ============================================================ */
.stAlert {
    border-radius: var(--jfw-radius-sm) !important;
    box-shadow: var(--jfw-shadow-sm);
    border: 1px solid var(--jfw-border) !important;
}

/* ============================================================
   FOOTER
   ============================================================ */
.enterprise-footer {
    text-align: center;
    color: var(--jfw-text-muted);
    font-size: 0.8rem;
    padding: 1.6rem 0 0.6rem 0;
    margin-top: 2rem;
    border-top: 1px solid var(--jfw-border);
    letter-spacing: 0.01em;
}

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 900px) {
    .enterprise-header { flex-direction: column; align-items: flex-start; text-align: left; }
    .enterprise-header > div:last-child { text-align: left !important; }
    .kpi-value { font-size: 1.5rem; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
}
"""
