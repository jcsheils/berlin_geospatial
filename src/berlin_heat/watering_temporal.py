"""Build fixed-scale monthly atlas products from the canonical LOR-month panel."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


REFERENCE_YEARS = tuple(range(2021, 2026))
ACTIVE_SEASON_MONTHS = tuple(range(4, 10))
SEASON_ORDER = ("Winter", "Spring", "Summer", "Autumn")
POSITIVE_BREAK_QUANTILES = (0.25, 0.50, 0.75, 0.90, 0.975)
MAP_COLORS = (
    "#f2f2f2",  # recorded zero
    "#edf8fb",
    "#ccece6",
    "#99d8c9",
    "#66c2a4",
    "#2ca25f",
    "#006d2c",
    "#9b9b9b",  # missing inventory denominator
)


@dataclass(frozen=True)
class WateringTemporalArtifacts:
    """Paths and headline counts produced by a temporal-atlas build."""

    calendar_lor_path: Path
    city_month_path: Path
    city_calendar_path: Path
    season_summary_path: Path
    year_summary_path: Path
    metadata_path: Path
    timing_figure_path: Path
    calendar_atlas_path: Path
    active_season_atlas_path: Path
    yearly_atlas_paths: tuple[Path, ...]
    calendar_lor_rows: int
    city_month_rows: int
    map_breaks: tuple[float, ...]


def season_for_month(month: int) -> str:
    """Return the meteorological season for a calendar month number."""

    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    if month in (9, 10, 11):
        return "Autumn"
    raise ValueError(f"Calendar month must be 1-12; received {month!r}.")


def derive_shared_positive_breaks(
    values: Iterable[float],
    *,
    quantiles: tuple[float, ...] = POSITIVE_BREAK_QUANTILES,
) -> tuple[float, ...]:
    """Derive monotonic fixed map thresholds from positive finite values."""

    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - exercised by users
        raise RuntimeError("Temporal map classification requires numpy.") from exc

    array = np.asarray(list(values), dtype="float64")
    positive = array[np.isfinite(array) & (array > 0)]
    if positive.size == 0:
        raise ValueError("Cannot derive map breaks without positive finite values.")
    breaks = np.quantile(positive, quantiles, method="linear")
    if not np.all(np.diff(breaks) > 0):
        raise ValueError("Positive map quantiles are not strictly increasing.")
    return tuple(float(value) for value in breaks)


def classify_map_value(value: object, breaks: tuple[float, ...]) -> int:
    """Return a stable class: zero, positive quantile band, or missing."""

    try:
        import math

        numeric = float(value)
    except (TypeError, ValueError):
        return len(breaks) + 2
    if not math.isfinite(numeric):
        return len(breaks) + 2
    if numeric < 0:
        raise ValueError("A negative recorded-watering map value is invalid.")
    if numeric == 0:
        return 0
    for index, threshold in enumerate(breaks, start=1):
        if numeric <= threshold:
            return index
    return len(breaks) + 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_or_absolute(path: Path, root: Path) -> str:
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def _atomic_csv(frame: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def _atomic_json(document: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _validate_panel(panel: Any, pd: Any) -> None:
    required = {
        "month",
        "plr_id",
        "plr_name",
        "bzr_id",
        "bzr_name",
        "district",
        "platform_month_status",
        "platform_live_days",
        "current_inventory_trees",
        "recorded_watered_trees",
        "recorded_watering_events",
        "recorded_litres",
        "recorded_reach_pct_current_inventory",
        "recorded_events_per_1000_current_inventory_trees",
        "recorded_litres_per_current_inventory_tree",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError("LOR-month panel is missing columns: " + ", ".join(missing))
    if len(panel) != 542 * 68:
        raise ValueError(f"Expected 36,856 LOR-month rows; found {len(panel):,}.")
    if panel.duplicated(["month", "plr_id"]).any():
        raise ValueError("LOR-month panel contains duplicate month/Planungsraum keys.")
    if panel["plr_id"].nunique() != 542 or panel["month"].nunique() != 68:
        raise ValueError("LOR-month panel is not the expected 542 by 68 balance.")
    expected = pd.date_range("2020-05-01", "2025-12-01", freq="MS")
    observed = pd.DatetimeIndex(sorted(panel["month"].unique()))
    if not observed.equals(expected):
        raise ValueError("LOR-month panel does not cover May 2020-December 2025.")
    counts = panel.groupby("month", observed=True)["plr_id"].size()
    if not counts.eq(542).all():
        raise ValueError("At least one month does not contain all 542 Planungsräume.")
    monthly_status = panel.groupby("month", observed=True).agg(
        statuses=("platform_month_status", "nunique"),
        live_day_values=("platform_live_days", "nunique"),
    )
    if not monthly_status[["statuses", "live_day_values"]].eq(1).all().all():
        raise ValueError("Platform status and live days must be uniform within a month.")
    may_2020 = panel[panel["month"].eq(pd.Timestamp("2020-05-01"))]
    if not may_2020["platform_month_status"].eq("partial_platform_start").all():
        raise ValueError("All May 2020 rows must be marked partial_platform_start.")
    if not may_2020["platform_live_days"].eq(14).all():
        raise ValueError("All May 2020 rows must report 14 platform-live days.")
    complete = panel[panel["month"].ne(pd.Timestamp("2020-05-01"))]
    if not complete["platform_month_status"].eq("complete_month").all():
        raise ValueError("Every month after May 2020 must be marked complete_month.")
    if not complete["platform_live_days"].eq(complete["month"].dt.days_in_month).all():
        raise ValueError("Complete months must report all calendar days as live.")

    nonnegative_columns = [
        "platform_live_days",
        "current_inventory_trees",
        "recorded_watered_trees",
        "recorded_watering_events",
        "recorded_litres",
        "recorded_reach_pct_current_inventory",
        "recorded_events_per_1000_current_inventory_trees",
        "recorded_litres_per_current_inventory_tree",
    ]
    for column in nonnegative_columns:
        observed_values = pd.to_numeric(panel[column], errors="coerce").dropna()
        if observed_values.lt(0).any():
            raise ValueError(f"LOR-month panel contains a negative value in {column}.")


def _build_city_month(panel: Any, pd: Any, np: Any) -> Any:
    city = (
        panel.groupby(
            ["month", "platform_month_status", "platform_live_days"],
            as_index=False,
            observed=True,
        )
        .agg(
            current_inventory_trees=("current_inventory_trees", "sum"),
            recorded_watered_trees=("recorded_watered_trees", "sum"),
            recorded_watering_events=("recorded_watering_events", "sum"),
            recorded_litres=("recorded_litres", "sum"),
            planungsraeume_with_recorded_activity=(
                "recorded_watering_events",
                lambda values: int(values.gt(0).sum()),
            ),
            berlin_area_ha=("plr_area_ha", "sum"),
        )
    )
    denominator = city["current_inventory_trees"]
    city["recorded_reach_pct_current_inventory"] = np.where(
        denominator > 0,
        100 * city["recorded_watered_trees"] / denominator,
        np.nan,
    )
    city["recorded_events_per_1000_current_inventory_trees"] = np.where(
        denominator > 0,
        1000 * city["recorded_watering_events"] / denominator,
        np.nan,
    )
    city["recorded_litres_per_current_inventory_tree"] = np.where(
        denominator > 0,
        city["recorded_litres"] / denominator,
        np.nan,
    )
    city["recorded_litres_per_ha"] = city["recorded_litres"] / city["berlin_area_ha"]
    city["year"] = city["month"].dt.year
    city["calendar_month"] = city["month"].dt.month
    city["calendar_month_name"] = city["calendar_month"].map(
        lambda month: calendar.month_abbr[int(month)]
    )
    city["season"] = city["calendar_month"].map(season_for_month)
    city["complete_reference_year"] = city["year"].isin(REFERENCE_YEARS)
    city["active_season"] = city["calendar_month"].isin(ACTIVE_SEASON_MONTHS)
    city = city.sort_values("month").reset_index(drop=True)
    city["month"] = city["month"].dt.strftime("%Y-%m-%d")
    return city


def _build_calendar_lor(panel: Any, pd: Any) -> Any:
    reference = panel[panel["year"].isin(REFERENCE_YEARS)].copy()
    if len(reference) != 542 * 60:
        raise ValueError("The complete-year reference panel must contain 542 x 60 rows.")
    if not reference["platform_month_status"].eq("complete_month").all():
        raise ValueError("The 2021-2025 reference period contains a partial month.")

    group_keys = [
        "calendar_month",
        "plr_id",
        "plr_name",
        "bzr_id",
        "bzr_name",
        "district",
        "current_inventory_trees",
        "plr_area_ha",
    ]
    calendar_lor = (
        reference.groupby(group_keys, as_index=False, observed=True, dropna=False)
        .agg(
            observed_complete_years=("year", "nunique"),
            years_with_recorded_activity=(
                "recorded_watering_events",
                lambda values: int(values.gt(0).sum()),
            ),
            recorded_watered_tree_months=("recorded_watered_trees", "sum"),
            recorded_watering_events=("recorded_watering_events", "sum"),
            recorded_litres=("recorded_litres", "sum"),
            mean_monthly_recorded_watered_trees=("recorded_watered_trees", "mean"),
            median_monthly_recorded_watered_trees=("recorded_watered_trees", "median"),
            mean_monthly_recorded_reach_pct_current_inventory=(
                "recorded_reach_pct_current_inventory",
                "mean",
            ),
            median_monthly_recorded_reach_pct_current_inventory=(
                "recorded_reach_pct_current_inventory",
                "median",
            ),
            mean_monthly_recorded_events_per_1000_current_inventory_trees=(
                "recorded_events_per_1000_current_inventory_trees",
                "mean",
            ),
            median_monthly_recorded_events_per_1000_current_inventory_trees=(
                "recorded_events_per_1000_current_inventory_trees",
                "median",
            ),
            mean_monthly_recorded_litres_per_current_inventory_tree=(
                "recorded_litres_per_current_inventory_tree",
                "mean",
            ),
            median_monthly_recorded_litres_per_current_inventory_tree=(
                "recorded_litres_per_current_inventory_tree",
                "median",
            ),
            mean_monthly_recorded_litres_per_ha=("recorded_litres_per_ha", "mean"),
            median_monthly_recorded_litres_per_ha=("recorded_litres_per_ha", "median"),
        )
    )
    calendar_lor["calendar_month_name"] = calendar_lor["calendar_month"].map(
        lambda month: calendar.month_abbr[int(month)]
    )
    calendar_lor["season"] = calendar_lor["calendar_month"].map(season_for_month)
    calendar_lor["recorded_activity_persistence_pct"] = (
        100
        * calendar_lor["years_with_recorded_activity"]
        / calendar_lor["observed_complete_years"]
    )
    calendar_lor["mean_monthly_recorded_watering_events"] = (
        calendar_lor["recorded_watering_events"]
        / calendar_lor["observed_complete_years"]
    )
    calendar_lor["mean_monthly_recorded_litres"] = (
        calendar_lor["recorded_litres"] / calendar_lor["observed_complete_years"]
    )
    if len(calendar_lor) != 542 * 12:
        raise ValueError("Calendar-month climatology must contain 542 x 12 rows.")
    if not calendar_lor["observed_complete_years"].eq(5).all():
        raise ValueError("Every climatology cell must use exactly five complete years.")
    columns = [
        "calendar_month",
        "calendar_month_name",
        "season",
        "plr_id",
        "plr_name",
        "bzr_id",
        "bzr_name",
        "district",
        "observed_complete_years",
        "years_with_recorded_activity",
        "recorded_activity_persistence_pct",
        "current_inventory_trees",
        "plr_area_ha",
        "recorded_watered_tree_months",
        "recorded_watering_events",
        "recorded_litres",
        "mean_monthly_recorded_watered_trees",
        "median_monthly_recorded_watered_trees",
        "mean_monthly_recorded_watering_events",
        "mean_monthly_recorded_litres",
        "mean_monthly_recorded_reach_pct_current_inventory",
        "median_monthly_recorded_reach_pct_current_inventory",
        "mean_monthly_recorded_events_per_1000_current_inventory_trees",
        "median_monthly_recorded_events_per_1000_current_inventory_trees",
        "mean_monthly_recorded_litres_per_current_inventory_tree",
        "median_monthly_recorded_litres_per_current_inventory_tree",
        "mean_monthly_recorded_litres_per_ha",
        "median_monthly_recorded_litres_per_ha",
    ]
    return calendar_lor[columns].sort_values(
        ["calendar_month", "plr_id"]
    ).reset_index(drop=True)


def _build_city_summaries(city_month: Any, pd: Any) -> tuple[Any, Any]:
    parsed = city_month.copy()
    parsed["month"] = pd.to_datetime(parsed["month"])
    reference = parsed[parsed["year"].isin(REFERENCE_YEARS)].copy()
    calendar_city = (
        reference.groupby(
            ["calendar_month", "calendar_month_name", "season"],
            as_index=False,
            observed=True,
        )
        .agg(
            observed_complete_years=("year", "nunique"),
            recorded_watered_tree_months=("recorded_watered_trees", "sum"),
            recorded_watering_events=("recorded_watering_events", "sum"),
            recorded_litres=("recorded_litres", "sum"),
            mean_monthly_recorded_watered_trees=("recorded_watered_trees", "mean"),
            mean_monthly_recorded_watering_events=("recorded_watering_events", "mean"),
            mean_monthly_recorded_litres=("recorded_litres", "mean"),
            mean_monthly_planungsraeume_with_recorded_activity=(
                "planungsraeume_with_recorded_activity",
                "mean",
            ),
            mean_monthly_recorded_events_per_1000_current_inventory_trees=(
                "recorded_events_per_1000_current_inventory_trees",
                "mean",
            ),
            mean_monthly_recorded_litres_per_current_inventory_tree=(
                "recorded_litres_per_current_inventory_tree",
                "mean",
            ),
            mean_monthly_recorded_litres_per_ha=("recorded_litres_per_ha", "mean"),
        )
    )
    calendar_city["share_of_reference_period_recorded_events"] = (
        calendar_city["recorded_watering_events"]
        / calendar_city["recorded_watering_events"].sum()
    )
    calendar_city["share_of_reference_period_recorded_litres"] = (
        calendar_city["recorded_litres"] / calendar_city["recorded_litres"].sum()
    )
    calendar_city = calendar_city.sort_values("calendar_month").reset_index(drop=True)

    season = (
        reference.groupby("season", as_index=False, observed=True)
        .agg(
            observed_complete_years=("year", "nunique"),
            observed_complete_months=("month", "nunique"),
            current_inventory_trees=("current_inventory_trees", "first"),
            berlin_area_ha=("berlin_area_ha", "first"),
            recorded_watered_tree_months=("recorded_watered_trees", "sum"),
            recorded_watering_events=("recorded_watering_events", "sum"),
            recorded_litres=("recorded_litres", "sum"),
            mean_recorded_watering_events_per_observed_month=(
                "recorded_watering_events",
                "mean",
            ),
            mean_recorded_litres_per_observed_month=("recorded_litres", "mean"),
            mean_planungsraeume_with_recorded_activity=(
                "planungsraeume_with_recorded_activity",
                "mean",
            ),
            mean_recorded_events_per_1000_current_inventory_trees_per_observed_month=(
                "recorded_events_per_1000_current_inventory_trees",
                "mean",
            ),
            mean_recorded_litres_per_current_inventory_tree_per_observed_month=(
                "recorded_litres_per_current_inventory_tree",
                "mean",
            ),
            mean_recorded_litres_per_ha_per_observed_month=(
                "recorded_litres_per_ha",
                "mean",
            ),
        )
    )
    season["mean_annual_season_recorded_events_per_1000_current_inventory_trees"] = (
        1000
        * season["recorded_watering_events"]
        / (season["current_inventory_trees"] * season["observed_complete_years"])
    )
    season["mean_annual_season_recorded_litres_per_current_inventory_tree"] = (
        season["recorded_litres"]
        / (season["current_inventory_trees"] * season["observed_complete_years"])
    )
    season["mean_annual_season_recorded_litres_per_ha"] = (
        season["recorded_litres"]
        / (season["berlin_area_ha"] * season["observed_complete_years"])
    )
    season["share_of_reference_period_recorded_events"] = (
        season["recorded_watering_events"] / season["recorded_watering_events"].sum()
    )
    season["share_of_reference_period_recorded_litres"] = (
        season["recorded_litres"] / season["recorded_litres"].sum()
    )
    order = {value: index for index, value in enumerate(SEASON_ORDER)}
    season["_order"] = season["season"].map(order)
    season = season.sort_values("_order").drop(columns="_order").reset_index(drop=True)
    return calendar_city, season


def _build_year_summary(panel: Any, city_month: Any) -> Any:
    """Describe exposure availability by actual year, without outcome selection."""

    reference = panel[panel["year"].isin(REFERENCE_YEARS)]
    summary = reference.groupby("year", as_index=False, observed=True).agg(
        observed_complete_months=("month", "nunique"),
        observed_planungsraeume=("plr_id", "nunique"),
        recorded_watering_events=("recorded_watering_events", "sum"),
        recorded_litres=("recorded_litres", "sum"),
        recorded_watered_tree_months=("recorded_watered_trees", "sum"),
        lor_months_with_recorded_activity=(
            "recorded_watering_events", lambda values: int(values.gt(0).sum())
        ),
    )
    active_lor = (
        reference.loc[reference["recorded_watering_events"].gt(0)]
        .groupby("year")["plr_id"].nunique()
    )
    summary["planungsraeume_with_recorded_activity"] = (
        summary["year"].map(active_lor).fillna(0).astype(int)
    )
    summary["share_of_lor_months_with_recorded_activity"] = (
        summary["lor_months_with_recorded_activity"]
        / (summary["observed_planungsraeume"] * summary["observed_complete_months"])
    )
    city_reference = city_month[city_month["year"].isin(REFERENCE_YEARS)]
    peaks = city_reference.loc[
        city_reference.groupby("year")["recorded_watering_events"].idxmax(),
        ["year", "month", "recorded_watering_events"],
    ].rename(columns={
        "month": "peak_recorded_event_month",
        "recorded_watering_events": "peak_month_recorded_watering_events",
    })
    return summary.merge(peaks, on="year", validate="one_to_one").sort_values("year")


def _legend_labels(breaks: tuple[float, ...]) -> list[str]:
    def formatted(value: float) -> str:
        if value < 1:
            return f"{value:.2f}"
        if value < 10:
            return f"{value:.1f}"
        return f"{value:.0f}"

    labels = ["No recorded activity"]
    labels.append(f">0 to {formatted(breaks[0])}")
    for lower, upper in zip(breaks[:-1], breaks[1:]):
        labels.append(f">{formatted(lower)} to {formatted(upper)}")
    labels.append(f">{formatted(breaks[-1])}")
    labels.append("No current-inventory denominator")
    return labels


def _plot_choropleth(
    frame: Any,
    *,
    metric: str,
    breaks: tuple[float, ...],
    ax: Any,
) -> None:
    classes = frame[metric].map(lambda value: classify_map_value(value, breaks))
    colors = [MAP_COLORS[int(value)] for value in classes]
    frame.plot(color=colors, edgecolor="#ffffff", linewidth=0.13, ax=ax)
    frame.boundary.plot(color="#4d4d4d", linewidth=0.08, ax=ax)
    ax.set_axis_off()


def _save_figure(figure: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=220, bbox_inches="tight", format="png")
    temporary.replace(path)


def _write_timing_figure(city_month: Any, path: Path, pd: Any, np: Any) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Patch

    timeline = city_month.copy()
    timeline["month"] = pd.to_datetime(timeline["month"])
    colors = np.where(
        timeline["calendar_month"].isin((6, 7, 8)),
        "#2b8cbe",
        np.where(timeline["active_season"], "#7bccc4", "#d9d9d9"),
    )
    figure, axes = plt.subplots(2, 1, figsize=(15, 9.5), height_ratios=(1.1, 1))
    axes[0].bar(timeline["month"], timeline["recorded_watering_events"], width=25, color=colors)
    partial = timeline["platform_month_status"].ne("complete_month")
    axes[0].bar(
        timeline.loc[partial, "month"],
        timeline.loc[partial, "recorded_watering_events"],
        width=25,
        facecolor="none",
        edgecolor="#333333",
        hatch="////",
        linewidth=0.8,
    )
    axes[0].set_ylabel("Recorded watering events")
    axes[0].set_title("Monthly recorded activity")
    axes[0].set_xlim(
        timeline["month"].min() - pd.Timedelta(days=15),
        timeline["month"].max() + pd.Timedelta(days=20),
    )
    axes[0].grid(axis="y", alpha=0.22)
    axes[0].legend(
        handles=[
            Patch(facecolor="#2b8cbe", label="June–August"),
            Patch(facecolor="#7bccc4", label="April–May / September"),
            Patch(facecolor="#d9d9d9", label="October–March"),
        ],
        frameon=False,
        ncols=3,
        loc="upper right",
    )

    matrix = timeline.pivot(index="year", columns="calendar_month", values="recorded_watering_events")
    matrix = matrix.reindex(index=range(2020, 2026), columns=range(1, 13))
    log_values = np.log1p(matrix.to_numpy(dtype=float))
    cmap = LinearSegmentedColormap.from_list(
        "watering_activity", ["#f7fcfd", "#66c2a4", "#006d2c"]
    )
    cmap.set_bad("#bdbdbd")
    image = axes[1].imshow(log_values, aspect="auto", cmap=cmap, interpolation="nearest")
    axes[1].set_xticks(range(12), [calendar.month_abbr[i] for i in range(1, 13)])
    axes[1].set_yticks(range(6), range(2020, 2026))
    axes[1].set_xlabel("Europe/Berlin calendar month")
    axes[1].set_ylabel("Year")
    axes[1].set_title("Recorded events by year and month")
    axes[1].text(4, 0, "partial", ha="center", va="center", fontsize=8, color="#111111")
    raw_ticks = [0, 10, 100, 1000, 5000]
    colorbar = figure.colorbar(image, ax=axes[1], fraction=0.025, pad=0.025)
    colorbar.set_ticks(
        np.log1p(raw_ticks), labels=[f"{value:,}" for value in raw_ticks]
    )
    colorbar.set_label("Recorded watering events (log colour scale)")
    figure.suptitle(
        "Recorded citizen watering by local month, May 2020–December 2025",
        fontsize=16,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.012,
        "May 2020 is a 14-day partial platform month. Grey heatmap cells precede platform launch; zeros mean no recorded platform activity.",
        ha="center",
        fontsize=9,
        color="#444444",
    )
    figure.tight_layout(rect=(0, 0.04, 1, 0.95))
    _save_figure(figure, path)
    plt.close(figure)


def _write_monthly_atlas(
    monthly_lor: Any,
    lor: Any,
    path: Path,
    breaks: tuple[float, ...],
    *,
    metric: str,
    title: str,
    legend_title: str,
    note: str,
    show_monthly_totals: bool = False,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    figure, axes = plt.subplots(3, 4, figsize=(15.5, 12.2))
    for month, ax in zip(range(1, 13), axes.flat):
        values = monthly_lor[monthly_lor["calendar_month"].eq(month)]
        mapped = lor.merge(values[["plr_id", metric]], on="plr_id", how="left", validate="one_to_one")
        _plot_choropleth(mapped, metric=metric, breaks=breaks, ax=ax)
        month_title = calendar.month_name[month]
        if show_monthly_totals:
            total = int(values["recorded_watering_events"].sum())
            active = int(values["recorded_watering_events"].gt(0).sum())
            month_title += f"\n{total:,} events · {active} active LORs"
        ax.set_title(month_title, fontsize=10.5, fontweight="bold")

    labels = _legend_labels(breaks)
    handles = [
        Patch(facecolor=color, edgecolor="#777777", linewidth=0.3, label=label)
        for color, label in zip(MAP_COLORS, labels)
    ]
    figure.legend(
        handles=handles,
        loc="lower center",
        ncols=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.018),
        title=legend_title,
    )
    figure.suptitle(
        title,
        fontsize=16,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.002,
        note,
        ha="center",
        fontsize=8.8,
        color="#444444",
    )
    figure.tight_layout(rect=(0, 0.105, 1, 0.955), h_pad=0.6, w_pad=0.3)
    _save_figure(figure, path)
    plt.close(figure)


def _write_calendar_atlas(
    calendar_lor: Any,
    lor: Any,
    path: Path,
    breaks: tuple[float, ...],
) -> None:
    _write_monthly_atlas(
        calendar_lor, lor, path, breaks,
        metric="mean_monthly_recorded_events_per_1000_current_inventory_trees",
        title="Calendar-month watering climatology across complete years 2021–2025",
        legend_title="Mean monthly recorded events per 1,000 current-inventory trees",
        note="Five-year descriptive mean; use dated exposure for cooling analysis. Zero does not exclude unlogged watering.",
    )


def _write_year_atlas(
    year_panel: Any,
    lor: Any,
    path: Path,
    breaks: tuple[float, ...],
    year: int,
) -> None:
    """Map twelve actual months, rejecting any mixed-year or incomplete plate."""

    if (
        len(year_panel) != len(lor) * 12
        or not year_panel["year"].eq(year).all()
        or set(year_panel["calendar_month"]) != set(range(1, 13))
        or year_panel.duplicated(["calendar_month", "plr_id"]).any()
        or set(year_panel["plr_id"]) != set(lor["plr_id"])
    ):
        raise ValueError(f"The {year} atlas requires one complete, unmixed year of LOR-months.")
    events = int(year_panel["recorded_watering_events"].sum())
    _write_monthly_atlas(
        year_panel, lor, path, breaks,
        metric="recorded_events_per_1000_current_inventory_trees",
        title=f"{year} | Monthly recorded watering\n{events:,} matched events across January–December",
        legend_title="Recorded events per 1,000 current-inventory trees · fixed scale for 2021–2025",
        note=f"Each panel contains only its month in {year}. Active LORs have ≥1 recorded event; zero does not exclude unlogged watering.",
        show_monthly_totals=True,
    )


def _write_active_season_atlas(
    panel: Any,
    lor: Any,
    path: Path,
    breaks: tuple[float, ...],
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    metric = "recorded_events_per_1000_current_inventory_trees"
    figure, axes = plt.subplots(5, 6, figsize=(17.5, 15.5))
    for row_index, year in enumerate(REFERENCE_YEARS):
        for column_index, month in enumerate(ACTIVE_SEASON_MONTHS):
            ax = axes[row_index, column_index]
            values = panel[panel["year"].eq(year) & panel["calendar_month"].eq(month)]
            mapped = lor.merge(values[["plr_id", metric]], on="plr_id", how="left", validate="one_to_one")
            _plot_choropleth(mapped, metric=metric, breaks=breaks, ax=ax)
            if row_index == 0:
                ax.set_title(calendar.month_abbr[month], fontsize=10.5, fontweight="bold")
            if column_index == 0:
                ax.text(
                    -0.06,
                    0.5,
                    str(year),
                    transform=ax.transAxes,
                    rotation=90,
                    va="center",
                    ha="right",
                    fontsize=10.5,
                    fontweight="bold",
                )

    labels = _legend_labels(breaks)
    handles = [
        Patch(facecolor=color, edgecolor="#777777", linewidth=0.3, label=label)
        for color, label in zip(MAP_COLORS, labels)
    ]
    figure.legend(
        handles=handles,
        loc="lower center",
        ncols=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.018),
        title="Recorded events per 1,000 current-inventory trees",
    )
    figure.suptitle(
        "Active-season recorded watering, complete calendar years 2021–2025",
        fontsize=16,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.002,
        "April–September contains 96.3% of matched events in the full observed window. All 30 panels use the same scale.",
        ha="center",
        fontsize=8.8,
        color="#444444",
    )
    figure.tight_layout(rect=(0.025, 0.095, 1, 0.96), h_pad=0.25, w_pad=0.12)
    _save_figure(figure, path)
    plt.close(figure)


def build_watering_temporal_atlas(
    root: Path,
    *,
    processed_dir: Path | None = None,
    output_dir: Path | None = None,
) -> WateringTemporalArtifacts:
    """Build comparable monthly summaries and static temporal atlas plates."""

    try:
        import geopandas as gpd
        import matplotlib  # noqa: F401
        import numpy as np
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - exercised by users
        raise RuntimeError(
            "The temporal atlas requires numpy, pandas, geopandas, and matplotlib. "
            "Install requirements-spatial.txt or the project[spatial] extra."
        ) from exc

    from .manifest import load_manifest
    from .paths import resolve_project_path

    root = root.expanduser().resolve()
    manifest = load_manifest(root)
    panel_spec = manifest.datasets["lor_month_recorded_watering_foundation"]
    lor_spec = manifest.datasets["lor_boundaries_2021"]
    panel_path = resolve_project_path(root, panel_spec.path or "")
    lor_path = resolve_project_path(root, lor_spec.path or "")
    for source in (panel_path, lor_path):
        if not source.is_file():
            raise FileNotFoundError(f"Required temporal-atlas input is missing: {source}")

    target = (processed_dir or root / "data/processed/temporal").expanduser().resolve()
    report_root = (
        output_dir or root / "output/03_spatial_equity_vulnerability"
    ).expanduser().resolve()
    calendar_lor_path = target / "lor_calendar_month_recorded_watering_2021_2025.csv"
    city_month_path = target / "berlin_month_recorded_watering_2020_2025.csv"
    city_calendar_path = target / "berlin_calendar_month_recorded_watering_2021_2025.csv"
    season_summary_path = target / "berlin_season_recorded_watering_2021_2025.csv"
    year_summary_path = target / "berlin_year_recorded_watering_2021_2025.csv"
    metadata_path = target / "watering_temporal_atlas_2020_2025.metadata.json"
    timing_figure_path = report_root / "figures/01_recorded_watering_monthly_timing.png"
    calendar_atlas_path = report_root / "maps/01_calendar_month_recorded_watering_atlas.png"
    active_season_atlas_path = report_root / "maps/02_active_season_recorded_watering_atlas.png"
    yearly_atlas_paths = tuple(
        report_root / f"maps/yearly/{year}_monthly_recorded_watering_atlas.png"
        for year in REFERENCE_YEARS
    )

    panel = pd.read_csv(
        panel_path,
        dtype={"plr_id": "string", "bzr_id": "string"},
    )
    panel["month"] = pd.to_datetime(panel["month"], errors="raise")
    _validate_panel(panel, pd)
    panel["year"] = panel["month"].dt.year
    panel["calendar_month"] = panel["month"].dt.month

    lor = gpd.read_file(
        lor_path,
        layer=lor_spec.expected_layer,
        columns=["plr_id", "geometry"],
    )
    analysis_crs = str(manifest.project["analysis_crs"])
    if str(lor.crs) != analysis_crs:
        lor = lor.to_crs(analysis_crs)
    lor["plr_id"] = lor["plr_id"].astype("string")
    if len(lor) != 542 or not lor["plr_id"].is_unique:
        raise ValueError("The LOR boundary layer is not the expected 542-unit vintage.")
    lor["plr_area_ha"] = lor.geometry.area / 10_000
    if not lor["plr_area_ha"].gt(0).all():
        raise ValueError("At least one Planungsraum has a non-positive area.")

    panel = panel.merge(
        lor[["plr_id", "plr_area_ha"]],
        on="plr_id",
        how="left",
        validate="many_to_one",
    )
    if panel["plr_area_ha"].isna().any():
        raise ValueError("At least one panel Planungsraum lacks a boundary match.")
    panel["recorded_litres_per_ha"] = panel["recorded_litres"] / panel["plr_area_ha"]

    city_month = _build_city_month(panel, pd, np)
    calendar_lor = _build_calendar_lor(panel, pd)
    city_calendar, season_summary = _build_city_summaries(city_month, pd)
    year_summary = _build_year_summary(panel, city_month)

    scale_reference = panel[
        panel["year"].isin(REFERENCE_YEARS)
        & panel["calendar_month"].isin(ACTIVE_SEASON_MONTHS)
    ]["recorded_events_per_1000_current_inventory_trees"]
    map_breaks = derive_shared_positive_breaks(scale_reference)

    _atomic_csv(calendar_lor, calendar_lor_path)
    _atomic_csv(city_month, city_month_path)
    _atomic_csv(city_calendar, city_calendar_path)
    _atomic_csv(season_summary, season_summary_path)
    _atomic_csv(year_summary, year_summary_path)
    table_dir = report_root / "tables"
    _atomic_csv(calendar_lor, table_dir / calendar_lor_path.name)
    _atomic_csv(city_month, table_dir / city_month_path.name)
    _atomic_csv(city_calendar, table_dir / city_calendar_path.name)
    _atomic_csv(season_summary, table_dir / season_summary_path.name)
    _atomic_csv(year_summary, table_dir / year_summary_path.name)

    _write_timing_figure(city_month, timing_figure_path, pd, np)
    _write_calendar_atlas(calendar_lor, lor, calendar_atlas_path, map_breaks)
    _write_active_season_atlas(panel, lor, active_season_atlas_path, map_breaks)
    for year, path in zip(REFERENCE_YEARS, yearly_atlas_paths):
        _write_year_atlas(panel.loc[panel["year"].eq(year)], lor, path, map_breaks, year)

    all_events = float(city_month["recorded_watering_events"].sum())
    all_litres = float(city_month["recorded_litres"].sum())
    summer = city_month[city_month["calendar_month"].isin((6, 7, 8))]
    care_season = city_month[city_month["calendar_month"].isin((5, 6, 7, 8, 9))]
    active = city_month[city_month["calendar_month"].isin(ACTIVE_SEASON_MONTHS)]
    class_labels = _legend_labels(map_breaks)
    metadata: dict[str, Any] = {
        "schema_version": 2,
        "dataset_id": "watering_temporal_atlas_2020_2025",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "grains": {
            "city_month": "berlin_month",
            "calendar_climatology": "planungsraum_calendar_month_complete_year_mean",
            "season_summary": "berlin_meteorological_season_pooled_2021_2025",
            "year_summary": "berlin_calendar_year",
            "yearly_atlas": "planungsraum_actual_year_month",
        },
        "coverage": {
            "observed_start": "2020-05-01",
            "observed_end": "2025-12-31",
            "calendar_timezone": str(manifest.project["timezone"]),
            "climatology_complete_years": list(REFERENCE_YEARS),
            "active_season_months": list(ACTIVE_SEASON_MONTHS),
            "yearly_atlas_years": list(REFERENCE_YEARS),
            "yearly_atlas_months_per_year": list(range(1, 13)),
            "partial_month_retained_in_timeline": "2020-05",
            "partial_month_excluded_from_climatology": True,
        },
        "inputs": {
            "lor_month_panel": {
                "path": _relative_or_absolute(panel_path, root),
                "sha256": _sha256(panel_path),
            },
            "lor_boundaries": {
                "path": _relative_or_absolute(lor_path, root),
                "sha256": _sha256(lor_path),
                "analysis_crs": analysis_crs,
            },
        },
        "audit": {
            "source_lor_month_rows": int(len(panel)),
            "calendar_lor_rows": int(len(calendar_lor)),
            "city_month_rows": int(len(city_month)),
            "yearly_atlas_panels": len(REFERENCE_YEARS) * 12,
            "yearly_atlas_lor_months": int(panel["year"].isin(REFERENCE_YEARS).sum()),
            "matched_recorded_events": int(all_events),
            "matched_recorded_litres": all_litres,
            "reference_period_recorded_events": int(city_calendar["recorded_watering_events"].sum()),
            "reference_period_recorded_litres": float(city_calendar["recorded_litres"].sum()),
            "share_of_events_june_august": float(summer["recorded_watering_events"].sum() / all_events),
            "share_of_litres_june_august": float(summer["recorded_litres"].sum() / all_litres),
            "share_of_events_may_september": float(care_season["recorded_watering_events"].sum() / all_events),
            "share_of_litres_may_september": float(care_season["recorded_litres"].sum() / all_litres),
            "share_of_events_april_september": float(active["recorded_watering_events"].sum() / all_events),
            "share_of_litres_april_september": float(active["recorded_litres"].sum() / all_litres),
            "zero_recorded_event_lor_months": int(panel["recorded_watering_events"].eq(0).sum()),
            "planungsraeume_never_recording_an_event": int(
                panel.groupby("plr_id")["recorded_watering_events"].sum().eq(0).sum()
            ),
            "planungsraeume_without_current_inventory_denominator": int(
                panel.groupby("plr_id")["current_inventory_trees"].first().eq(0).sum()
            ),
        },
        "map_scale": {
            "metric": "recorded_events_per_1000_current_inventory_trees",
            "reference": "Positive Planungsraum-month observations in April-September 2021-2025",
            "positive_break_quantiles": list(POSITIVE_BREAK_QUANTILES),
            "positive_break_values": list(map_breaks),
            "class_labels": class_labels,
            "class_colors": list(MAP_COLORS),
            "fixed_across_all_panels": True,
            "zero_class": "No recorded platform activity",
            "missing_class": "No current-inventory denominator",
        },
        "semantics": {
            "recorded_zero": "No Gieß den Kiez platform activity was recorded for that Planungsraum-month; municipal, private, and unlogged watering remain unobserved.",
            "denominator_caveat": "Current-inventory-normalised rates do not use a historical monthly eligible-tree risk set.",
            "area_density_definition": "Recorded litres per hectare divide logged litres by the full Planungsraum or Berlin polygon area in EPSG:25833. This is a spatial density for description, not an irrigation application dose to watered soil or canopy.",
            "climatology": "A five-year calendar-month summary of recorded activity, not a climate normal.",
            "yearly_atlas": "Each plate uses only the twelve actual months in its labelled year. Values are not averaged or summed across years; all sixty panels use the same classification scale.",
            "temporal_alignment": "Cooling analysis must join spatial support to actual acquisition dates and strictly preceding dated watering windows. Never join exposure and outcomes by calendar month alone or substitute pooled climatology for dated exposure.",
            "year_selection": "Year summaries describe recorded exposure availability, not logging completeness or thermal detectability. Choose eligible years using pre-outcome rules for usable imagery, weather, logging coverage and dose variation; do not select a year because it produces an effect.",
            "watered_tree_months": "Distinct trees may recur across months or years; seasonal and multi-year sums are tree-month counts, not distinct-tree reach.",
            "claim_boundary": "These products describe temporal and spatial concentration of recorded activity. They do not estimate cooling, irrigation coverage, or causal effects.",
        },
        "outputs": {
            "calendar_lor": _relative_or_absolute(calendar_lor_path, root),
            "city_month": _relative_or_absolute(city_month_path, root),
            "city_calendar": _relative_or_absolute(city_calendar_path, root),
            "season_summary": _relative_or_absolute(season_summary_path, root),
            "year_summary": _relative_or_absolute(year_summary_path, root),
            "timing_figure": _relative_or_absolute(timing_figure_path, root),
            "calendar_atlas": _relative_or_absolute(calendar_atlas_path, root),
            "active_season_atlas": _relative_or_absolute(active_season_atlas_path, root),
            **{
                f"yearly_atlas_{year}": _relative_or_absolute(path, root)
                for year, path in zip(REFERENCE_YEARS, yearly_atlas_paths)
            },
            "sha256": {
                "calendar_lor": _sha256(calendar_lor_path),
                "city_month": _sha256(city_month_path),
                "city_calendar": _sha256(city_calendar_path),
                "season_summary": _sha256(season_summary_path),
                "year_summary": _sha256(year_summary_path),
                "timing_figure": _sha256(timing_figure_path),
                "calendar_atlas": _sha256(calendar_atlas_path),
                "active_season_atlas": _sha256(active_season_atlas_path),
                **{
                    f"yearly_atlas_{year}": _sha256(path)
                    for year, path in zip(REFERENCE_YEARS, yearly_atlas_paths)
                },
            },
        },
    }
    _atomic_json(metadata, metadata_path)

    return WateringTemporalArtifacts(
        calendar_lor_path=calendar_lor_path,
        city_month_path=city_month_path,
        city_calendar_path=city_calendar_path,
        season_summary_path=season_summary_path,
        year_summary_path=year_summary_path,
        metadata_path=metadata_path,
        timing_figure_path=timing_figure_path,
        calendar_atlas_path=calendar_atlas_path,
        active_season_atlas_path=active_season_atlas_path,
        yearly_atlas_paths=yearly_atlas_paths,
        calendar_lor_rows=int(len(calendar_lor)),
        city_month_rows=int(len(city_month)),
        map_breaks=map_breaks,
    )
