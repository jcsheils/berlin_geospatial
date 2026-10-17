"""Build canonical positive recorded-watering tree-day temporal products."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


AGE_BAND_ORDER = (
    "0-9",
    "10-19",
    "20-39",
    "40-59",
    "60+",
    "unknown",
)
COMPLETE_PROFILE_YEARS = tuple(range(2021, 2026))


@dataclass(frozen=True)
class RecordedTreeDayArtifacts:
    """Paths and headline counts produced by a recorded-tree-day build."""

    tree_day_path: Path
    age_summary_path: Path
    genus_summary_path: Path
    metadata_path: Path
    figure_path: Path
    age_table_path: Path
    genus_table_path: Path
    tree_day_rows: int
    matched_events: int
    matched_litres: float
    unique_trees: int


def assign_age_band(age: object) -> str:
    """Assign a non-negative age to the locked, no-gap age bands.

    Missing, non-numeric, non-finite, negative, and implausibly old values are
    labelled ``unknown``. Within the validated 0--250 range, the upper display
    band is open-ended from age 60.
    """

    try:
        value = float(age)
    except (TypeError, ValueError):
        return "unknown"
    if not math.isfinite(value) or value < 0 or value > 250:
        return "unknown"
    if value < 10:
        return "0-9"
    if value < 20:
        return "10-19"
    if value < 40:
        return "20-39"
    if value < 60:
        return "40-59"
    return "60+"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _clean_text(series: Any) -> Any:
    cleaned = series.astype("string").str.strip()
    return cleaned.mask(cleaned.eq(""))


def _deterministic_mode(values: Any) -> Any:
    """Return the most common non-missing value, breaking ties lexically."""

    observed = values.dropna()
    if observed.empty:
        return None
    counts = observed.value_counts(dropna=True)
    tied = list(counts[counts.eq(counts.max())].index)
    return sorted(tied, key=lambda value: str(value).casefold())[0]


def _attribute_conflicts(events: Any, columns: Iterable[str]) -> dict[str, int]:
    conflicts: dict[str, int] = {}
    for column in columns:
        distinct = events.groupby("tree_id", observed=True)[column].nunique(dropna=True)
        conflicts[column] = int(distinct.gt(1).sum())
    return conflicts


def _build_temporal_summary(
    tree_day: Any,
    *,
    group_column: str,
    groups: list[str],
    pd: Any,
) -> Any:
    complete = tree_day[tree_day["year"].isin(COMPLETE_PROFILE_YEARS)].copy()
    yearly = complete.groupby(
        [group_column, "year", "calendar_month"],
        observed=True,
        as_index=False,
    ).agg(
        recorded_watering_days=("tree_id", "size"),
        recorded_watering_events=("recorded_watering_events", "sum"),
        recorded_litres=("recorded_litres", "sum"),
        unique_recorded_watered_trees=("tree_id", "nunique"),
    )

    full_index = pd.MultiIndex.from_product(
        [groups, COMPLETE_PROFILE_YEARS, range(1, 13)],
        names=[group_column, "year", "calendar_month"],
    )
    yearly = (
        yearly.set_index([group_column, "year", "calendar_month"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    summary = yearly.groupby([group_column, "calendar_month"], as_index=False).agg(
        recorded_watering_days=("recorded_watering_days", "sum"),
        recorded_watering_events=("recorded_watering_events", "sum"),
        recorded_litres=("recorded_litres", "sum"),
        mean_recorded_watering_days_per_year=(
            "recorded_watering_days",
            "mean",
        ),
        mean_recorded_watering_events_per_year=(
            "recorded_watering_events",
            "mean",
        ),
        mean_recorded_litres_per_year=("recorded_litres", "mean"),
        mean_unique_recorded_watered_trees_per_year=(
            "unique_recorded_watered_trees",
            "mean",
        ),
    )
    unique_across_years = complete.groupby(
        [group_column, "calendar_month"],
        observed=True,
        as_index=False,
    ).agg(unique_recorded_watered_trees=("tree_id", "nunique"))
    summary = summary.merge(
        unique_across_years,
        on=[group_column, "calendar_month"],
        how="left",
        validate="one_to_one",
    )
    summary["unique_recorded_watered_trees"] = (
        summary["unique_recorded_watered_trees"].fillna(0).astype("int64")
    )
    summary["observed_complete_years"] = len(COMPLETE_PROFILE_YEARS)
    summary["calendar_month_name"] = summary["calendar_month"].map(
        lambda month: calendar.month_abbr[int(month)]
    )

    share_fields = {
        "recorded_watering_days": "within_group_recorded_watering_day_share",
        "recorded_watering_events": "within_group_recorded_watering_event_share",
        "recorded_litres": "within_group_recorded_litre_share",
    }
    for value_column, share_column in share_fields.items():
        denominator = summary.groupby(group_column)[value_column].transform("sum")
        summary[share_column] = summary[value_column].div(
            denominator.where(denominator.gt(0))
        )

    if group_column == "age_band":
        order = {value: index for index, value in enumerate(AGE_BAND_ORDER)}
        summary["_group_order"] = summary[group_column].map(order)
        summary = summary.sort_values(["_group_order", "calendar_month"])
        summary = summary.drop(columns="_group_order")
    else:
        summary["_group_order"] = summary[group_column].str.casefold()
        summary = summary.sort_values(["_group_order", "calendar_month"])
        summary = summary.drop(columns="_group_order")

    columns = [
        group_column,
        "calendar_month",
        "calendar_month_name",
        "observed_complete_years",
        "recorded_watering_days",
        "recorded_watering_events",
        "recorded_litres",
        "unique_recorded_watered_trees",
        "mean_recorded_watering_days_per_year",
        "mean_recorded_watering_events_per_year",
        "mean_recorded_litres_per_year",
        "mean_unique_recorded_watered_trees_per_year",
        "within_group_recorded_watering_day_share",
        "within_group_recorded_watering_event_share",
        "within_group_recorded_litre_share",
    ]
    return summary[columns].reset_index(drop=True)


def _write_timing_figure(
    age_summary: Any,
    genus_summary: Any,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(16, 6.8))

    colors = {
        "0-9": "#1b9e77",
        "10-19": "#66a61e",
        "20-39": "#1f78b4",
        "40-59": "#7570b3",
        "60+": "#d95f02",
        "unknown": "#777777",
    }
    for age_band in AGE_BAND_ORDER:
        values = age_summary[age_summary["age_band"].eq(age_band)]
        axes[0].plot(
            values["calendar_month"],
            100 * values["within_group_recorded_watering_day_share"],
            marker="o",
            linewidth=1.5 if age_band == "unknown" else 2,
            markersize=4,
            label=age_band,
            color=colors[age_band],
            linestyle="--" if age_band == "unknown" else "-",
        )
    axes[0].set_xticks(range(1, 13), [calendar.month_abbr[i] for i in range(1, 13)])
    axes[0].set_ylabel("Share of each age band's recorded watering days (%)")
    axes[0].set_title("Seasonal timing by age at watering")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend(title="Age band (years)", frameon=False, ncols=2)

    genus_totals = (
        genus_summary.groupby("genus", as_index=False)["recorded_watering_days"]
        .sum()
        .sort_values(["recorded_watering_days", "genus"], ascending=[False, True])
    )
    known = genus_totals[~genus_totals["genus"].str.casefold().eq("unknown")]
    top_genera = known.head(12)["genus"].tolist()
    heat = (
        genus_summary[genus_summary["genus"].isin(top_genera)]
        .pivot(
            index="genus",
            columns="calendar_month",
            values="within_group_recorded_watering_day_share",
        )
        .reindex(index=top_genera, columns=range(1, 13))
    )
    image = axes[1].imshow(
        100 * heat.to_numpy(dtype=float),
        aspect="auto",
        cmap="YlGnBu",
        interpolation="nearest",
    )
    axes[1].set_xticks(range(12), [calendar.month_abbr[i] for i in range(1, 13)])
    axes[1].set_yticks(range(len(top_genera)), top_genera)
    axes[1].set_title("Seasonal timing for the 12 most-recorded genera")
    colorbar = figure.colorbar(image, ax=axes[1], fraction=0.046, pad=0.04)
    colorbar.set_label("Share of each genus's recorded watering days (%)")

    figure.suptitle(
        "Recorded citizen-watering timing, complete calendar years 2021–2025",
        fontsize=15,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.015,
        "Positive Gieß den Kiez records only; absence of a record is not absence of watering.",
        ha="center",
        fontsize=9,
        color="#444444",
    )
    figure.tight_layout(rect=(0, 0.045, 1, 0.94))

    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=220, bbox_inches="tight", format="png")
    plt.close(figure)
    temporary.replace(path)


def build_recorded_tree_day(
    root: Path,
    *,
    processed_dir: Path | None = None,
    output_dir: Path | None = None,
) -> RecordedTreeDayArtifacts:
    """Build positive tree-day watering data and complete-year timing profiles."""

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - exercised by users
        raise RuntimeError(
            "The recorded-tree-day build requires pandas and matplotlib. "
            "Install requirements-spatial.txt or the project[spatial] extra."
        ) from exc

    from .manifest import load_manifest
    from .paths import resolve_project_path

    root = root.expanduser().resolve()
    manifest = load_manifest(root)
    project = manifest.project
    watering_spec = manifest.datasets["recorded_watering_events"]
    watering_path = resolve_project_path(root, watering_spec.path or "")
    crosswalk_path = (
        root / "data/processed/foundation/recorded_tree_lor_crosswalk_2020_2025.csv"
    )
    for source in (watering_path, crosswalk_path):
        if not source.is_file():
            raise FileNotFoundError(
                f"Required recorded-tree-day input is missing: {source}"
            )

    target = (processed_dir or root / "data/processed/temporal").expanduser().resolve()
    report_root = (
        (output_dir or root / "output/03_spatial_equity_vulnerability")
        .expanduser()
        .resolve()
    )
    tree_day_path = target / "recorded_tree_day_watering_2020_2025.csv"
    age_summary_path = target / "recorded_watering_timing_by_age_band_2021_2025.csv"
    genus_summary_path = target / "recorded_watering_timing_by_genus_2021_2025.csv"
    metadata_path = target / "recorded_tree_day_watering_2020_2025.metadata.json"
    figure_path = (
        report_root / "figures/02_recorded_watering_timing_by_tree_age_genus.png"
    )
    age_table_path = (
        report_root / "tables/recorded_watering_timing_by_age_band_2021_2025.csv"
    )
    genus_table_path = (
        report_root / "tables/recorded_watering_timing_by_genus_2021_2025.csv"
    )

    raw = pd.read_csv(
        watering_path,
        sep=watering_spec.delimiter,
        dtype={"id": "string"},
        low_memory=False,
    )
    missing_columns = sorted(set(watering_spec.required_columns) - set(raw.columns))
    if missing_columns:
        raise ValueError(
            "Recorded watering input is missing columns: " + ", ".join(missing_columns)
        )
    raw_rows = int(len(raw))
    duplicate_rows = int(raw.duplicated(keep="first").sum())
    events = raw.drop_duplicates(keep="first").copy()
    events["tree_id"] = _clean_text(events["id"])
    events["timestamp_utc"] = pd.to_datetime(
        events["timestamp"], format="mixed", utc=True, errors="coerce"
    )
    invalid_timestamps = int(events["timestamp_utc"].isna().sum())

    local_timezone = str(project["timezone"])
    start_local = pd.Timestamp(
        str(project["recorded_watering_start"]), tz=local_timezone
    )
    end_local_exclusive = pd.Timestamp(
        str(project["complete_recorded_watering_end_exclusive"]),
        tz=local_timezone,
    )
    start_utc = start_local.tz_convert("UTC")
    end_utc_exclusive = end_local_exclusive.tz_convert("UTC")
    events = events[
        events["timestamp_utc"].ge(start_utc)
        & events["timestamp_utc"].lt(end_utc_exclusive)
    ].copy()
    events["timestamp_local"] = events["timestamp_utc"].dt.tz_convert(local_timezone)
    events["local_date"] = events["timestamp_local"].dt.tz_localize(None).dt.normalize()

    events["recorded_litres"] = pd.to_numeric(
        events["bewaesserungsmenge_in_liter"], errors="coerce"
    )
    nonpositive_or_missing_litres = int((~events["recorded_litres"].gt(0)).sum())

    events["longitude"] = pd.to_numeric(events["lng"], errors="coerce")
    events["latitude"] = pd.to_numeric(events["lat"], errors="coerce")
    swapped = events["longitude"].between(52.3, 52.7) & events["latitude"].between(
        13.1, 13.8
    )
    reversed_values = events.loc[swapped, ["latitude", "longitude"]].to_numpy()
    events.loc[swapped, ["longitude", "latitude"]] = reversed_values
    valid_coordinate = events["longitude"].between(13.0, 14.0) & events[
        "latitude"
    ].between(52.3, 52.7)
    invalid_or_missing_coordinates = int((~valid_coordinate).sum())
    events.loc[~valid_coordinate, ["longitude", "latitude"]] = pd.NA

    events["species"] = _clean_text(events["art_dtsch"])
    events["genus"] = _clean_text(events["gattung_deutsch"])
    planting_numeric = pd.to_numeric(events["pflanzjahr"], errors="coerce")
    integer_planting = planting_numeric.where(
        planting_numeric.isna() | planting_numeric.mod(1).eq(0)
    )
    events["planting_year"] = integer_planting.round().astype("Int64")

    source_events_in_window = int(len(events))
    timestamp_midnight = events["timestamp_utc"].eq(
        events["timestamp_utc"].dt.normalize()
    )
    timestamp_precision_by_year = []
    for year, year_rows in events.assign(
        _local_year=events["timestamp_local"].dt.year
    ).groupby("_local_year", sort=True):
        midnight_count = int(timestamp_midnight.loc[year_rows.index].sum())
        timestamp_precision_by_year.append(
            {
                "year": int(year),
                "events": int(len(year_rows)),
                "events_at_exact_utc_midnight": midnight_count,
                "share_at_exact_utc_midnight": (
                    midnight_count / len(year_rows) if len(year_rows) else None
                ),
            }
        )

    positive = events[events["recorded_litres"].gt(0)].copy()
    crosswalk = pd.read_csv(crosswalk_path, dtype="string")
    required_crosswalk = [
        "tree_id",
        "plr_id",
        "plr_name",
        "bzr_id",
        "bzr_name",
        "district",
    ]
    missing_crosswalk = sorted(set(required_crosswalk) - set(crosswalk.columns))
    if missing_crosswalk:
        raise ValueError(
            "Recorded-tree crosswalk is missing columns: "
            + ", ".join(missing_crosswalk)
        )
    crosswalk["tree_id"] = _clean_text(crosswalk["tree_id"])
    if crosswalk["tree_id"].isna().any() or not crosswalk["tree_id"].is_unique:
        raise ValueError("Recorded-tree crosswalk must have unique, non-null tree IDs.")
    for column in required_crosswalk[1:]:
        crosswalk[column] = _clean_text(crosswalk[column])
    missing_geography_rows = crosswalk[required_crosswalk[1:]].isna().any(axis=1)
    if missing_geography_rows.any():
        raise ValueError(
            "Recorded-tree crosswalk contains "
            f"{int(missing_geography_rows.sum()):,} rows with incomplete geography."
        )

    matched = positive.merge(
        crosswalk[required_crosswalk],
        on="tree_id",
        how="inner",
        validate="many_to_one",
    )
    unmatched_positive_events = int(len(positive) - len(matched))
    unmatched_positive_litres = float(
        positive.loc[
            ~positive["tree_id"].isin(crosswalk["tree_id"]), "recorded_litres"
        ].sum()
    )

    conflict_columns = ["species", "genus", "planting_year"]
    attribute_conflicts = _attribute_conflicts(matched, conflict_columns)
    stable_attributes = matched.groupby("tree_id", observed=True, as_index=False).agg(
        species=("species", _deterministic_mode),
        genus=("genus", _deterministic_mode),
        planting_year=("planting_year", _deterministic_mode),
    )
    stable_attributes["species"] = stable_attributes["species"].fillna("unknown")
    stable_attributes["genus"] = stable_attributes["genus"].fillna("unknown")
    stable_attributes["planting_year"] = pd.to_numeric(
        stable_attributes["planting_year"], errors="coerce"
    ).astype("Int64")

    coordinate_rows = matched.dropna(subset=["longitude", "latitude"]).copy()
    coordinate_rows["coordinate_pair"] = list(
        zip(coordinate_rows["longitude"], coordinate_rows["latitude"])
    )
    coordinate_conflicts = int(
        coordinate_rows.groupby("tree_id", observed=True)["coordinate_pair"]
        .nunique()
        .gt(1)
        .sum()
    )
    stable_coordinates = coordinate_rows.groupby(
        "tree_id", observed=True, as_index=False
    ).agg(coordinate_pair=("coordinate_pair", _deterministic_mode))
    if stable_coordinates.empty:
        stable_coordinates["longitude"] = pd.Series(dtype="float64")
        stable_coordinates["latitude"] = pd.Series(dtype="float64")
    else:
        stable_coordinates[["longitude", "latitude"]] = pd.DataFrame(
            stable_coordinates["coordinate_pair"].tolist(),
            index=stable_coordinates.index,
        )
    stable_coordinates = stable_coordinates.drop(columns="coordinate_pair")

    source_repeated_day_sizes = positive.groupby(
        ["tree_id", "local_date"], observed=True
    ).size()
    source_tree_days_with_multiple_events = int(source_repeated_day_sizes.gt(1).sum())
    source_events_on_repeated_tree_days = int(
        source_repeated_day_sizes.loc[source_repeated_day_sizes.gt(1)].sum()
    )
    source_extra_events_on_repeated_tree_days = int(
        (source_repeated_day_sizes - 1).clip(lower=0).sum()
    )

    repeated_day_sizes = matched.groupby(
        ["tree_id", "local_date"], observed=True
    ).size()
    tree_days_with_multiple_events = int(repeated_day_sizes.gt(1).sum())
    events_on_repeated_tree_days = int(
        repeated_day_sizes.loc[repeated_day_sizes.gt(1)].sum()
    )
    extra_events_on_repeated_tree_days = int(
        (repeated_day_sizes - 1).clip(lower=0).sum()
    )
    maximum_events_on_one_tree_day = int(repeated_day_sizes.max())

    tree_day = (
        matched.groupby(
            [
                "tree_id",
                "local_date",
                "plr_id",
                "plr_name",
                "bzr_id",
                "bzr_name",
                "district",
            ],
            observed=True,
            as_index=False,
            dropna=False,
        )
        .agg(
            recorded_watering_events=("tree_id", "size"),
            recorded_litres=("recorded_litres", "sum"),
        )
        .merge(stable_attributes, on="tree_id", how="left", validate="many_to_one")
        .merge(stable_coordinates, on="tree_id", how="left", validate="many_to_one")
    )
    tree_day["year"] = tree_day["local_date"].dt.year.astype("int64")
    tree_day["calendar_month"] = tree_day["local_date"].dt.month.astype("int64")
    age = tree_day["year"] - tree_day["planting_year"]
    valid_age = (
        tree_day["planting_year"].notna()
        & tree_day["planting_year"].ge(1700)
        & age.between(0, 250)
    )
    tree_day["age_at_watering"] = age.where(valid_age).astype("Int64")
    tree_day["age_band"] = tree_day["age_at_watering"].map(assign_age_band)
    tree_day["multiple_logs_tree_day"] = tree_day["recorded_watering_events"].gt(1)
    tree_day["recorded_events_tree_day"] = tree_day["recorded_watering_events"]
    tree_day["recorded_litres_tree_day"] = tree_day["recorded_litres"]
    tree_day["recorded_exposure_semantics"] = "positive_recorded_platform_activity_only"
    tree_day["local_date"] = tree_day["local_date"].dt.strftime("%Y-%m-%d")
    tree_day = tree_day.sort_values(["local_date", "tree_id"]).reset_index(drop=True)
    tree_day = tree_day[
        [
            "tree_id",
            "local_date",
            "year",
            "calendar_month",
            "recorded_watering_events",
            "recorded_litres",
            "recorded_events_tree_day",
            "recorded_litres_tree_day",
            "multiple_logs_tree_day",
            "recorded_exposure_semantics",
            "longitude",
            "latitude",
            "species",
            "genus",
            "planting_year",
            "age_at_watering",
            "age_band",
            "plr_id",
            "plr_name",
            "bzr_id",
            "bzr_name",
            "district",
        ]
    ]

    if not tree_day["recorded_watering_events"].gt(0).all():
        raise ValueError("Tree-day product unexpectedly contains a zero-event row.")
    if not tree_day["recorded_litres"].gt(0).all():
        raise ValueError("Tree-day product unexpectedly contains a non-positive dose.")
    if tree_day.duplicated(["tree_id", "local_date"]).any():
        raise ValueError("Tree-day product does not have unique tree/date keys.")
    if int(tree_day["recorded_events_tree_day"].sum()) != int(len(matched)):
        raise ValueError("Tree-day event totals do not reconcile to matched events.")
    if not math.isclose(
        float(tree_day["recorded_litres_tree_day"].sum()),
        float(matched["recorded_litres"].sum()),
        rel_tol=0,
        abs_tol=1e-9,
    ):
        raise ValueError("Tree-day litre totals do not reconcile to matched litres.")

    age_groups = list(AGE_BAND_ORDER)
    genus_groups = sorted(
        tree_day.loc[tree_day["year"].isin(COMPLETE_PROFILE_YEARS), "genus"]
        .dropna()
        .unique(),
        key=lambda value: str(value).casefold(),
    )
    age_summary = _build_temporal_summary(
        tree_day,
        group_column="age_band",
        groups=age_groups,
        pd=pd,
    )
    genus_summary = _build_temporal_summary(
        tree_day,
        group_column="genus",
        groups=genus_groups,
        pd=pd,
    )

    _atomic_csv(tree_day, tree_day_path)
    _atomic_csv(age_summary, age_summary_path)
    _atomic_csv(genus_summary, genus_summary_path)
    _atomic_csv(age_summary, age_table_path)
    _atomic_csv(genus_summary, genus_table_path)
    _write_timing_figure(age_summary, genus_summary, figure_path)

    litres = matched["recorded_litres"]
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "dataset_id": "recorded_tree_day_watering_2020_2025",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "grain": "recorded_tree_local_calendar_day_positive_exposure",
        "coverage": {
            "start_inclusive": str(project["recorded_watering_start"]),
            "end_exclusive": str(project["complete_recorded_watering_end_exclusive"]),
            "timezone": local_timezone,
            "profile_complete_years": list(COMPLETE_PROFILE_YEARS),
            "first_period_status": "partial_platform_start",
        },
        "inputs": {
            "recorded_watering_events": {
                "path": str(watering_path.relative_to(root)),
                "sha256": _sha256(watering_path),
            },
            "recorded_tree_lor_crosswalk": {
                "path": str(crosswalk_path.relative_to(root)),
                "sha256": _sha256(crosswalk_path),
            },
        },
        "audit": {
            "raw_source_rows": raw_rows,
            "exact_duplicate_rows_removed": duplicate_rows,
            "invalid_timestamps_after_deduplication": invalid_timestamps,
            "deduplicated_events_in_window": source_events_in_window,
            "events_with_nonpositive_or_missing_litres_excluded": nonpositive_or_missing_litres,
            "positive_events_matched_to_assigned_trees": int(len(matched)),
            "positive_litres_matched_to_assigned_trees": float(litres.sum()),
            "unmatched_positive_events": unmatched_positive_events,
            "unmatched_positive_litres": unmatched_positive_litres,
            "unique_matched_trees": int(matched["tree_id"].nunique()),
            "tree_day_rows": int(len(tree_day)),
            "source_positive_tree_day_rows_before_matching": int(
                len(source_repeated_day_sizes)
            ),
            "source_tree_days_with_multiple_events_before_matching": (
                source_tree_days_with_multiple_events
            ),
            "source_events_on_repeated_tree_days_before_matching": (
                source_events_on_repeated_tree_days
            ),
            "source_extra_events_on_repeated_tree_days_before_matching": (
                source_extra_events_on_repeated_tree_days
            ),
            "tree_days_with_multiple_source_events": tree_days_with_multiple_events,
            "source_events_on_repeated_tree_days": events_on_repeated_tree_days,
            "extra_events_on_repeated_tree_days": extra_events_on_repeated_tree_days,
            "maximum_events_on_one_tree_day": maximum_events_on_one_tree_day,
            "coordinate_pairs_reversed": int(swapped.sum()),
            "events_with_invalid_or_missing_coordinate_after_repair": invalid_or_missing_coordinates,
            "tree_ids_with_multiple_valid_coordinate_pairs": coordinate_conflicts,
            "tree_days_without_a_valid_stable_coordinate": int(
                tree_day["longitude"].isna().sum()
            ),
            "stable_attribute_conflicting_tree_ids": attribute_conflicts,
            "stable_attribute_missing_tree_ids": {
                "species": int(stable_attributes["species"].eq("unknown").sum()),
                "genus": int(stable_attributes["genus"].eq("unknown").sum()),
                "planting_year": int(stable_attributes["planting_year"].isna().sum()),
            },
            "timestamp_precision_by_local_year": timestamp_precision_by_year,
            "litre_outliers": {
                "events_above_500_litres": int(litres.gt(500).sum()),
                "events_above_1000_litres": int(litres.gt(1000).sum()),
                "minimum_litres": float(litres.min()),
                "median_litres": float(litres.median()),
                "p95_litres": float(litres.quantile(0.95)),
                "p99_litres": float(litres.quantile(0.99)),
                "maximum_litres": float(litres.max()),
            },
            "profile_rows": {
                "age_band_month": int(len(age_summary)),
                "genus_month": int(len(genus_summary)),
                "genera": int(len(genus_groups)),
            },
        },
        "methods": {
            "deduplication": "Exact source-row duplicates are removed before filtering.",
            "tree_day": "Positive matched events are summed by assigned tree ID and Europe/Berlin local date.",
            "stable_attributes": "Species, genus, planting year, and valid coordinates use the most frequent non-missing value per tree; ties are resolved lexically.",
            "age": "Age at watering is local calendar year minus planting year; ages outside 0-250 and missing planting years yield unknown age.",
            "age_bands": list(AGE_BAND_ORDER),
            "metric_aliases": {
                "recorded_events_tree_day": "recorded_watering_events",
                "recorded_litres_tree_day": "recorded_litres",
            },
            "profiles": "Age and genus profiles contain every calendar month for complete years 2021-2025; means use five annual observations including zeros.",
        },
        "semantics": {
            "positive_rows_only": "Every tree-day row contains at least one positive recorded Gieß den Kiez event; structurally absent tree-days are not materialised as zero rows.",
            "recorded_zero": "Absence from this positive-exposure table means no platform event is represented; it does not mean no municipal, private, or unlogged watering occurred.",
            "watering_day": "A recorded watering day is one unique assigned tree ID by Europe/Berlin local calendar date, regardless of how many source events were logged that day.",
            "claim_boundary": "The products describe timing and composition of recorded platform activity. They do not estimate irrigation coverage, volunteer behaviour, tree-level cooling, or causal temperature effects.",
        },
        "outputs": {
            "tree_day": str(tree_day_path.relative_to(root))
            if tree_day_path.is_relative_to(root)
            else str(tree_day_path),
            "age_summary": str(age_summary_path.relative_to(root))
            if age_summary_path.is_relative_to(root)
            else str(age_summary_path),
            "genus_summary": str(genus_summary_path.relative_to(root))
            if genus_summary_path.is_relative_to(root)
            else str(genus_summary_path),
            "metadata": str(metadata_path.relative_to(root))
            if metadata_path.is_relative_to(root)
            else str(metadata_path),
            "figure": str(figure_path.relative_to(root))
            if figure_path.is_relative_to(root)
            else str(figure_path),
            "human_facing_age_table": str(age_table_path.relative_to(root))
            if age_table_path.is_relative_to(root)
            else str(age_table_path),
            "human_facing_genus_table": str(genus_table_path.relative_to(root))
            if genus_table_path.is_relative_to(root)
            else str(genus_table_path),
            "sha256": {
                "tree_day": _sha256(tree_day_path),
                "age_summary": _sha256(age_summary_path),
                "genus_summary": _sha256(genus_summary_path),
                "figure": _sha256(figure_path),
                "human_facing_age_table": _sha256(age_table_path),
                "human_facing_genus_table": _sha256(genus_table_path),
            },
        },
    }
    _atomic_json(metadata, metadata_path)

    return RecordedTreeDayArtifacts(
        tree_day_path=tree_day_path,
        age_summary_path=age_summary_path,
        genus_summary_path=genus_summary_path,
        metadata_path=metadata_path,
        figure_path=figure_path,
        age_table_path=age_table_path,
        genus_table_path=genus_table_path,
        tree_day_rows=int(len(tree_day)),
        matched_events=int(len(matched)),
        matched_litres=float(litres.sum()),
        unique_trees=int(matched["tree_id"].nunique()),
    )
