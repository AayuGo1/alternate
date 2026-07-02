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
# ENERGY PAGE — dedicated dynamic dashboard
# ==========================================================
#
# Energy gets its own layout (tabs instead of stacked expander sections)
# and its own grouping logic: rather than relying solely on the workbook's
# Subcategory column, every Energy metric is classified into a section by
# inspecting its own name (and Subcategory, when present) for keywords —
# so a brand-new metric added to the workbook next month is automatically
# picked up and bucketed without any code change here. No metric name,
# unit, category, or sheet name is ever hardcoded; only the classification
# keywords (generic energy-domain vocabulary) are fixed.

_ENERGY_BUCKET_ORDER: list[str] = [
    "Direct Energy",
    "Indirect Energy",
    "Energy KPI",
    "Energy Intensity",
    "Renewable Energy",
    "Other Energy Metrics",
]

_ENERGY_BUCKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Renewable Energy": ("renewable", "solar", "wind", "green power", "biomass"),
    "Energy Intensity": (
        "intensity", "per tonne", "per unit", "per production",
        "specific energy", "normalized", "normalised",
    ),
    "Energy KPI": ("kpi",),
    # NOTE: "indirect" must be checked before "direct" — "indirect" contains
    # "direct" as a substring, so direct-only matching would misclassify it.
    "Indirect Energy": ("indirect",),
    "Direct Energy": ("direct",),
}


def _classify_energy_metric(subcategory: Any, metric_name: str) -> str:
    """
    Infer which Energy section a metric belongs to, using only text already
    present in the workbook (its own name and, if available, its Subcategory).
    Falls back to 'Other Energy Metrics' when nothing matches.
    """
    combined_text = f"{subcategory if pd.notna(subcategory) else ''} {metric_name}".lower()

    for bucket_name in ("Renewable Energy", "Energy Intensity", "Energy KPI", "Indirect Energy", "Direct Energy"):
        if any(keyword in combined_text for keyword in _ENERGY_BUCKET_KEYWORDS[bucket_name]):
            return bucket_name

    return "Other Energy Metrics"


def _build_metric_mom_df(metric_df: pd.DataFrame, ordered_months: list[str]) -> pd.DataFrame:
    """
    Build a Month-over-Month percentage-change series for a single metric,
    across every month present, reusing metrics.calculate_mom() for each
    consecutive pair rather than inventing a new formula here. The result
    is shaped so it can be rendered with the existing charts.bar_chart().
    """
    if metric_df.empty:
        return pd.DataFrame(columns=["Metric", "Month", "Value", "Unit", "Target"])

    metric_name = str(metric_df["Metric"].iloc[0])
    months_present = [m for m in ordered_months if m in set(metric_df["Month"])]
    monthly_totals = metric_df.groupby("Month")["Value"].apply(
        lambda s: pd.to_numeric(s, errors="coerce").sum(min_count=1)
    )

    records: list[dict[str, Any]] = []
    previous_value: float | None = None
    for month_label in months_present:
        raw_value = monthly_totals.get(month_label)
        current_value = None if pd.isna(raw_value) else float(raw_value)
        mom_value = metrics.calculate_mom(current_value, previous_value)
        records.append(
            {
                "Metric": metric_name,
                "Month": month_label,
                "Value": mom_value,
                "Unit": "%",
                "Target": None,
            }
        )
        previous_value = current_value

    return pd.DataFrame(records, columns=["Metric", "Month", "Value", "Unit", "Target"])


def _render_energy_page(category_df: pd.DataFrame, category: str) -> None:
    """Render the dedicated, dynamically-grouped Energy dashboard."""
    if category_df.empty:
        st.info(f"No data found for {category} in the current workbook.")
        return

    metric_names = list(dict.fromkeys(str(m) for m in category_df["Metric"].tolist() if pd.notna(m)))

    # First non-null Subcategory seen for each Metric, used only as extra
    # classification context (never displayed as a hardcoded label).
    metric_subcategory = (
        category_df.dropna(subset=["Metric"])
        .groupby("Metric")["Subcategory"]
        .agg(lambda s: next((v for v in s if pd.notna(v)), None))
    )

    buckets: dict[str, list[str]] = {name: [] for name in _ENERGY_BUCKET_ORDER}
    for metric_name in metric_names:
        bucket_name = _classify_energy_metric(metric_subcategory.get(metric_name), metric_name)
        buckets[bucket_name].append(metric_name)

    latest_month = metrics.get_latest_month(category_df)
    previous_month = metrics.get_previous_month(category_df)

    # Overall Energy snapshot, reusing metrics.get_summary_cards() as-is.
    overall_summary = metrics.get_summary_cards(category_df)
    if overall_summary:
        _, overall_card = next(iter(overall_summary.items()))
        st.markdown("#### Overall Energy Snapshot")
        _render_kpi_card(f"{category} — All Sources Combined", overall_card, config.ICONS.get(category, ""))

    active_buckets = [name for name in _ENERGY_BUCKET_ORDER if buckets.get(name)]
    if not active_buckets:
        st.info("No Energy metrics could be detected in the current workbook.")
        return

    tabs = st.tabs(active_buckets)
    for tab, bucket_name in zip(tabs, active_buckets):
        with tab:
            bucket_metrics = buckets[bucket_name]
            bucket_df = category_df[category_df["Metric"].isin(bucket_metrics)]

            metric_word = "metric" if len(bucket_metrics) == 1 else "metrics"
            st.markdown(f"##### {bucket_name} · {len(bucket_metrics)} {metric_word}")

            # One KPI card per discovered metric in this section.
            cols = st.columns(min(config.KPI_COLUMNS, max(len(bucket_metrics), 1)))
            for idx, metric_name in enumerate(bucket_metrics):
                metric_df = bucket_df[bucket_df["Metric"] == metric_name]
                snapshot = _metric_snapshot(metric_df, latest_month, previous_month)
                with cols[idx % len(cols)]:
                    _render_kpi_card(metric_name, snapshot, "⚡")

            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.plotly_chart(
                    charts.line_chart(bucket_df, f"{bucket_name} — Monthly Trend"),
                    use_container_width=True,
                )
            with chart_col2:
                st.plotly_chart(
                    charts.target_vs_actual_chart(bucket_df, f"{bucket_name} — Target vs Actual"),
                    use_container_width=True,
                )

            mom_frames = [
                _build_metric_mom_df(bucket_df[bucket_df["Metric"] == metric_name], available_months)
                for metric_name in bucket_metrics
            ]
            mom_df = (
                pd.concat(mom_frames, ignore_index=True)
                if mom_frames
                else pd.DataFrame(columns=["Metric", "Month", "Value", "Unit", "Target"])
            )
            st.plotly_chart(
                charts.bar_chart(mom_df, f"{bucket_name} — MoM % Change"),
                use_container_width=True,
            )

            # Multiple sources -> share-of-total pie. Exactly one source ->
            # the Monthly Trend line above already tells that story, per spec.
            if len(bucket_metrics) > 1:
                st.plotly_chart(
                    charts.donut_chart(bucket_df, f"{bucket_name} — Source Distribution"),
                    use_container_width=True,
                )

            with st.expander(f"📋 {bucket_name} — Data Table", expanded=False):
                search_term = st.text_input(
                    "Search metric",
                    key=f"energy_search_{bucket_name}",
                    placeholder="Filter by metric name...",
                )
                table_df = bucket_df[["Metric", "Month", "Value", "Unit", "Target"]].copy()
                table_df["_MonthSort"] = _month_sort_categorical(table_df["Month"], available_months)
                table_df = table_df.sort_values(["Metric", "_MonthSort"]).drop(columns="_MonthSort")

                if search_term:
                    table_df = table_df[table_df["Metric"].str.contains(search_term, case=False, na=False)]

                st.dataframe(
                    table_df, use_container_width=True, height=config.DEFAULT_TABLE_HEIGHT, hide_index=True
                )


# ==========================================================
# WATER PAGE — dedicated dynamic dashboard
# ==========================================================
#
# Same philosophy as the Energy page: nothing about Water sections or
# metrics is hardcoded. Each row is classified into a section by
# inspecting its Subcategory/Metric text for keywords, with one extra
# signal unique to Water: if the row's own Excel-parsed Unit contains a
# "/" (e.g. "m³/Gross Weight (t Metric)"), that row is a per-production
# ratio and is treated as Water Intensity regardless of its metric name —
# so a metric like "Total water withdrawal" that is reported both as an
# absolute m³ figure and as an intensity ratio automatically lands in
# both the Withdrawal section (for the m³ rows) and the Intensity section
# (for the ratio rows), using the units exactly as they appear in Excel.

_WATER_BUCKET_ORDER: list[str] = [
    "Water Withdrawal",
    "Water Consumption",
    "Water Recycled",
    "Water KPI",
    "Water Intensity",
    "Other Water Metrics",
]

_WATER_BUCKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Water Recycled": ("recycled", "re-cycled", "reused", "re-used", "reuse"),
    "Water Intensity": (
        "intensity", "per tonne", "per unit", "per production",
        "specific water", "normalized", "normalised",
    ),
    "Water KPI": ("kpi",),
    # Discharge / effluent text is checked separately (see _WATER_DISCHARGE_KEYWORDS
    # below) so it is never swept into Withdrawal just because it also mentions
    # "municipal" or "surface water" as the receiving point rather than the source.
    "Water Withdrawal": (
        "withdrawal", "abstract", "municipal", "public supply", "public / municipal",
        "surface water", "ground water", "groundwater", "tanker", "borewell",
        "bore well", "river", "lake", "lagoon",
    ),
    "Water Consumption": ("consumption", "consumed"),
}

_WATER_DISCHARGE_KEYWORDS: tuple[str, ...] = ("discharge", "discharged", "wastewater", "effluent", "sewer")


def _classify_water_row(subcategory: Any, metric_name: str, unit: Any) -> str:
    """
    Infer which Water section a single row belongs to, using the row's own
    Subcategory/Metric text plus its Excel-parsed Unit. A "/" in the Unit
    (e.g. a per-tonnage ratio) is treated as a hard Water Intensity signal
    since it comes directly from the workbook rather than being inferred
    from wording. Discharge/effluent rows are routed to Other Water Metrics
    rather than Withdrawal, since mentioning "municipal" or "surface water"
    as the *destination* of discharged water is not the same as withdrawing
    from that source.
    """
    if isinstance(unit, str) and "/" in unit:
        return "Water Intensity"

    combined_text = f"{subcategory if pd.notna(subcategory) else ''} {metric_name}".lower()

    for bucket_name in ("Water Recycled", "Water Intensity", "Water KPI"):
        if any(keyword in combined_text for keyword in _WATER_BUCKET_KEYWORDS[bucket_name]):
            return bucket_name

    if any(keyword in combined_text for keyword in _WATER_DISCHARGE_KEYWORDS):
        return "Other Water Metrics"

    for bucket_name in ("Water Withdrawal", "Water Consumption"):
        if any(keyword in combined_text for keyword in _WATER_BUCKET_KEYWORDS[bucket_name]):
            return bucket_name

    return "Other Water Metrics"


def _render_water_page(category_df: pd.DataFrame, category: str) -> None:
    """Render the dedicated, dynamically-grouped Water dashboard."""
    if category_df.empty:
        st.info(f"No data found for {category} in the current workbook.")
        return

    bucket_series = category_df.apply(
        lambda row: _classify_water_row(row["Subcategory"], row["Metric"], row["Unit"]), axis=1
    )
    classified_df = category_df.assign(_Bucket=bucket_series)

    latest_month = metrics.get_latest_month(category_df)
    previous_month = metrics.get_previous_month(category_df)

    # Overall Water snapshot, reusing metrics.get_summary_cards() as-is.
    overall_summary = metrics.get_summary_cards(category_df)
    if overall_summary:
        _, overall_card = next(iter(overall_summary.items()))
        st.markdown("#### Overall Water Snapshot")
        _render_kpi_card(f"{category} — All Sources Combined", overall_card, config.ICONS.get(category, ""))

    active_buckets = [
        name for name in _WATER_BUCKET_ORDER if not classified_df[classified_df["_Bucket"] == name].empty
    ]
    if not active_buckets:
        st.info("No Water metrics could be detected in the current workbook.")
        return

    tabs = st.tabs(active_buckets)
    for tab, bucket_name in zip(tabs, active_buckets):
        with tab:
            bucket_df = classified_df[classified_df["_Bucket"] == bucket_name].drop(columns="_Bucket")
            bucket_metrics = list(dict.fromkeys(str(m) for m in bucket_df["Metric"].tolist() if pd.notna(m)))

            metric_word = "metric" if len(bucket_metrics) == 1 else "metrics"
            st.markdown(f"##### {bucket_name} · {len(bucket_metrics)} {metric_word}")

            # One KPI card per discovered metric in this section (Excel units shown as-is).
            cols = st.columns(min(config.KPI_COLUMNS, max(len(bucket_metrics), 1)))
            for idx, metric_name in enumerate(bucket_metrics):
                metric_df = bucket_df[bucket_df["Metric"] == metric_name]
                snapshot = _metric_snapshot(metric_df, latest_month, previous_month)
                with cols[idx % len(cols)]:
                    _render_kpi_card(metric_name, snapshot, "💧")

            trend_title = f"{bucket_name} Trend" if bucket_name != "Water Intensity" else "Water Intensity Trend"
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.plotly_chart(
                    charts.line_chart(bucket_df, trend_title),
                    use_container_width=True,
                )
            with chart_col2:
                st.plotly_chart(
                    charts.target_vs_actual_chart(bucket_df, f"{bucket_name} — Target vs Actual"),
                    use_container_width=True,
                )

            # Water Source Distribution — only meaningful (and only shown) where
            # more than one distinct withdrawal source is actually reported.
            if bucket_name == "Water Withdrawal" and len(bucket_metrics) > 1:
                st.plotly_chart(
                    charts.donut_chart(bucket_df, "Water Source Distribution"),
                    use_container_width=True,
                )

            with st.expander(f"📋 {bucket_name} — Data Table", expanded=False):
                search_term = st.text_input(
                    "Search metric",
                    key=f"water_search_{bucket_name}",
                    placeholder="Filter by metric name...",
                )
                table_df = bucket_df[["Metric", "Month", "Value", "Unit", "Target"]].copy()
                table_df["_MonthSort"] = _month_sort_categorical(table_df["Month"], available_months)
                table_df = table_df.sort_values(["Metric", "_MonthSort"]).drop(columns="_MonthSort")

                if search_term:
                    table_df = table_df[table_df["Metric"].str.contains(search_term, case=False, na=False)]

                st.dataframe(
                    table_df, use_container_width=True, height=config.DEFAULT_TABLE_HEIGHT, hide_index=True
                )


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
# ENERGY PAGE (dedicated dynamic dashboard)
# ==========================================================

elif selected_page == "Energy":
    st.markdown(f"## {config.ICONS.get(selected_page, '')} {selected_page}")
    _render_energy_page(metrics.filter_category(df, selected_page), selected_page)


# ==========================================================
# WATER PAGE (dedicated dynamic dashboard)
# ==========================================================

elif selected_page == "Water":
    st.markdown(f"## {config.ICONS.get(selected_page, '')} {selected_page}")
    _render_water_page(metrics.filter_category(df, selected_page), selected_page)


# ==========================================================
# WASTE PAGE (unchanged)
# ==========================================================

elif selected_page == "Waste":
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
