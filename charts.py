
"""
charts.py
Reusable Plotly (Graph Objects) chart builders for the JFL sustainability
dashboard. Operates on the long-format DataFrame produced by parser.py.

Charts are built dynamically from whatever Metric / Month / Value / Unit
values are present in the DataFrame — no KPI or metric names are hardcoded,
and no KPI calculations (variance, MoM, targets math, etc.) are performed
here; that belongs in metrics.py.

This module contains NO Streamlit code, NO HTML, and NO CSS.
Every function returns a plotly.graph_objects.Figure. Nothing is rendered
or shown from within this module.
"""

from __future__ import annotations

from itertools import cycle
from typing import Final

import pandas as pd
import plotly.graph_objects as go

import config

_MONTH_ORDER: Final[dict[str, int]] = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

_CHART_COLOR_SEQUENCE: Final[list[str]] = getattr(config, "CHART_COLORS", None) or [
    config.THEME.PRIMARY_COLOR,
    config.THEME.SECONDARY_COLOR,
    config.THEME.SUCCESS_COLOR,
    config.THEME.WARNING_COLOR,
    config.THEME.DANGER_COLOR,
]

_MARGINS: Final[dict[str, int]] = {"l": 50, "r": 30, "t": 60, "b": 50}


def _color_cycle() -> "cycle[str]":
    """Return a fresh cycling iterator over the enterprise color palette."""
    return cycle(_CHART_COLOR_SEQUENCE)


def _month_sort_key(month_label: object) -> tuple[int, int]:
    """Build a chronological sort key from a 'Mon-YYYY' style month label."""
    if not isinstance(month_label, str) or "-" not in month_label:
        return (0, 0)
    abbr, _, year_str = month_label.partition("-")
    month_num = _MONTH_ORDER.get(abbr.strip().capitalize(), 0)
    try:
        year = int(year_str.strip())
    except ValueError:
        year = 0
    return (year, month_num)


def _sorted_months(df: pd.DataFrame) -> list[str]:
    """Return unique Month labels from df in chronological order."""
    if df.empty or "Month" not in df.columns:
        return []
    months = df["Month"].dropna().unique().tolist()
    return sorted(months, key=_month_sort_key)


def _unit_axis_label(df: pd.DataFrame) -> str:
    """Build a y-axis label from the distinct Unit values present in df."""
    if df.empty or "Unit" not in df.columns:
        return "Value"
    units = [u for u in df["Unit"].dropna().unique().tolist() if str(u).strip()]
    if not units:
        return "Value"
    if len(units) == 1:
        return str(units[0])
    return " / ".join(str(u) for u in units)


def _apply_enterprise_layout(fig: go.Figure, title: str) -> go.Figure:
    """Apply consistent enterprise styling to any chart figure."""
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        template=config.PLOT_TEMPLATE,
        height=config.DEFAULT_CHART_HEIGHT,
        autosize=True,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=_MARGINS,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        font={"color": config.THEME.TEXT_COLOR},
    )
    return fig


def _empty_figure(title: str) -> go.Figure:
    """Return a placeholder figure when there is no data to plot."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": config.THEME.TEXT_COLOR},
    )
    return _apply_enterprise_layout(fig, title)


def _iter_metric_groups(df: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    """
    Group df into (trace_name, group_df) pairs by Metric. If the same
    Metric name maps to more than one distinct Unit (e.g. a raw value and
    its per-tonnage ratio sharing a base name), the Unit is appended to
    the trace name so the two series are not collapsed into one.
    """
    if df.empty or "Metric" not in df.columns:
        return []

    unit_col = df["Unit"] if "Unit" in df.columns else pd.Series([None] * len(df), index=df.index)
    grouped = df.assign(_unit=unit_col).groupby(["Metric", "_unit"], dropna=False)

    metric_unit_counts = df.assign(_unit=unit_col).groupby("Metric")["_unit"].nunique(dropna=False)

    groups: list[tuple[str, pd.DataFrame]] = []
    for (metric_name, unit_value), group_df in grouped:
        needs_unit_suffix = metric_unit_counts.get(metric_name, 1) > 1
        if needs_unit_suffix and unit_value not in (None, ""):
            trace_name = f"{metric_name} ({unit_value})"
        else:
            trace_name = str(metric_name)
        groups.append((trace_name, group_df.drop(columns="_unit")))

    return groups


def line_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Line chart of Value over Month. One trace per unique Metric — if only
    one Metric is present, a single trace is drawn automatically.
    """
    if df.empty or "Metric" not in df.columns:
        return _empty_figure(title)

    months = _sorted_months(df)
    colors = _color_cycle()
    fig = go.Figure()

    for trace_name, metric_df in _iter_metric_groups(df):
        ordered = metric_df.drop_duplicates(subset="Month").set_index("Month").reindex(months).reset_index()
        fig.add_trace(
            go.Scatter(
                x=ordered["Month"],
                y=ordered["Value"],
                mode="lines+markers",
                name=trace_name,
                line={"color": next(colors), "width": 2.5},
                marker={"size": 6},
                hovertemplate="%{x}<br>%{y}<extra>%{fullData.name}</extra>",
            )
        )

    fig.update_yaxes(title_text=_unit_axis_label(df))
    return _apply_enterprise_layout(fig, title)


def bar_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Grouped bar chart of Value by Month. One series per unique Metric.
    """
    if df.empty or "Metric" not in df.columns:
        return _empty_figure(title)

    months = _sorted_months(df)
    colors = _color_cycle()
    fig = go.Figure()

    for trace_name, metric_df in _iter_metric_groups(df):
        ordered = metric_df.drop_duplicates(subset="Month").set_index("Month").reindex(months).reset_index()
        fig.add_trace(
            go.Bar(
                x=ordered["Month"],
                y=ordered["Value"],
                name=trace_name,
                marker_color=next(colors),
                hovertemplate="%{x}<br>%{y}<extra>%{fullData.name}</extra>",
            )
        )

    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text=_unit_axis_label(df))
    return _apply_enterprise_layout(fig, title)


def stacked_bar_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Stacked bar chart of Value by Month. One stacked segment per unique
    Metric.
    """
    if df.empty or "Metric" not in df.columns:
        return _empty_figure(title)

    months = _sorted_months(df)
    colors = _color_cycle()
    fig = go.Figure()

    for trace_name, metric_df in _iter_metric_groups(df):
        ordered = metric_df.drop_duplicates(subset="Month").set_index("Month").reindex(months).reset_index()
        fig.add_trace(
            go.Bar(
                x=ordered["Month"],
                y=ordered["Value"],
                name=trace_name,
                marker_color=next(colors),
                hovertemplate="%{x}<br>%{y}<extra>%{fullData.name}</extra>",
            )
        )

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text=_unit_axis_label(df))
    return _apply_enterprise_layout(fig, title)


def area_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Stacked area chart of Value over Month. One layer per unique Metric.
    """
    if df.empty or "Metric" not in df.columns:
        return _empty_figure(title)

    months = _sorted_months(df)
    colors = _color_cycle()
    fig = go.Figure()

    for trace_name, metric_df in _iter_metric_groups(df):
        ordered = metric_df.drop_duplicates(subset="Month").set_index("Month").reindex(months).reset_index()
        color = next(colors)
        fig.add_trace(
            go.Scatter(
                x=ordered["Month"],
                y=ordered["Value"],
                mode="lines",
                name=trace_name,
                line={"color": color, "width": 1.5},
                fill="tonexty" if len(fig.data) > 0 else "tozeroy",
                stackgroup="one",
                hovertemplate="%{x}<br>%{y}<extra>%{fullData.name}</extra>",
            )
        )

    fig.update_yaxes(title_text=_unit_axis_label(df))
    return _apply_enterprise_layout(fig, title)


def donut_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Donut chart showing the share of total Value contributed by each
    unique Metric present in df.
    """
    if df.empty or "Metric" not in df.columns:
        return _empty_figure(title)

    groups = _iter_metric_groups(df)
    if not groups:
        return _empty_figure(title)

    labels: list[str] = []
    values: list[float] = []
    for trace_name, metric_df in groups:
        total = metric_df["Value"].sum(min_count=1)
        if pd.isna(total):
            continue
        labels.append(trace_name)
        values.append(float(total))

    if not values:
        return _empty_figure(title)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker={"colors": _CHART_COLOR_SEQUENCE},
                hovertemplate="%{label}<br>%{value} (%{percent})<extra></extra>",
            )
        ]
    )
    return _apply_enterprise_layout(fig, title)


def gauge_chart(value: float, min_value: float, max_value: float, title: str) -> go.Figure:
    """
    Gauge indicator chart for a single scalar value within a min/max range.
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [min_value, max_value]},
                "bar": {"color": config.THEME.PRIMARY_COLOR},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 1,
                "bordercolor": config.THEME.SECONDARY_COLOR,
            },
        )
    )
    return _apply_enterprise_layout(fig, title)


def target_vs_actual_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Grouped bar chart comparing actual Value against Target, per unique
    Metric present in df.
    """
    if df.empty or "Metric" not in df.columns or "Target" not in df.columns:
        return _empty_figure(title)

    groups = _iter_metric_groups(df)
    if not groups:
        return _empty_figure(title)

    labels: list[str] = []
    actual_values: list[float | None] = []
    target_values: list[float | None] = []
    for trace_name, metric_df in groups:
        actual_total = metric_df["Value"].sum(min_count=1)
        target_total = pd.to_numeric(metric_df["Target"], errors="coerce").sum(min_count=1)
        if pd.isna(actual_total) and pd.isna(target_total):
            continue
        labels.append(trace_name)
        actual_values.append(None if pd.isna(actual_total) else float(actual_total))
        target_values.append(None if pd.isna(target_total) else float(target_total))

    if not labels:
        return _empty_figure(title)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=actual_values,
            name="Actual",
            marker_color=config.THEME.PRIMARY_COLOR,
            hovertemplate="%{x}<br>Actual: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=target_values,
            name="Target",
            marker_color=config.THEME.WARNING_COLOR,
            hovertemplate="%{x}<br>Target: %{y}<extra></extra>",
        )
    )
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text=_unit_axis_label(df))
    return _apply_enterprise_layout(fig, title)


def monthly_trend_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Single aggregated trend line of total Value (summed across all Metrics
    present in df) across Month.
    """
    if df.empty or "Month" not in df.columns:
        return _empty_figure(title)

    months = _sorted_months(df)
    totals = df.groupby("Month")["Value"].sum(min_count=1).reindex(months)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=totals.index.tolist(),
            y=totals.values.tolist(),
            mode="lines+markers",
            name="Trend",
            line={"color": config.THEME.PRIMARY_COLOR, "width": 3, "shape": "spline"},
            marker={"size": 8, "color": config.THEME.PRIMARY_COLOR},
            fill="tozeroy",
            fillcolor="rgba(11, 95, 255, 0.10)",
            hovertemplate="%{x}<br>%{y}<extra></extra>",
        )
    )

    fig.update_yaxes(title_text=_unit_axis_label(df))
    return _apply_enterprise_layout(fig, title)
