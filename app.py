"""
app.py
Jubilant FoodWorks Limited — Enterprise Sustainability Analytics Dashboard.

This module contains ZERO business logic. It only:
    Load     -> excel_loader.py
    Parse    -> parser.py
    Calculate -> metrics.py
    Display  -> charts.py / styles.py / Streamlit

No KPI names, categories, subcategories, or values are hardcoded.
Everything shown on screen is driven by whatever is actually present in
the parsed DataFrame.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

import charts
import config
import excel_loader
import metrics
import parser
import styles


# ==========================================================
# PAGE CONFIG (must be first Streamlit call)
# ==========================================================

st.set_page_config(
    page_title=config.STREAMLIT_CONFIG.PAGE_TITLE,
    page_icon=config.STREAMLIT_CONFIG.PAGE_ICON,
    layout=config.STREAMLIT_CONFIG.LAYOUT,
    initial_sidebar_state=config.STREAMLIT_CONFIG.INITIAL_SIDEBAR_STATE,
)

st.markdown(f"<style>{styles.load_css()}</style>", unsafe_allow_html=True)


# ==========================================================
# DATA LOADING (cached, resilient)
# ==========================================================

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def _load_data() -> tuple[pd.DataFrame, list[str], list[str]]:
    """Download, parse, and return (long_df, available_months, available_categories)."""
    workbook = excel_loader.get_workbook()
    return parser.parse_workbook(workbook)


try:
    with st.spinner("Loading latest KPI data..."):
        df, available_months, available_categories = _load_data()
except excel_loader.ExcelDownloadError as exc:
    st.error(f"Could not download the KPI workbook from GitHub.\n\n{exc}")
    st.stop()
except excel_loader.ExcelCorruptedError as exc:
    st.error(f"The KPI workbook could not be parsed.\n\n{exc}")
    st.stop()

if df.empty:
    st.warning("No KPI data could be detected in the workbook.")
    st.stop()


# ==========================================================
# SHARED HELPERS (display wiring only — no KPI math)
# ==========================================================

_PAGE_ICON_KEYS: dict[str, str] = {
    "Executive Overview": "Executive",
    "Energy": "Energy",
    "Water": "Water",
    "Waste": "Waste",
}


def _fmt_number(value: float | None) -> str:
    """Format a numeric value using config precision/thousands settings, or '—' if missing."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.{config.NUMBER_PRECISION}f}".replace(",", config.THOUSANDS_SEPARATOR)


def _fmt_percent(value: float | None) -> str:
    """Format a percentage value, or '—' if missing."""
    if value is None or pd.isna(value):
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{config.NUMBER_PRECISION}f}%"


def _delta_class(value: float | None) -> str:
    """Return the CSS class for a signed delta value."""
    if value is None or pd.isna(value):
        return ""
    return "kpi-delta-positive" if value >= 0 else "kpi-delta-negative"


def _month_sort_categorical(months: pd.Series, ordered_months: list[str]) -> pd.Categorical:
    """Wrap a Month series as an ordered Categorical using the workbook's own month order."""
    return pd.Categorical(months, categories=ordered_months, ordered=True)


def _render_kpi_card(title: str, card: dict[str, Any], icon: str) -> None:
    """Render a single KPI card as styled HTML using values already computed by metrics.py."""
    current = card.get("Current Value")
    unit = card.get("Unit") or ""
    target = card.get("Target")
    variance = card.get("Variance")
    mom = card.get("MoM %")

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{icon} {title}</div>
            <div class="kpi-value">{_fmt_number(current)}<span class="kpi-unit">{unit}</span></div>
            <div style="margin-top:0.6rem; display:flex; gap:1rem; flex-wrap:wrap;">
                <span style="font-size:0.82rem; color:rgba(30,41,59,0.55);">
                    Target: <strong>{_fmt_number(target)}</strong>
                </span>
                <span class="{_delta_class(variance)}">Var: {_fmt_percent(variance)}</span>
                <span class="{_delta_class(mom)}">MoM: {_fmt_percent(mom)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _metric_snapshot(
    metric_df: pd.DataFrame, latest_month: str | None, previous_month: str | None
) -> dict[str, Any]:
    """
    Build a single-metric snapshot (Current Value / Unit / Target / Variance / MoM %)
    using the same formulas exposed by metrics.py (calculate_variance / calculate_mom),
    scoped to one Metric instead of a whole Category.
    """
    latest_df = metric_df[metric_df["Month"] == latest_month] if latest_month else metric_df.iloc[0:0]
    previous_df = metric_df[metric_df["Month"] == previous_month] if previous_month else metric_df.iloc[0:0]

    current_series = pd.to_numeric(latest_df["Value"], errors="coerce")
    target_series = pd.to_numeric(latest_df["Target"], errors="coerce")
    previous_series = pd.to_numeric(previous_df["Value"], errors="coerce")

    current_value = current_series.sum(min_count=1)
    target_value = target_series.sum(min_count=1)
    previous_value = previous_series.sum(min_count=1)

    current_value = None if pd.isna(current_value) else float(current_value)
    target_value = None if pd.isna(target_value) else float(target_value)
    previous_value = None if pd.isna(previous_value) else float(previous_value)

    unit_series = latest_df["Unit"].dropna()
    unit = str(unit_series.mode().iloc[0]) if not unit_series.empty and not unit_series.mode().empty else None

    return {
        "Current Value": current_value,
        "Unit": unit,
        "Target": target_value,
        "Variance": metrics.calculate_variance(current_value, target_value),
        "MoM %": metrics.calculate_mom(current_value, previous_value),
    }


def _render_subcategory_section(subcategory_df: pd.DataFrame, subcategory: str) -> None:
    """Render title, cards, charts, and a data table for one subcategory."""
    st.markdown(f"### {subcategory}")

    latest_month = metrics.get_latest_month(subcategory_df)
    previous_month = metrics.get_previous_month(subcategory_df)

    # Overall subcategory roll-up card, reusing metrics.get_summary_cards().
    rollup = metrics.get_summary_cards(subcategory_df)
    if rollup:
        # subcategory_df carries a single Category, so exactly one key is returned.
        _, rollup_card = next(iter(rollup.items()))
        _render_kpi_card(f"{subcategory} — Overall", rollup_card, config.ICONS.get("Target", ""))

    # Per-metric cards within this subcategory.
    metric_names = list(dict.fromkeys(str(m) for m in subcategory_df["Metric"].tolist() if pd.notna(m)))
    if metric_names:
        cols = st.columns(min(config.KPI_COLUMNS, max(len(metric_names), 1)))
        for idx, metric_name in enumerate(metric_names):
            metric_df = subcategory_df[subcategory_df["Metric"] == metric_name]
            snapshot = _metric_snapshot(metric_df, latest_month, previous_month)
            with cols[idx % len(cols)]:
                _render_kpi_card(metric_name, snapshot, "📌")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(
            charts.line_chart(subcategory_df, f"{subcategory} — Trend"),
            use_container_width=True,
        )
    with chart_col2:
        st.plotly_chart(
            charts.bar_chart(subcategory_df, f"{subcategory} — Monthly Comparison"),
            use_container_width=True,
        )

    st.plotly_chart(
        charts.target_vs_actual_chart(subcategory_df, f"{subcategory} — Target vs Actual"),
        use_container_width=True,
    )

    with st.expander(f"📋 {subcategory} — Data Table", expanded=False):
        search_term = st.text_input(
            "Search metric",
            key=f"search_{subcategory}",
            placeholder="Filter by metric name...",
        )
        table_df = subcategory_df[["Metric", "Month", "Value", "Unit", "Target"]].copy()
        table_df["_MonthSort"] = _month_sort_categorical(table_df["Month"], available_months)
        table_df = table_df.sort_values(["Metric", "_MonthSort"]).drop(columns="_MonthSort")

        if search_term:
            table_df = table_df[table_df["Metric"].str.contains(search_term, case=False, na=False)]

        st.dataframe(table_df, use_container_width=True, height=config.DEFAULT_TABLE_HEIGHT, hide_index=True)

    st.markdown("<hr/>", unsafe_allow_html=True)


def _render_category_page(category: str) -> None:
    """Render a full category page (Energy / Water / Waste) with all its subcategories."""
    category_df = metrics.filter_category(df, category)

    if category_df.empty:
        st.info(f"No data found for {category} in the current workbook.")
        return

    subcategories = metrics.get_available_subcategories(category_df)

    if not subcategories:
        # Sheets without a subcategory hierarchy (e.g. flat Category -> Metric) fall
        # back to rendering the whole category as a single section.
        _render_subcategory_section(category_df, category)
        return

    for subcategory in subcategories:
        subcategory_df = metrics.filter_subcategory(category_df, subcategory)
        if subcategory_df.empty:
            continue
        _render_subcategory_section(subcategory_df, subcategory)


# ==========================================================
# HEADER
# ==========================================================

latest_month_overall = metrics.get_latest_month(df)
total_kpis = df["Metric"].nunique()
last_refresh = datetime.now().strftime(f"{config.DATE_FORMAT} %H:%M")

st.markdown(
    f"""
    <div class="enterprise-header">
        <div>
            <h1>{config.COMPANY_NAME}</h1>
            <p>{config.DASHBOARD_TITLE} · {config.DASHBOARD_SUBTITLE}</p>
        </div>
        <div style="text-align:right;">
            <p>Reporting Month: <strong>{latest_month_overall or "—"}</strong></p>
            <p>Total KPIs: <strong>{total_kpis}</strong> &nbsp;|&nbsp; Last Refresh: <strong>{last_refresh}</strong></p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================

with st.sidebar:
    st.markdown(f"## {config.ICONS.get('Executive', '')} {config.COMPANY_SHORT_NAME}")
    st.caption(config.DASHBOARD_SUBTITLE)
    st.markdown("---")

    page_labels = [f"{config.ICONS.get(_PAGE_ICON_KEYS.get(p, ''), '')}  {p}".strip() for p in config.PAGES]
    label_to_page = dict(zip(page_labels, config.PAGES))
    selected_label = st.radio("Navigate", page_labels, label_visibility="collapsed")
    selected_page = label_to_page[selected_label]

    st.markdown("---")
    st.caption(f"Source: {config.EXCEL_FILENAME}")
    if st.button("🔄 Refresh Data"):
        excel_loader.refresh_cache()
        _load_data.clear()
        st.rerun()


# ==========================================================
# EXECUTIVE OVERVIEW
# ==========================================================

if selected_page == "Executive Overview":
    summary_cards = metrics.get_summary_cards(df)

    st.markdown("## Executive KPI Overview")
    if summary_cards:
        categories_list = list(summary_cards.keys())
        cols = st.columns(config.KPI_COLUMNS)
        for idx, category_name in enumerate(categories_list):
            icon = config.ICONS.get(category_name, "📊")
            with cols[idx % config.KPI_COLUMNS]:
                _render_kpi_card(category_name, summary_cards[category_name], icon)
    else:
        st.info("No category-level KPIs detected.")

    st.markdown("## Category Snapshots")
    snapshot_categories = [c for c in ("Energy", "Water", "Waste") if c in summary_cards]
    if snapshot_categories:
        snap_cols = st.columns(len(snapshot_categories))
        for col, category_name in zip(snap_cols, snapshot_categories):
            with col:
                _render_kpi_card(
                    f"{category_name} Snapshot",
                    summary_cards[category_name],
                    config.ICONS.get(category_name, "📊"),
                )
    else:
        st.info("Energy, Water, or Waste categories were not found in the current workbook.")

    st.markdown("## Overall Monthly Trend")
    st.plotly_chart(charts.monthly_trend_chart(df, "Overall Monthly Trend"), use_container_width=True)

    st.markdown("## Target vs Actual")
    st.plotly_chart(charts.target_vs_actual_chart(df, "Target vs Actual — All Categories"), use_container_width=True)

    st.markdown("## Category Distribution")
    if latest_month_overall:
        latest_snapshot_df = df[df["Month"] == latest_month_overall].copy()
    else:
        latest_snapshot_df = df.copy()
    # Relabel rows by Category so charts.donut_chart (which groups on "Metric")
    # can be reused to show category-level share without duplicating its logic.
    category_distribution_df = latest_snapshot_df.assign(Metric=latest_snapshot_df["Category"])
    st.plotly_chart(
        charts.donut_chart(category_distribution_df, f"Category Distribution — {latest_month_overall or 'Latest'}"),
        use_container_width=True,
    )

    st.markdown("## Summary Table")
    if summary_cards:
        summary_table = pd.DataFrame(summary_cards).T
        summary_table.index.name = "Category"
        summary_table = summary_table.reset_index()
        st.dataframe(summary_table, use_container_width=True, height=config.DEFAULT_TABLE_HEIGHT, hide_index=True)
    else:
        st.info("No summary data available.")


# ==========================================================
# ENERGY / WATER / WASTE PAGES
# ==========================================================

elif selected_page in ("Energy", "Water", "Waste"):
    st.markdown(f"## {config.ICONS.get(selected_page, '')} {selected_page}")
    _render_category_page(selected_page)


# ==========================================================
# FOOTER
# ==========================================================

st.markdown(
    f"""
    <div class="enterprise-footer">
        {config.COMPANY_NAME} · {config.DASHBOARD_TITLE} · Data source: {config.EXCEL_FILENAME}
    </div>
    """,
    unsafe_allow_html=True,
)
