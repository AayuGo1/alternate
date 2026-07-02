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
import plotly.io as pio
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
# GLOBAL PLOTLY THEME (presentation only — every chart already
# produced by charts.py automatically inherits this as Plotly's
# default template; no chart data, traces, or logic are touched).
# ==========================================================

_JFW_PLOTLY_TEMPLATE = pio.templates["plotly_white"]
_JFW_PLOTLY_TEMPLATE.layout.update(
    font=dict(family="Inter, Segoe UI, Helvetica Neue, Arial, sans-serif", color="#14213D", size=13),
    title=dict(font=dict(size=15, color="#0B2545", family="Inter, Segoe UI, sans-serif"), x=0.01, xanchor="left"),
    colorway=["#1565D8", "#16A876", "#4C9AFF", "#4FD1A5", "#0B2545", "#0F7A5C", "#8FB8FF", "#8FE0C4"],
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=24, t=48, b=36),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        bgcolor="rgba(0,0,0,0)", font=dict(size=12),
    ),
    xaxis=dict(gridcolor="rgba(15,35,64,0.07)", zerolinecolor="rgba(15,35,64,0.12)", linecolor="rgba(15,35,64,0.15)"),
    yaxis=dict(gridcolor="rgba(15,35,64,0.07)", zerolinecolor="rgba(15,35,64,0.12)", linecolor="rgba(15,35,64,0.15)"),
    hoverlabel=dict(bgcolor="#0B2545", font_color="#FFFFFF", font_size=12, bordercolor="#0B2545"),
)
pio.templates["jfw_enterprise"] = _JFW_PLOTLY_TEMPLATE
pio.templates.default = "jfw_enterprise"


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
            <div style="margin-top:0.6rem; display:flex; gap:1rem; flex-wrap:wrap; align-items:center;">
                <span style="font-size:0.82rem; color:rgba(20,33,61,0.55);">
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
# WASTE PAGE — dedicated dynamic dashboard
# ==========================================================
#
# Waste rows are classified by inspecting each row's own Subcategory/Metric
# text (generic domain vocabulary only — never a specific KPI name) plus its
# Excel-parsed Unit. Unlike Energy/Water, a single row can legitimately
# belong to MORE THAN ONE bucket at once — e.g. "Non-hazardous waste
# recycled [kg]" is simultaneously part of the Non-Hazardous inventory AND
# the Recycled outcome — so classification returns a list of buckets rather
# than a single one.

_WASTE_BUCKET_ORDER: list[str] = [
    "Hazardous Waste",
    "Non Hazardous Waste",
    "Recycled Waste",
    "Landfill",
    "Waste Intensity",
    "Other Waste Metrics",
]

_WASTE_BUCKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Recycled Waste": ("recycled", "re-cycled", "reused", "re-used", "reuse", "compost"),
    "Landfill": ("landfill",),
    "Waste Intensity": (
        "intensity", "per tonne", "per unit", "per production", "per t(",
        "specific waste", "normalized", "normalised",
    ),
    # NOTE: "non-hazardous" must be checked before "hazardous" — "hazardous"
    # is a substring of "non-hazardous", so hazardous-only matching would
    # misclassify every non-hazardous row as hazardous.
    "Non Hazardous Waste": ("non-hazardous", "non hazardous", "nonhazardous"),
    "Hazardous Waste": ("hazardous",),
}


def _classify_waste_row(subcategory: Any, metric_name: str, unit: Any) -> list[str]:
    """
    Infer every Waste section a single row belongs to, using the row's own
    Subcategory/Metric text plus its Excel-parsed Unit. A "/" in the Unit
    (e.g. a per-tonnage ratio) is treated as a hard Waste Intensity signal
    since it comes directly from the workbook. Returns a list because a row
    can be both a waste-type row (Hazardous/Non-Hazardous) and a
    disposal-outcome row (Recycled/Landfill) at the same time.
    """
    combined_text = f"{subcategory if pd.notna(subcategory) else ''} {metric_name}".lower()
    buckets: list[str] = []

    if isinstance(unit, str) and "/" in unit:
        buckets.append("Waste Intensity")
    elif any(keyword in combined_text for keyword in _WASTE_BUCKET_KEYWORDS["Waste Intensity"]):
        buckets.append("Waste Intensity")

    if any(keyword in combined_text for keyword in _WASTE_BUCKET_KEYWORDS["Recycled Waste"]):
        buckets.append("Recycled Waste")

    if any(keyword in combined_text for keyword in _WASTE_BUCKET_KEYWORDS["Landfill"]):
        buckets.append("Landfill")

    if any(keyword in combined_text for keyword in _WASTE_BUCKET_KEYWORDS["Non Hazardous Waste"]):
        buckets.append("Non Hazardous Waste")
    elif any(keyword in combined_text for keyword in _WASTE_BUCKET_KEYWORDS["Hazardous Waste"]):
        buckets.append("Hazardous Waste")

    if not buckets:
        buckets.append("Other Waste Metrics")

    return buckets


def _is_mass_row(unit: Any) -> bool:
    """
    True for rows reported in a plain mass unit (e.g. 'kg', 'Kg', 'KG') as
    opposed to a ratio/intensity unit (contains '/') or a different scale
    (e.g. 't (metric)') — used to keep composition/recycling-rate totals
    from mixing incompatible units. Purely a unit-text check, not a
    hardcoded metric list.
    """
    return isinstance(unit, str) and "/" not in unit and "kg" in unit.lower()


def _build_waste_composition_df(
    bucket_frames: dict[str, pd.DataFrame], latest_month: str | None
) -> pd.DataFrame:
    """
    Build a single-month composition snapshot (one row per waste-type
    bucket) shaped for charts.donut_chart, which groups on 'Metric'. Only
    mass-unit rows are summed so tonnage/ratio rows never distort the split.
    Recycled Waste / Landfill are outcome views that overlap with
    Hazardous/Non-Hazardous, so composition is shown only across the two
    mutually-exclusive waste-type buckets.
    """
    records: list[dict[str, Any]] = []
    for bucket_name in ("Hazardous Waste", "Non Hazardous Waste"):
        bucket_df = bucket_frames.get(bucket_name)
        if bucket_df is None or bucket_df.empty or not latest_month:
            continue
        month_df = bucket_df[(bucket_df["Month"] == latest_month) & (bucket_df["Unit"].apply(_is_mass_row))]
        total = pd.to_numeric(month_df["Value"], errors="coerce").sum(min_count=1)
        if pd.notna(total):
            records.append({"Metric": bucket_name, "Month": latest_month, "Value": float(total), "Unit": "kg", "Target": None})

    return pd.DataFrame(records, columns=["Metric", "Month", "Value", "Unit", "Target"])


def _build_recycling_pct_df(bucket_frames: dict[str, pd.DataFrame], ordered_months: list[str]) -> pd.DataFrame:
    """
    Build a Recycling % series: recycled mass / total generated mass
    (Hazardous + Non-Hazardous mass rows) for each month present. Shaped for
    charts.bar_chart / line_chart re-use.
    """
    recycled_df = bucket_frames.get("Recycled Waste", pd.DataFrame(columns=["Month", "Value", "Unit"]))
    hazardous_df = bucket_frames.get("Hazardous Waste", pd.DataFrame(columns=["Month", "Value", "Unit"]))
    non_hazardous_df = bucket_frames.get("Non Hazardous Waste", pd.DataFrame(columns=["Month", "Value", "Unit"]))
    generated_df = (
        pd.concat([hazardous_df, non_hazardous_df], ignore_index=True)
        if not (hazardous_df.empty and non_hazardous_df.empty)
        else pd.DataFrame(columns=["Month", "Value", "Unit"])
    )

    def _monthly_mass_totals(source_df: pd.DataFrame) -> pd.Series:
        if source_df.empty:
            return pd.Series(dtype=float)
        mass_df = source_df[source_df["Unit"].apply(_is_mass_row)]
        if mass_df.empty:
            return pd.Series(dtype=float)
        return mass_df.groupby("Month")["Value"].apply(lambda s: pd.to_numeric(s, errors="coerce").sum(min_count=1))

    recycled_totals = _monthly_mass_totals(recycled_df)
    generated_totals = _monthly_mass_totals(generated_df)

    records: list[dict[str, Any]] = []
    for month_label in ordered_months:
        recycled_value = recycled_totals.get(month_label)
        generated_value = generated_totals.get(month_label)
        pct_value = None
        if pd.notna(recycled_value) and pd.notna(generated_value) and generated_value:
            pct_value = float(recycled_value) / float(generated_value) * 100.0
        if pct_value is not None:
            records.append({"Metric": "Recycling Rate", "Month": month_label, "Value": pct_value, "Unit": "%", "Target": None})

    return pd.DataFrame(records, columns=["Metric", "Month", "Value", "Unit", "Target"])


def _render_waste_page(category_df: pd.DataFrame, category: str) -> None:
    """Render the dedicated, dynamically-grouped Waste dashboard."""
    if category_df.empty:
        st.info(f"No data found for {category} in the current workbook.")
        return

    bucket_assignments = category_df.apply(
        lambda row: _classify_waste_row(row["Subcategory"], row["Metric"], row["Unit"]), axis=1
    )

    bucket_frames: dict[str, pd.DataFrame] = {}
    for bucket_name in _WASTE_BUCKET_ORDER:
        mask = bucket_assignments.apply(lambda buckets: bucket_name in buckets)
        bucket_frames[bucket_name] = category_df[mask]

    latest_month = metrics.get_latest_month(category_df)
    previous_month = metrics.get_previous_month(category_df)

    # Overall Waste snapshot, reusing metrics.get_summary_cards() as-is.
    overall_summary = metrics.get_summary_cards(category_df)
    if overall_summary:
        _, overall_card = next(iter(overall_summary.items()))
        st.markdown("#### Overall Waste Snapshot")
        _render_kpi_card(f"{category} — All Streams Combined", overall_card, config.ICONS.get(category, ""))

    # Page-level charts: Waste Composition Donut + Recycling %.
    st.markdown("#### Waste Composition & Recycling")
    composition_df = _build_waste_composition_df(bucket_frames, latest_month)
    recycling_df = _build_recycling_pct_df(bucket_frames, available_months)

    comp_col, rec_col = st.columns(2)
    with comp_col:
        if not composition_df.empty:
            st.plotly_chart(
                charts.donut_chart(composition_df, f"Waste Composition — {latest_month or 'Latest'}"),
                use_container_width=True,
            )
        else:
            st.info("No mass-based waste data available for composition.")
    with rec_col:
        if not recycling_df.empty:
            st.plotly_chart(
                charts.bar_chart(recycling_df, "Recycling % — Monthly Trend"),
                use_container_width=True,
            )
        else:
            st.info("No recycling-rate data could be computed from the current workbook.")

    active_buckets = [name for name in _WASTE_BUCKET_ORDER if not bucket_frames.get(name, pd.DataFrame()).empty]
    if not active_buckets:
        st.info("No Waste metrics could be detected in the current workbook.")
        return

    tabs = st.tabs(active_buckets)
    for tab, bucket_name in zip(tabs, active_buckets):
        with tab:
            bucket_df = bucket_frames[bucket_name]
            bucket_metrics = list(dict.fromkeys(str(m) for m in bucket_df["Metric"].tolist() if pd.notna(m)))

            metric_word = "metric" if len(bucket_metrics) == 1 else "metrics"
            st.markdown(f"##### {bucket_name} · {len(bucket_metrics)} {metric_word}")

            # One KPI card per discovered metric in this section.
            cols = st.columns(min(config.KPI_COLUMNS, max(len(bucket_metrics), 1)))
            for idx, metric_name in enumerate(bucket_metrics):
                metric_df = bucket_df[bucket_df["Metric"] == metric_name]
                snapshot = _metric_snapshot(metric_df, latest_month, previous_month)
                with cols[idx % len(cols)]:
                    _render_kpi_card(metric_name, snapshot, "🗑️")

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

            with st.expander(f"📋 {bucket_name} — Data Table", expanded=False):
                search_term = st.text_input(
                    "Search metric",
                    key=f"waste_search_{bucket_name}",
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
# EXECUTIVE OVERVIEW — management dashboard
# ==========================================================
#
# Nothing here is fabricated: every card, chart, alert, and change is
# derived from rows that already exist in the parsed DataFrame, using the
# same metrics.py formulas (calculate_variance / calculate_mom / summary
# cards) and the same charts.py renderers already used elsewhere in this
# file. Only two things are fixed: a generic "what counts as an intensity
# row" keyword set (identical in spirit to the ones already used on the
# Energy/Water/Waste pages) and a small set of display constants (max
# cards, max alerts/changes, the variance threshold that defines an
# "alert"). No category, metric name, or numeric value is hardcoded.

_EXEC_MAX_CARDS = 8
_EXEC_CORE_CATEGORIES: tuple[str, ...] = ("Production", "Energy", "Water", "Waste")
_EXEC_INTENSITY_CATEGORIES: tuple[str, ...] = ("Energy", "Water", "Waste")
_EXEC_INTENSITY_KEYWORDS: tuple[str, ...] = (
    "intensity", "per tonne", "per unit", "per production",
    "specific energy", "specific water", "specific waste",
    "normalized", "normalised",
)
_EXEC_ALERT_VARIANCE_THRESHOLD = 10.0  # percent deviation from target considered noteworthy
_EXEC_MAX_ALERTS = 5
_EXEC_MAX_CHANGES = 5


def _is_intensity_row(subcategory: Any, metric_name: str, unit: Any) -> bool:
    """Same signal used on the Energy/Water/Waste pages: a '/' unit or intensity wording."""
    if isinstance(unit, str) and "/" in unit:
        return True
    combined_text = f"{subcategory if pd.notna(subcategory) else ''} {metric_name}".lower()
    return any(keyword in combined_text for keyword in _EXEC_INTENSITY_KEYWORDS)


def _get_category_intensity_snapshot(
    category_df: pd.DataFrame, latest_month: str | None, previous_month: str | None
) -> dict[str, Any] | None:
    """Roll up whichever rows in a category look like intensity/ratio metrics into one card."""
    if category_df.empty:
        return None
    mask = category_df.apply(
        lambda row: _is_intensity_row(row["Subcategory"], row["Metric"], row["Unit"]), axis=1
    )
    intensity_df = category_df[mask]
    if intensity_df.empty:
        return None
    snapshot = _metric_snapshot(intensity_df, latest_month, previous_month)
    return snapshot if snapshot.get("Current Value") is not None else None


def _build_exec_kpi_cards(source_df: pd.DataFrame) -> list[tuple[str, dict[str, Any], str]]:
    """
    Select up to 8 of the most important KPIs actually present in the
    workbook: the core category roll-ups (Production/Energy/Water/Waste),
    their Intensity counterparts where detectable, and any Safety/Health
    category roll-up — in that priority order. Categories or intensity
    signals that aren't present in the data are simply skipped, never
    invented.
    """
    summary_cards = metrics.get_summary_cards(source_df)
    if not summary_cards:
        return []

    latest_month = metrics.get_latest_month(source_df)
    previous_month = metrics.get_previous_month(source_df)

    all_categories = list(dict.fromkeys(str(c) for c in source_df["Category"].dropna().unique()))
    core_present = [c for c in _EXEC_CORE_CATEGORIES if c in all_categories]
    other_present = [c for c in all_categories if c not in core_present]
    safety_like = [c for c in other_present if any(k in c.lower() for k in ("safety", "h&s", "health"))]
    remaining_other = [c for c in other_present if c not in safety_like]

    cards: list[tuple[str, dict[str, Any], str]] = []

    for category_name in core_present:
        if category_name in summary_cards:
            cards.append((category_name, summary_cards[category_name], config.ICONS.get(category_name, "📊")))

    for category_name in core_present:
        if category_name not in _EXEC_INTENSITY_CATEGORIES:
            continue
        category_df = metrics.filter_category(source_df, category_name)
        intensity_snapshot = _get_category_intensity_snapshot(category_df, latest_month, previous_month)
        if intensity_snapshot:
            cards.append((f"{category_name} Intensity", intensity_snapshot, config.ICONS.get(category_name, "📊")))

    for category_name in safety_like + remaining_other:
        card = summary_cards.get(category_name)
        if card and card.get("Current Value") is not None:
            cards.append((category_name, card, config.ICONS.get(category_name, "🛡️")))

    return cards[:_EXEC_MAX_CARDS]


def _collect_alerts(source_df: pd.DataFrame, latest_month: str | None, max_alerts: int) -> list[dict[str, Any]]:
    """
    Flag metrics whose latest-month value deviates from its Target by more
    than the alert threshold, reusing metrics.calculate_variance() for the
    math. Magnitude-based (not direction-based), since whether a Target is a
    ceiling or a floor isn't something this display layer can infer.
    """
    if not latest_month:
        return []

    alerts: list[dict[str, Any]] = []
    grouped = source_df.dropna(subset=["Metric"]).groupby(["Category", "Metric"])
    for (category_name, metric_name), metric_df in grouped:
        latest_df = metric_df[metric_df["Month"] == latest_month]
        if latest_df.empty:
            continue
        current = pd.to_numeric(latest_df["Value"], errors="coerce").sum(min_count=1)
        target = pd.to_numeric(latest_df["Target"], errors="coerce").sum(min_count=1)
        if pd.isna(current) or pd.isna(target):
            continue
        variance = metrics.calculate_variance(float(current), float(target))
        if variance is None or pd.isna(variance):
            continue
        if abs(variance) >= _EXEC_ALERT_VARIANCE_THRESHOLD:
            alerts.append(
                {
                    "Category": str(category_name),
                    "Metric": str(metric_name),
                    "Value": float(current),
                    "Target": float(target),
                    "Variance": float(variance),
                }
            )

    alerts.sort(key=lambda a: abs(a["Variance"]), reverse=True)
    return alerts[:max_alerts]


def _collect_recent_changes(
    source_df: pd.DataFrame, latest_month: str | None, previous_month: str | None, max_changes: int
) -> list[dict[str, Any]]:
    """
    Surface the metrics with the largest month-over-month swing, reusing
    metrics.calculate_mom() for the math.
    """
    if not latest_month or not previous_month:
        return []

    changes: list[dict[str, Any]] = []
    grouped = source_df.dropna(subset=["Metric"]).groupby(["Category", "Metric"])
    for (category_name, metric_name), metric_df in grouped:
        snapshot = _metric_snapshot(metric_df, latest_month, previous_month)
        mom_value = snapshot.get("MoM %")
        if mom_value is None or pd.isna(mom_value):
            continue
        changes.append(
            {
                "Category": str(category_name),
                "Metric": str(metric_name),
                "Current Value": snapshot.get("Current Value"),
                "Unit": snapshot.get("Unit") or "",
                "MoM": float(mom_value),
            }
        )

    changes.sort(key=lambda c: abs(c["MoM"]), reverse=True)
    return changes[:max_changes]


def _render_mini_card(title: str, subtitle: str, badge_text: str, badge_class: str) -> None:
    """Small, compact card used for Alerts and Recent Changes panels."""
    st.markdown(
        f"""
        <div class="kpi-card" style="padding:0.8rem 1rem; margin-bottom:0.6rem; min-height:auto;">
            <div style="font-weight:600; font-size:0.92rem; color:var(--jfw-navy, #0B2545);">{title}</div>
            <div style="margin-top:0.35rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                <span style="font-size:0.8rem; color:rgba(20,33,61,0.6);">{subtitle}</span>
                <span class="{badge_class}">{badge_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
# EXECUTIVE OVERVIEW (management dashboard)
# ==========================================================

if selected_page == "Executive Overview":
    previous_month_overall = metrics.get_previous_month(df)

    # ---- KPI Cards (max 8, most important metrics actually present) ----
    st.markdown("## Executive KPI Overview")
    exec_cards = _build_exec_kpi_cards(df)
    if exec_cards:
        num_cols = min(config.KPI_COLUMNS, 4)
        cols = st.columns(num_cols)
        for idx, (label, card, icon) in enumerate(exec_cards):
            with cols[idx % num_cols]:
                _render_kpi_card(label, card, icon)
    else:
        st.info("No category-level KPIs detected.")

    # ---- Monthly KPI Trend ----
    st.markdown("## Monthly KPI Trend")
    st.plotly_chart(charts.monthly_trend_chart(df, "Monthly KPI Trend"), use_container_width=True)

    # ---- Production vs Energy / Energy vs Water ----
    st.markdown("## Cross-Category Trends")
    all_categories_present = set(str(c) for c in df["Category"].dropna().unique())
    comparison_col1, comparison_col2 = st.columns(2)

    with comparison_col1:
        if {"Production", "Energy"}.issubset(all_categories_present):
            prod_energy_df = df[df["Category"].isin(["Production", "Energy"])]
            st.plotly_chart(
                charts.monthly_trend_chart(prod_energy_df, "Production vs Energy"),
                use_container_width=True,
            )
        else:
            st.info("Production and/or Energy data not found in the current workbook.")

    with comparison_col2:
        if {"Energy", "Water"}.issubset(all_categories_present):
            energy_water_df = df[df["Category"].isin(["Energy", "Water"])]
            st.plotly_chart(
                charts.monthly_trend_chart(energy_water_df, "Energy vs Water"),
                use_container_width=True,
            )
        else:
            st.info("Energy and/or Water data not found in the current workbook.")

    # ---- Waste Composition (reuses the Waste page's own classification logic) ----
    st.markdown("## Waste Composition")
    if "Waste" in all_categories_present:
        waste_category_df = metrics.filter_category(df, "Waste")
        waste_latest_month = metrics.get_latest_month(waste_category_df)
        waste_bucket_assignments = waste_category_df.apply(
            lambda row: _classify_waste_row(row["Subcategory"], row["Metric"], row["Unit"]), axis=1
        )
        waste_bucket_frames = {
            bucket_name: waste_category_df[waste_bucket_assignments.apply(lambda buckets: bucket_name in buckets)]
            for bucket_name in _WASTE_BUCKET_ORDER
        }
        exec_composition_df = _build_waste_composition_df(waste_bucket_frames, waste_latest_month)
        if not exec_composition_df.empty:
            st.plotly_chart(
                charts.donut_chart(exec_composition_df, f"Waste Composition — {waste_latest_month or 'Latest'}"),
                use_container_width=True,
            )
        else:
            st.info("No mass-based waste data available for composition.")
    else:
        st.info("Waste data not found in the current workbook.")

    # ---- Latest Alerts / Recent KPI Changes ----
    st.markdown("## Latest Alerts & Recent Changes")
    alert_col, change_col = st.columns(2)

    with alert_col:
        st.markdown(f"#### 🚨 Latest Alerts (±{_EXEC_ALERT_VARIANCE_THRESHOLD:.0f}% vs Target)")
        alerts = _collect_alerts(df, latest_month_overall, _EXEC_MAX_ALERTS)
        if alerts:
            for alert in alerts:
                direction = "above" if alert["Variance"] >= 0 else "below"
                _render_mini_card(
                    title=f"{alert['Metric']} ({alert['Category']})",
                    subtitle=f"Value: {_fmt_number(alert['Value'])} · Target: {_fmt_number(alert['Target'])} · {direction} target",
                    badge_text=_fmt_percent(alert["Variance"]),
                    badge_class=_delta_class(alert["Variance"]),
                )
        else:
            st.info("No KPIs are significantly off target this month.")

    with change_col:
        st.markdown("#### 📈 Recent KPI Changes (MoM)")
        changes = _collect_recent_changes(df, latest_month_overall, previous_month_overall, _EXEC_MAX_CHANGES)
        if changes:
            for change in changes:
                _render_mini_card(
                    title=f"{change['Metric']} ({change['Category']})",
                    subtitle=f"Current: {_fmt_number(change['Current Value'])}{change['Unit']}",
                    badge_text=_fmt_percent(change["MoM"]),
                    badge_class=_delta_class(change["MoM"]),
                )
        else:
            st.info("No month-over-month comparisons available yet.")

    # ---- Summary Table ----
    st.markdown("## Summary Table")
    summary_cards_full = metrics.get_summary_cards(df)
    if summary_cards_full:
        summary_table = pd.DataFrame(summary_cards_full).T
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
# WASTE PAGE (dedicated dynamic dashboard)
# ==========================================================

elif selected_page == "Waste":
    st.markdown(f"## {config.ICONS.get(selected_page, '')} {selected_page}")
    _render_waste_page(metrics.filter_category(df, selected_page), selected_page)


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
