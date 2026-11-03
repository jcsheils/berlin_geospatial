"""Build the canonical Planungsraum-month recorded-watering foundation panel."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PanelArtifacts:
    """Paths and headline counts produced by a panel build."""

    panel_path: Path
    crosswalk_path: Path
    metadata_path: Path
    rows: int
    matched_events: int
    matched_litres: float


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


def build_lor_month_panel(
    root: Path,
    *,
    output_dir: Path | None = None,
) -> PanelArtifacts:
    """Build a balanced LOR-month panel from the declared local sources.

    The denominator is the current tree inventory, not a historical monthly
    risk set. Every derived exposure name therefore uses ``recorded_`` and
    every denominator-dependent field explicitly says ``current_inventory``.
    """

    try:
        import geopandas as gpd
        import numpy as np
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - exercised by users
        raise RuntimeError(
            "The foundation panel requires the spatial optional dependencies. "
            "Install requirements-spatial.txt or the project[spatial] extra."
        ) from exc

    from .manifest import load_manifest
    from .paths import resolve_project_path

    root = root.expanduser().resolve()
    manifest = load_manifest(root)
    project = manifest.project

    watering_spec = manifest.datasets["recorded_watering_events"]
    tree_spec = manifest.datasets["tree_inventory"]
    lor_spec = manifest.datasets["lor_boundaries_2021"]
    watering_path = resolve_project_path(root, watering_spec.path or "")
    tree_path = resolve_project_path(root, tree_spec.path or "")
    lor_path = resolve_project_path(root, lor_spec.path or "")

    for path in (watering_path, tree_path, lor_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required panel input is missing: {path}")

    local_timezone = str(project["timezone"])
    analysis_crs = str(project["analysis_crs"])
    start_local = pd.Timestamp(
        str(project["recorded_watering_start"]), tz=local_timezone
    )
    end_local_exclusive = pd.Timestamp(
        str(project["complete_recorded_watering_end_exclusive"]),
        tz=local_timezone,
    )
    start_utc = start_local.tz_convert("UTC")
    end_utc_exclusive = end_local_exclusive.tz_convert("UTC")

    raw = pd.read_csv(
        watering_path,
        sep=watering_spec.delimiter,
        low_memory=False,
    )
    raw_rows = len(raw)
    duplicate_rows = int(raw.duplicated(keep="first").sum())
    events = raw.drop_duplicates(keep="first").copy()
    events["timestamp_utc"] = pd.to_datetime(
        events["timestamp"], format="mixed", utc=True, errors="coerce"
    )
    invalid_timestamps = int(events["timestamp_utc"].isna().sum())
    events["recorded_litres"] = pd.to_numeric(
        events["bewaesserungsmenge_in_liter"], errors="coerce"
    )
    events["id"] = events["id"].astype("string")
    events = events[
        events["timestamp_utc"].ge(start_utc)
        & events["timestamp_utc"].lt(end_utc_exclusive)
    ].copy()
    local_timestamp = events["timestamp_utc"].dt.tz_convert(local_timezone)
    events["month"] = (
        local_timestamp.dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
    )

    lor = gpd.read_file(
        lor_path,
        layer=lor_spec.expected_layer,
        columns=["plr_id", "plr_name", "bzr_id", "bzr_name", "bez"],
    )
    if len(lor) != 542 or not lor["plr_id"].is_unique:
        raise ValueError("The declared LOR layer is not the expected 542-unit vintage.")
    if str(lor.crs) != analysis_crs:
        lor = lor.to_crs(analysis_crs)
    lor["plr_id"] = lor["plr_id"].astype("string")
    lor["district"] = lor["bez"].str.replace(
        r"^\d+\s*-\s*", "", regex=True
    )

    trees = gpd.read_file(
        tree_path,
        layer=tree_spec.expected_layer,
        columns=["pitid"],
    )
    bounds = trees.total_bounds
    if not (bounds[0] > 300_000 and bounds[1] > 5_000_000):
        raise ValueError(
            "Tree coordinates do not look like the documented EPSG:25833 metres."
        )
    trees = trees[trees["pitid"].notna()].copy()
    trees["pitid"] = trees["pitid"].astype("string")
    trees = trees.set_crs(analysis_crs, allow_override=True)

    lor_columns = [
        "plr_id",
        "plr_name",
        "bzr_id",
        "bzr_name",
        "district",
        "geometry",
    ]
    trees_lor = gpd.sjoin(
        trees,
        lor[lor_columns],
        how="left",
        predicate="within",
    ).drop(columns="index_right")
    trees_lor = trees_lor[trees_lor["plr_id"].notna()].copy()

    tree_lor = trees_lor[
        ["pitid", "plr_id", "plr_name", "bzr_id", "bzr_name", "district"]
    ].drop_duplicates()
    multiple_lor = tree_lor.groupby("pitid")["plr_id"].nunique()
    if int((multiple_lor > 1).sum()):
        raise ValueError("At least one tree ID maps to more than one Planungsraum.")
    tree_lor = tree_lor.drop_duplicates("pitid")

    inventory = (
        tree_lor.groupby("plr_id", as_index=False)
        .agg(current_inventory_trees=("pitid", "nunique"))
    )
    recorded_tree_ids = set(events["id"].dropna().astype(str))
    crosswalk = tree_lor[tree_lor["pitid"].isin(recorded_tree_ids)].copy()
    crosswalk = crosswalk.rename(columns={"pitid": "tree_id"}).sort_values(
        ["plr_id", "tree_id"]
    )

    event_geo = events.merge(
        crosswalk[["tree_id", "plr_id"]],
        left_on="id",
        right_on="tree_id",
        how="inner",
        validate="many_to_one",
    )
    monthly = (
        event_geo.groupby(["month", "plr_id"], as_index=False)
        .agg(
            recorded_watered_trees=("id", "nunique"),
            recorded_watering_events=("id", "size"),
            recorded_litres=("recorded_litres", "sum"),
        )
    )

    first_month = start_local.tz_localize(None).to_period("M").start_time
    last_instant = end_local_exclusive.tz_localize(None) - pd.Timedelta(microseconds=1)
    last_month = last_instant.to_period("M").start_time
    months = pd.date_range(first_month, last_month, freq="MS")
    month_frame = pd.DataFrame({"month": months})
    local_start = start_local.tz_localize(None)
    local_end = end_local_exclusive.tz_localize(None)

    month_ends = month_frame["month"] + pd.offsets.MonthBegin(1)
    live_starts = month_frame["month"].where(
        month_frame["month"] >= local_start, local_start
    )
    live_ends = month_ends.where(month_ends <= local_end, local_end)
    month_frame["platform_live_days"] = (
        live_ends.dt.normalize() - live_starts.dt.normalize()
    ).dt.days.clip(lower=0)
    month_frame["platform_month_status"] = np.where(
        month_frame["platform_live_days"] < month_frame["month"].dt.days_in_month,
        "partial_platform_start",
        "complete_month",
    )

    geography = lor[
        ["plr_id", "plr_name", "bzr_id", "bzr_name", "district"]
    ].copy()
    panel = month_frame.merge(geography, how="cross")
    panel = panel.merge(inventory, on="plr_id", how="left")
    panel = panel.merge(monthly, on=["month", "plr_id"], how="left")
    count_columns = [
        "current_inventory_trees",
        "recorded_watered_trees",
        "recorded_watering_events",
    ]
    panel[count_columns] = panel[count_columns].fillna(0).astype("int64")
    panel["recorded_litres"] = panel["recorded_litres"].fillna(0.0)
    denominator = panel["current_inventory_trees"]
    panel["recorded_reach_pct_current_inventory"] = np.where(
        denominator > 0,
        100 * panel["recorded_watered_trees"] / denominator,
        np.nan,
    )
    panel["recorded_events_per_1000_current_inventory_trees"] = np.where(
        denominator > 0,
        1000 * panel["recorded_watering_events"] / denominator,
        np.nan,
    )
    panel["recorded_litres_per_current_inventory_tree"] = np.where(
        denominator > 0,
        panel["recorded_litres"] / denominator,
        np.nan,
    )
    panel = panel.sort_values(["month", "plr_id"]).reset_index(drop=True)
    panel["month"] = panel["month"].dt.strftime("%Y-%m-%d")
    panel = panel[
        [
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
        ]
    ]

    target = output_dir or root / "data/processed/foundation"
    target = target.expanduser().resolve()
    panel_path = target / "lor_month_recorded_watering_2020_2025.csv"
    crosswalk_path = target / "recorded_tree_lor_crosswalk_2020_2025.csv"
    metadata_path = target / "lor_month_recorded_watering_2020_2025.metadata.json"
    _atomic_csv(panel, panel_path)
    _atomic_csv(crosswalk, crosswalk_path)

    source_events = int(len(events))
    source_litres = float(events["recorded_litres"].sum())
    matched_events = int(len(event_geo))
    matched_litres = float(event_geo["recorded_litres"].sum())
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "dataset_id": "lor_month_recorded_watering_foundation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "grain": "planungsraum_month",
        "coverage": {
            "start_inclusive": str(project["recorded_watering_start"]),
            "end_exclusive": str(project["complete_recorded_watering_end_exclusive"]),
            "timezone_for_calendar_month": local_timezone,
            "months": int(len(months)),
            "first_month_status": "partial_platform_start",
        },
        "geography": {
            "lor_vintage": str(project["lor_vintage"]),
            "analysis_crs": analysis_crs,
            "planungsraeume": int(len(lor)),
        },
        "inputs": {
            "recorded_watering_events": {
                "path": str(watering_path.relative_to(root)),
                "sha256": _sha256(watering_path),
            },
            "tree_inventory": {
                "path": str(tree_path.relative_to(root)),
                "sha256": _sha256(tree_path),
                "crs_override": "Declared EPSG:4326 metadata overridden to EPSG:25833 after coordinate-range validation.",
            },
            "lor_boundaries": {
                "path": str(lor_path.relative_to(root)),
                "sha256": _sha256(lor_path),
            },
        },
        "audit": {
            "raw_source_rows": raw_rows,
            "exact_duplicate_rows_removed": duplicate_rows,
            "invalid_timestamps_after_deduplication": invalid_timestamps,
            "deduplicated_events_in_window": source_events,
            "deduplicated_litres_in_window": source_litres,
            "matched_and_lor_assigned_events": matched_events,
            "matched_and_lor_assigned_litres": matched_litres,
            "matched_and_lor_assigned_unique_trees": int(event_geo["id"].nunique()),
            "unmatched_or_unassigned_events": source_events - matched_events,
            "unmatched_or_unassigned_litres": source_litres - matched_litres,
            "panel_rows": int(len(panel)),
        },
        "semantics": {
            "recorded_zero": "No Gieß den Kiez platform activity was recorded for that Planungsraum-month; municipal, private, and unlogged watering remain unobserved.",
            "denominator_caveat": "All denominator-dependent fields use the current tree inventory. They are not historical month-specific eligible-tree risk sets and may include trees planted after the panel month.",
            "first_month_caveat": "May 2020 is only observed from the declared platform start on 18 May and is marked partial_platform_start.",
            "claim_boundary": "This foundation panel describes recorded activity. It does not estimate irrigation coverage, cooling effects, service failure, or causal impacts.",
        },
        "outputs": {
            "panel": str(panel_path.relative_to(root)),
            "recorded_tree_crosswalk": str(crosswalk_path.relative_to(root)),
        },
    }
    _atomic_json(metadata, metadata_path)

    return PanelArtifacts(
        panel_path=panel_path,
        crosswalk_path=crosswalk_path,
        metadata_path=metadata_path,
        rows=int(len(panel)),
        matched_events=matched_events,
        matched_litres=matched_litres,
    )
