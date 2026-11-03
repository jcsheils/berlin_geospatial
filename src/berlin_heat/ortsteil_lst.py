"""Audit and provisionally align supplied monthly LST with recorded watering."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from .watering_response import sha256

CSV_NAME = "berlin_ortsteile_LST_rain_2018_2025_LNDSAT.csv"
BOUNDARY_URL = "https://gdi.berlin.de/services/wfs/alkis_ortsteile?service=WFS&version=2.0.0&request=GetFeature&typeNames=alkis_ortsteile%3Aortsteile&outputFormat=application%2Fjson&srsName=EPSG%3A25833"
EXCLUDED = {"Buckow": "two_distinct_source_rows_per_month",
            "Nikolassee": "source_boundary_vintage_unresolved_after_Schlachtensee_split",
            "Zehlendorf": "source_boundary_vintage_unresolved_after_Schlachtensee_split",
            "Schlachtensee": "no_source_LST_rows"}
DISTRICTS = {
    "01": "Mitte", "02": "Friedrichshain-Kreuzberg", "03": "Pankow",
    "04": "Charlottenburg-Wilmersdorf", "05": "Spandau", "06": "Steglitz-Zehlendorf",
    "07": "Tempelhof-Schöneberg", "08": "Neukölln", "09": "Treptow-Köpenick",
    "10": "Marzahn-Hellersdorf", "11": "Lichtenberg", "12": "Reinickendorf",
}
METRICS = ["recorded_watering_events", "recorded_litres", "recorded_watered_trees"]
RELATIONSHIPS = {
    "previous_LST_current_watering": "previous_month_lst_c",
    "same_month": "lst_c",
    "watering_next_LST": "next_month_lst_c",
}


def audit_source(source: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    needed = {"ortsteil", "bezirk", "year", "month", "LST_C_mean", "LST_C_count", "rain_mm_mean"}
    if not needed.issubset(source):
        raise ValueError("Supplied CSV lacks required columns.")
    raw = source.copy()
    raw["source_row"] = np.arange(2, len(raw) + 2)
    if not raw.month.between(1, 12).all() or not raw.year.between(2018, 2025).all():
        raise ValueError("Unexpected dates in supplied CSV.")
    raw["date"] = pd.to_datetime(dict(year=raw.year, month=raw.month, day=1))
    keys = ["ortsteil", "bezirk", "date"]
    duplicate = raw.duplicated(keys, keep=False)
    if not raw.LST_C_mean.isna().eq(raw.LST_C_count.eq(0)).all():
        raise ValueError("LST missingness and zero counts disagree; inspect source before proceeding.")
    if not raw.LST_C_count.ge(0).all():
        raise ValueError("Negative LST counts.")
    raw["comparison_exclusion_reason"] = raw.ortsteil.map(EXCLUDED).fillna("")
    raw.loc[duplicate, "comparison_exclusion_reason"] = "ambiguous_duplicate_outcome_key"
    usable = raw[raw.comparison_exclusion_reason.eq("")].copy()
    if usable.duplicated(keys).any():
        raise ValueError("Outcome join keys are not unique after exclusions.")
    usable = usable.rename(columns={"date": "month_date", "LST_C_mean": "lst_c",
                                    "LST_C_count": "source_lst_count",
                                    "rain_mm_mean": "source_rain_mm_mean_unverified"})
    maxima = usable.groupby(["ortsteil", "bezirk"]).source_lst_count.transform("max")
    usable["relative_source_count"] = usable.source_lst_count / maxima.where(maxima.gt(0))
    summary = {
        "rows": len(raw), "distinct_ortsteil_names": int(raw.ortsteil.nunique()),
        "years": sorted(int(y) for y in raw.year.unique()),
        "missing_lst_rows": int(raw.LST_C_mean.isna().sum()),
        "missing_lst_pct": float(100 * raw.LST_C_mean.isna().mean()),
        "duplicate_key_rows": int(duplicate.sum()),
        "duplicate_keys": int(raw.loc[duplicate, keys].drop_duplicates().shape[0]),
        "duplicate_names": sorted(raw.loc[duplicate, "ortsteil"].unique().tolist()),
        "exact_duplicate_rows": int(source.duplicated().sum()),
        "valid_lst_count_min": int(raw.loc[raw.LST_C_mean.notna(), "LST_C_count"].min()),
        "valid_lst_count_max": int(raw.LST_C_count.max()),
        "candidate_comparison_areas": int(usable.ortsteil.nunique()),
        "rainfall_missing_rows": int(raw.rain_mm_mean.isna().sum()),
        "counts_semantics": "undefined; not assumed to be overpasses or valid-pixel coverage",
        "missing_metadata": ["extraction script", "boundary file and vintage", "Landsat sensor/product",
                             "acquisition dates and scene counts", "cloud/shadow mask",
                             "monthly compositing method", "LST_C_count definition",
                             "rainfall source, units and monthly aggregation"],
    }
    return raw, usable, summary


def exact_calendar_join(panel: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    keys = ["ortsteil", "district", "month_date"]
    fields = ["lst_c", "source_lst_count", "relative_source_count", "source_rain_mm_mean_unverified"]
    if outcomes.duplicated(keys).any() or panel.duplicated(keys).any():
        raise ValueError("Calendar joins require unique area/month keys.")
    result = panel.merge(outcomes[keys + fields], on=keys, how="left", validate="one_to_one")
    for prefix, shift in [("previous_month", 1), ("next_month", -1)]:
        side = outcomes[keys + fields].copy()
        # Shift source dates toward the watering month: February LST is prior to March watering.
        side["month_date"] = side.month_date + pd.DateOffset(months=shift)
        side = side.rename(columns={name: f"{prefix}_{name}" for name in fields})
        result = result.merge(side, on=keys, how="left", validate="one_to_one")
    return result


def residualise_two_way(values: np.ndarray, area, date) -> np.ndarray:
    """Alternating projections remove area and actual year-month means.

    The projection is applied jointly on identical complete cases. Iteration
    is necessary because the LST panel is unbalanced.
    """
    frame = pd.DataFrame(np.asarray(values, dtype=float))
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("Residualisation requires finite, complete cases.")
    area = pd.Series(np.asarray(area), index=frame.index)
    date = pd.Series(np.asarray(date), index=frame.index)
    for _ in range(1000):
        before = frame.to_numpy().copy()
        frame -= frame.groupby(area).transform("mean")
        frame -= frame.groupby(date).transform("mean")
        if np.max(np.abs(frame.to_numpy() - before)) < 1e-10:
            return frame.to_numpy()
    raise ValueError("Fixed-effect residualisation failed to converge.")


def descriptive_correlations(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    complete_years = panel[panel.year.between(2021, 2025) & panel.comparison_eligible].copy()
    rows, local_rows = [], []
    samples = {
        "April-September_2021-2025": complete_years[complete_years.calendar_month.between(4, 9)],
        "all_months_2021-2025": complete_years,
        "April-September_excluding_2022": complete_years[complete_years.calendar_month.between(4, 9) & complete_years.year.ne(2022)],
    }
    for sample_name, sample in samples.items():
        for relationship, outcome in RELATIONSHIPS.items():
            count_column = outcome.replace("lst_c", "relative_source_count")
            for screen in ["all_available_LST", "relative_count_at_least_0.5"]:
                selected = sample if screen == "all_available_LST" else sample[sample[count_column].ge(.5)]
                for metric in METRICS:
                    exposure = metric + "_per_ha"
                    cases = selected.dropna(subset=[outcome, exposure]).copy()
                    if len(cases) < 3:
                        raise ValueError("Too few complete cases for the specified comparison.")
                    transformed = np.column_stack([cases[outcome], np.log1p(cases[exposure])])
                    residual = residualise_two_way(transformed, cases.ortsteil, cases.month_date)
                    rho = cases[[outcome, exposure]].rank().corr().iloc[0, 1]
                    partial = np.corrcoef(residual.T)[0, 1]
                    rows.append({
                        "sample": sample_name, "relationship": relationship, "screen": screen,
                        "exposure": exposure, "outcome": outcome, "n_area_months": len(cases),
                        "n_areas": cases.ortsteil.nunique(), "n_watering_months": cases.month_date.nunique(),
                        "raw_spearman_rho": rho, "area_and_yearmonth_residual_correlation": partial,
                        "raw_pearson_log1p_exposure": np.corrcoef(transformed.T)[0, 1],
                        "exposure_transform_for_residual_correlation": "log1p(per_ha)",
                        "claim": "provisional descriptive association; no inference or causal effect",
                    })
                    if sample_name == "April-September_2021-2025" and screen == "all_available_LST":
                        for area, group in cases.groupby("ortsteil"):
                            varying = group[outcome].nunique() > 1 and group[exposure].nunique() > 1
                            local_rows.append({"ortsteil": area, "relationship": relationship,
                                               "exposure": exposure, "n_months": len(group),
                                               "raw_spearman_rho": group[[outcome, exposure]].rank().corr().iloc[0, 1] if varying and len(group) >= 12 else np.nan,
                                               "status": "descriptive_only" if varying and len(group) >= 12 else "insufficient_variation_or_months"})
    return pd.DataFrame(rows), pd.DataFrame(local_rows)


def build_ortsteil_extension(root: Path) -> dict:
    output = root / "output/watering_response/ortsteil"
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    source_path = root / "data/raw/supervisor" / CSV_NAME
    boundary_path = root / "data/spatial/alkis_ortsteile_2026_09_29.geojson"
    inventory_path = root / "data/Berlin_trees.gpkg"
    days_path = root / "data/processed/temporal/recorded_tree_day_watering_2020_2025.csv"
    audited, outcomes, source_audit = audit_source(pd.read_csv(source_path))
    polygons = gpd.read_file(boundary_path).to_crs(25833)
    polygons = polygons.rename(columns={"nam": "ortsteil", "sch": "official_area_id"})
    polygons["district"] = polygons.official_area_id.astype(str).str[-4:-2].map(DISTRICTS)
    if len(polygons) != 97 or not polygons.ortsteil.is_unique or polygons.district.isna().any() or not polygons.is_valid.all():
        raise ValueError("Unexpected official boundary keys, district code, count or geometry.")
    polygons["current_boundary_area_ha"] = polygons.geometry.area / 10000
    source_names = set(audited.ortsteil)
    if source_names - set(polygons.ortsteil):
        raise ValueError("Source names not present in official polygons.")
    check = audited[["ortsteil", "bezirk"]].drop_duplicates().merge(
        polygons[["ortsteil", "district"]], on="ortsteil", validate="one_to_one")
    if not check.bezirk.eq(check.district).all():
        raise ValueError("Source and official districts disagree.")

    # Keep inventory geometry authoritative, including its already documented CRS correction.
    trees = gpd.read_file(inventory_path, layer="Berlin_trees", columns=["pitid"])
    if not (trees.total_bounds[0] > 300000 and trees.total_bounds[1] > 5000000):
        raise ValueError("Inventory coordinates no longer match the documented projected CRS.")
    trees = trees.set_crs(25833, allow_override=True).dropna(subset=["pitid"]).copy()
    trees["pitid"] = trees.pitid.astype(str)
    if trees.pitid.duplicated().any():
        raise ValueError("Inventory tree IDs are not unique.")
    assigned = gpd.sjoin(trees, polygons[["ortsteil", "district", "official_area_id", "geometry"]],
                         how="left", predicate="within").drop(columns="index_right")
    if assigned.pitid.duplicated().any():
        raise ValueError("At least one tree assigned to multiple polygons.")
    inventory_counts = assigned.dropna(subset=["ortsteil"]).groupby("ortsteil").pitid.nunique().rename("current_inventory_trees")
    areas = polygons.drop(columns="geometry")[["ortsteil", "district", "official_area_id", "current_boundary_area_ha"]].merge(
        inventory_counts, on="ortsteil", how="left", validate="one_to_one")
    areas["current_inventory_trees"] = areas.current_inventory_trees.fillna(0).astype(int)
    areas["comparison_exclusion_reason"] = areas.ortsteil.map(EXCLUDED).fillna("")
    areas["comparison_eligible"] = areas.comparison_exclusion_reason.eq("")

    days = pd.read_csv(days_path, dtype={"tree_id": str}, parse_dates=["local_date"])
    days = days.rename(columns={"district": "foundation_district"})
    tree_crosswalk = assigned[assigned.pitid.isin(set(days.tree_id))].drop(columns="geometry").rename(columns={"pitid": "tree_id"})
    linked = days.merge(tree_crosswalk, on="tree_id", how="left", validate="many_to_one")
    unassigned = linked[linked.ortsteil.isna()].copy()
    matched = linked[linked.ortsteil.notna()].copy()
    matched["month_date"] = matched.local_date.dt.to_period("M").dt.to_timestamp()
    monthly = matched.groupby(["ortsteil", "district", "month_date"], as_index=False).agg(
        recorded_watering_events=(METRICS[0], "sum"), recorded_litres=(METRICS[1], "sum"),
        recorded_watered_trees=("tree_id", "nunique"))
    grid = areas.merge(pd.DataFrame({"month_date": pd.date_range("2020-05-01", "2025-12-01", freq="MS")}), how="cross")
    panel = grid.merge(monthly, on=["ortsteil", "district", "month_date"], how="left", validate="one_to_one")
    panel[METRICS] = panel[METRICS].fillna(0)
    panel[METRICS[0]] = panel[METRICS[0]].astype(int)
    panel[METRICS[2]] = panel[METRICS[2]].astype(int)
    panel["year"] = panel.month_date.dt.year
    panel["calendar_month"] = panel.month_date.dt.month
    panel["platform_month_status"] = np.where(panel.month_date.eq("2020-05-01"), "partial_platform_start", "complete_month")
    for metric in METRICS:
        panel[metric + "_per_ha"] = panel[metric] / panel.current_boundary_area_ha
    panel["recorded_reach_pct_current_inventory"] = 100 * panel.recorded_watered_trees / panel.current_inventory_trees.where(panel.current_inventory_trees.gt(0))
    outcomes = outcomes.rename(columns={"bezirk": "district"})
    panel = exact_calendar_join(panel, outcomes)
    panel["geography_status"] = "provisional_current_official_boundaries_source_vintage_unverified"
    panel = panel.sort_values(["month_date", "district", "ortsteil"]).reset_index(drop=True)
    if int(panel.recorded_watering_events.sum()) + int(unassigned.recorded_watering_events.sum()) != int(days.recorded_watering_events.sum()):
        raise ValueError("Ortsteil event totals do not reconcile to linked tree-day source.")
    if not np.isclose(panel.recorded_litres.sum() + unassigned.recorded_litres.sum(), days.recorded_litres.sum()):
        raise ValueError("Ortsteil litre totals do not reconcile.")

    correlations, local = descriptive_correlations(panel)
    availability = audited.groupby(["year", "month"], as_index=False).agg(
        source_rows=("source_row", "size"), valid_lst_rows=("LST_C_mean", "count"),
        source_lst_count_total=("LST_C_count", "sum"))
    availability["valid_lst_pct"] = 100 * availability.valid_lst_rows / availability.source_rows
    eligibility = panel[panel.year.ge(2021) & panel.calendar_month.between(4, 9) & panel.comparison_eligible]
    spatial_audit = {
        "official_areas": len(areas), "comparison_areas": int(areas.comparison_eligible.sum()),
        "current_inventory_trees_assigned": int(areas.current_inventory_trees.sum()),
        "current_inventory_trees_unassigned": int(assigned.ortsteil.isna().sum()),
        "recorded_tree_ids_assigned": int(matched.tree_id.nunique()),
        "recorded_events_assigned": int(matched.recorded_watering_events.sum()),
        "recorded_litres_assigned": float(matched.recorded_litres.sum()),
        "recorded_events_unassigned": int(unassigned.recorded_watering_events.sum()),
        "recorded_litres_unassigned": float(unassigned.recorded_litres.sum()),
        "recorded_events_district_disagreement": int(matched.loc[matched.district.ne(matched.foundation_district), "recorded_watering_events"].sum()),
        "comparison_eligible_events_entire_period": int(panel.loc[panel.comparison_eligible, "recorded_watering_events"].sum()),
        "core_eligible_area_months_before_LST_missingness": len(eligibility),
        "core_available_same_month_LST": int(eligibility.lst_c.count()),
        "source_boundary_alignment": "provisional; matching names/districts is not proof of identical polygons",
    }
    all_tables = {
        "source_row_audit": audited,
        "source_excluded_rows": audited[audited.comparison_exclusion_reason.ne("")],
        "source_monthly_availability": availability,
        "ortsteil_geography_audit": areas,
        "recorded_tree_ortsteil_crosswalk": tree_crosswalk,
        "unassigned_recorded_tree_days": unassigned,
        "ortsteil_month_watering_lst_2020_2025": panel,
        "provisional_pooled_correlations": correlations,
        "provisional_within_ortsteil_correlations": local,
    }
    for name, frame in all_tables.items():
        frame.to_csv(tables / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    meta = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_audit": source_audit, "spatial_audit": spatial_audit,
        "boundary_source": BOUNDARY_URL,
        "boundary_catalogue": "https://daten.berlin.de/datensaetze/alkis-berlin-ortsteile-wfs-61bd3084",
        "boundary_licence": "Datenlizenz Deutschland – Zero – Version 2.0",
        "boundary_retrieved_date": "2026-09-29",
        "boundary_change_reference": "https://www.berlin.de/ba-steglitz-zehlendorf/aktuelles/pressemitteilungen/2020/pressemitteilung.1024262.php",
        "inputs_sha256": {str(p.relative_to(root)): sha256(p) for p in [source_path, boundary_path, inventory_path, days_path]},
        "outputs_sha256": {name: sha256(tables / f"{name}.csv") for name in all_tables},
        "protocol_sha256": sha256(root / "docs/watering_response_exploratory_protocol.md"),
        "code_sha256": sha256(Path(__file__)),
        "claims": "Provisional descriptive correlations only. Source metadata and original polygon alignment remain unresolved. No causal or confirmatory cooling analysis.",
    }
    (output / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return {"tables": all_tables, "metadata": meta}
