"""
config.py

Static configuration for the
Jubilant FoodWorks Limited
Enterprise Sustainability Analytics Dashboard.

This module contains ONLY configuration values.
No business logic.
No Streamlit code.
No parsing.
No KPI calculations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Final


# ==========================================================
# COMPANY INFORMATION
# ==========================================================

COMPANY_NAME: Final[str] = "Jubilant FoodWorks Limited"
COMPANY_SHORT_NAME: Final[str] = "JFL"

DASHBOARD_TITLE: Final[str] = "Enterprise Sustainability Analytics Dashboard"
DASHBOARD_SUBTITLE: Final[str] = "Health, Safety & Environment KPI Dashboard"

CURRENT_YEAR: Final[int] = 2026

DEFAULT_PAGE: Final[str] = "Executive Overview"
DEFAULT_THEME: Final[str] = "light"


# ==========================================================
# GITHUB CONFIGURATION
# ==========================================================

GITHUB_OWNER: Final[str] = "AayuGo1"
GITHUB_REPO: Final[str] = "alternate"
GITHUB_BRANCH: Final[str] = "main"

EXCEL_FILENAME: Final[str] = "Monthly KPI Summary Sheet_April_GNSC.xlsx"

RAW_GITHUB_URL: Final[str] = (
    f"https://raw.githubusercontent.com/"
    f"{GITHUB_OWNER}/"
    f"{GITHUB_REPO}/"
    f"{GITHUB_BRANCH}/"
    f"{EXCEL_FILENAME}"
)

RAW_CACHE_TTL_SECONDS: Final[int] = 300


# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================

PAGES: Final[list[str]] = [
    "Executive Overview",
    "Energy",
    "Water",
    "Waste",
]


# ==========================================================
# THEME
# ==========================================================

@dataclass(frozen=True)
class ThemeConfig:
    PRIMARY_COLOR: str = "#0B5FFF"
    SECONDARY_COLOR: str = "#1E293B"

    SUCCESS_COLOR: str = "#16A34A"
    WARNING_COLOR: str = "#F59E0B"
    DANGER_COLOR: str = "#DC2626"

    BACKGROUND_COLOR: str = "#F5F7FA"
    CARD_COLOR: str = "#FFFFFF"

    TEXT_COLOR: str = "#1E293B"
    SIDEBAR_COLOR: str = "#0F172A"

    BORDER_RADIUS: str = "14px"
    CARD_SHADOW: str = "0 6px 16px rgba(15,23,42,0.08)"

    CARD_HEIGHT: int = 145
    CARD_PADDING: int = 20
    CARD_ICON_SIZE: int = 32

    SIDEBAR_WIDTH: int = 260

    CONTENT_MAX_WIDTH = None


THEME: Final = ThemeConfig()


# ==========================================================
# CHART CONFIGURATION
# ==========================================================

DEFAULT_CHART_HEIGHT: Final[int] = 420
DEFAULT_TABLE_HEIGHT: Final[int] = 380

PLOT_TEMPLATE: Final[str] = "plotly_white"

FONT_FAMILY: Final[str] = "Inter"

CHART_COLORS: Final[list[str]] = [
    "#0B5FFF",
    "#16A34A",
    "#F59E0B",
    "#DC2626",
    "#8B5CF6",
    "#14B8A6",
    "#2563EB",
    "#10B981",
]


# ==========================================================
# KPI CARD LAYOUT
# ==========================================================

KPI_COLUMNS: Final[int] = 4


# ==========================================================
# STREAMLIT
# ==========================================================

@dataclass(frozen=True)
class StreamlitConfig:
    PAGE_TITLE: str = "JFL Sustainability Dashboard"

    PAGE_ICON: str = "🌱"

    LAYOUT: str = "wide"

    INITIAL_SIDEBAR_STATE: str = "expanded"


STREAMLIT_CONFIG: Final = StreamlitConfig()


# ==========================================================
# MONTH ORDER
# ==========================================================

MONTH_ORDER: Final[list[str]] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


# ==========================================================
# FORMATTING
# ==========================================================

DATE_FORMAT: Final[str] = "%d-%b-%Y"

NUMBER_PRECISION: Final[int] = 2

THOUSANDS_SEPARATOR: Final[str] = ","


# ==========================================================
# DEFAULT UNITS
# (Fallback only. Actual units come from Excel Row 3.)
# ==========================================================

DEFAULT_UNITS: Final[dict[str, str]] = {
    "default": ""
}


# ==========================================================
# ICONS
# ==========================================================

ICONS: Final[dict[str, str]] = {
    "Executive": "🏠",
    "Energy": "⚡",
    "Water": "💧",
    "Waste": "♻",
    "Production": "🏭",
    "Safety": "🦺",
    "Target": "🎯",
    "Alert": "🚨",
}


# ==========================================================
# CACHE
# ==========================================================

ENABLE_CACHE: Final[bool] = True

CACHE_TTL_SECONDS: Final[int] = 300


# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL: Final[str] = "INFO"


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR: Final[Path] = Path(__file__).resolve().parent
