
"""
metrics.py
Reusable, dynamic KPI calculation functions operating on the long-format
DataFrame produced by parser.py.

No Category, Subcategory, or Metric names are hardcoded anywhere in this
module. All aggregation is derived dynamically from whatever categories,
subcategories, months, and units are actually present in the DataFrame.

This module contains NO Streamlit code, NO charts, and NO HTML/CSS.
"""

from __future__ import annotations

from typing import Any, Final

import pandas as pd

_MONTH_ABBR_ORDER: Final[dict[str, int]] = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def _parse_month_label(month_label: str) -> tuple[int, int] | None:
    """
    Parse a "Mon-YYYY" style month label (e.g. "Apr-2025") into a
    (year, month_number) sort key. Returns None if the label cannot
    be parsed.
    """
    if not isinstance(month_label, str) or "-" not in month_label:
        return None

    abbr, _, year_str = month_label.partition("-")
    month_num = _MONTH_ABBR_ORDER.get(abbr.strip().capitalize())
    if month_num is None:
        return None

    try:
        year = int(year_str.strip())
    except ValueError:
        return None

    return year, month_num


def _sorted_months_desc(df: pd.DataFrame) -> list[str]:
    """Return unique Month labels present in df, sorted most-recent first."""
    if df.empty or "Month" not in df.columns:
        return []

    unique_months = df["Month"].dropna().unique().tolist()
    parsed = [(month, _parse_month_label(month)) for month in unique_months]
    parsed = [(month, key) for month, key in parsed if key is not None]
    parsed.sort(key=lambda item: item[1], reverse=True)
    return [month for month, _ in parsed]


def get_latest_month(df: pd.DataFrame) -> str | None:
    """Return the most recent reporting Month label present in df."""
    months = _sorted_months_desc(df)
    return months[0] if months else None


def get_previous_month(df: pd.DataFrame) -> str | None:
    """Return the second-most-recent reporting Month label present in df."""
    months = _sorted_months_desc(df)
    return months[1] if len(months) >= 2 else None


def calculate_variance(actual: float | None, target: float | None) -> float | None:
    """
    Calculate percentage variance of actual against target:
    ((actual - target) / target) * 100.

    Returns None if either value is missing or target is zero.
    """
    if actual is None or target is None:
        return None
    if pd.isna(actual) or pd.isna(target):
        return None
    if target == 0:
        return None
    return ((actual - target) / target) * 100


def calculate_mom(current: float | None, previous: float | None) -> float | None:
    """
    Calculate month-over-month percentage change:
    ((current - previous) / previous) * 100.

    Returns None if either value is missing or previous is zero.
    """
    if current is None or previous is None:
        return None
    if pd.isna(current) or pd.isna(previous):
        return None
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def filter_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """Return rows of df matching the given Category value."""
    if df.empty or "Category" not in df.columns:
        return df.iloc[0:0]
    return df[df["Category"] == category]


def filter_subcategory(df: pd.DataFrame, subcategory: str) -> pd.DataFrame:
    """Return rows of df matching the given Subcategory value."""
    if df.empty or "Subcategory" not in df.columns:
        return df.iloc[0:0]
    return df[df["Subcategory"] == subcategory]


def get_available_categories(df: pd.DataFrame) -> list[str]:
    """Return unique Category values present in df, in first-seen order."""
    if df.empty or "Category" not in df.columns:
        return []
    return list(dict.fromkeys(str(c) for c in df["Category"].tolist() if pd.notna(c)))


def get_available_subcategories(df: pd.DataFrame) -> list[str]:
    """Return unique Subcategory values present in df, in first-seen order."""
    if df.empty or "Subcategory" not in df.columns:
        return []
    return list(dict.fromkeys(str(s) for s in df["Subcategory"].tolist() if pd.notna(s)))


def _sum_or_none(series: pd.Series) -> float | None:
    """
    Sum a series as numeric values, returning None if every value is
    missing or non-numeric. Non-numeric entries (e.g. "NA" placeholders
    stored in the workbook) are excluded from the sum rather than
    fabricated into a value.
    """
    if series.empty:
        return None
    numeric_series = pd.to_numeric(series, errors="coerce")
    total = numeric_series.sum(min_count=1)
    return None if pd.isna(total) else float(total)


def _most_common_unit(series: pd.Series) -> str | None:
    """Return the most frequently occurring non-null Unit in a series."""
    non_null = series.dropna()
    if non_null.empty:
        return None
    mode_values = non_null.mode()
    return str(mode_values.iloc[0]) if not mode_values.empty else None


def get_summary_cards(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    Build a KPI summary dictionary for every Category present in df.

    For each Category, returns:
        Current Value: sum of Value for the latest reporting Month
        Unit: most common Unit reported for that Category in the latest Month
        Target: sum of Target for the latest reporting Month
        Variance: percentage variance of Current Value against Target
        MoM %: percentage change of Current Value versus the previous Month

    Returns:
        dict keyed by Category name, e.g.:
        {
            "Energy": {
                "Current Value": ...,
                "Unit": ...,
                "Target": ...,
                "Variance": ...,
                "MoM %": ...,
            },
            ...
        }
    """
    summary: dict[str, dict[str, Any]] = {}

    if df.empty:
        return summary

    latest_month = get_latest_month(df)
    previous_month = get_previous_month(df)

    for category in get_available_categories(df):
        category_df = filter_category(df, category)

        latest_df = category_df[category_df["Month"] == latest_month] if latest_month else category_df.iloc[0:0]
        previous_df = (
            category_df[category_df["Month"] == previous_month] if previous_month else category_df.iloc[0:0]
        )

        current_value = _sum_or_none(latest_df["Value"])
        target_value = _sum_or_none(latest_df["Target"])
        previous_value = _sum_or_none(previous_df["Value"])
        unit = _most_common_unit(latest_df["Unit"])

        summary[category] = {
            "Current Value": current_value,
            "Unit": unit,
            "Target": target_value,
            "Variance": calculate_variance(current_value, target_value),
            "MoM %": calculate_mom(current_value, previous_value),
        }

    return summary
