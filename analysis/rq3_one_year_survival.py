"""Registered one-year test for RQ3: logged citizen watering and street-tree removal, 2025 to 2026.

Two stages, run in order:

- `design` builds the cohort, exposure, matching strata and detectability from the
  2025 inventory and the 2020-2024 logs. It never opens the 2026 inventory, so it
  sees no outcome.
- `outcome` runs the analysis fixed in docs/rq3_one_year_survival_protocol.md. It
  refuses to run unless the protocol's SHA-256 equals the registered hash in
  config/project.toml and the cohort matches the saved design exactly.
- `corrected` is a disclosed deviation (docs/rq3_one_year_survival_deviation.md).
  The registered run took exposure from the tree-day table, which keeps only trees
  still in the 2026 inventory, so every removed tree counted as unwatered. This
  stage takes exposure from the raw log export and adds a cluster-bootstrap interval.

Results are pooled over ages: nothing is tabulated by single year of age or by
municipal-care limit, which belong to a separately registered test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tomllib

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

from analysis.build_feedback_benchmarks import INVENTORY_2025, Z_80, compare_identifiers

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/rq3_one_year_survival_protocol.md"
CONFIG = ROOT / "config/project.toml"
OUT = ROOT / "output/rq3_one_year_survival"
TREE_DAY = ROOT / "data/processed/temporal/recorded_tree_day_watering_2020_2025.csv"
RAW_LOGS = ROOT / "data/giessdenkiez_bewässerungsdaten (1).csv"
LOR = ROOT / "data/spatial/lor_planungsraeume_2021.gpkg"
BENCHMARKS = ROOT / "output/feedback_benchmarks/benchmarks.json"

COHORT_YEAR = 2025
EXPOSURE_YEARS = (2020, 2024)
SEASON_MONTHS = (4, 9)
YOUNG_AGES = (0, 15)
PLACEBO_AGES = (16, 40)
HIGH_DOSE_L = 500
TOP_GENERA = 10
BOOTSTRAP_REPS = 2000
STRATUM = ["district", "planting_year", "genus_group"]
LOCAL_STRATUM = ["plr_id", "planting_year"]


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def pitid(tree_id: pd.Series) -> pd.Series:
    """`strassenbaeume.00008100_0012abcd` -> `00008100:0012abcd`, the identifier the logs use."""
    return tree_id.str.split(".", n=1).str[1].str.replace("_", ":", n=1)


def load_cohort() -> pd.DataFrame:
    """Street trees in the 2025 inventory aged 0-40, with matching covariates and planning area."""
    trees = pd.read_csv(INVENTORY_2025, dtype={"tree_id": str})
    street = trees[trees["tree_id"].str.startswith("strassenbaeume.") & trees["planting_year"].notna()].copy()
    street["age"] = COHORT_YEAR - street["planting_year"]
    street = street[street["age"].between(YOUNG_AGES[0], PLACEBO_AGES[1])].copy()
    street["pitid"] = pitid(street["tree_id"])
    young = street["age"] <= YOUNG_AGES[1]
    common = street.loc[young, "genus"].value_counts().head(TOP_GENERA).index
    street["genus_group"] = street["genus"].where(street["genus"].isin(common), "OTHER")
    points = gpd.GeoDataFrame(street[["tree_id"]], geometry=gpd.points_from_xy(street["x_25833"], street["y_25833"]), crs="EPSG:25833")
    areas = gpd.read_file(LOR)[["plr_id", "geometry"]]
    located = gpd.sjoin(points, areas, how="left", predicate="within").drop_duplicates("tree_id")
    street["plr_id"] = located.set_index("tree_id").loc[street["tree_id"], "plr_id"].to_numpy()
    return street


def add_exposure(cohort: pd.DataFrame, tree_day: pd.DataFrame) -> pd.DataFrame:
    """Flag trees with any April-September log in 2020-2024, and those that once got 500 L or more in a season."""
    logs = tree_day[tree_day["year"].between(*EXPOSURE_YEARS) & tree_day["calendar_month"].between(*SEASON_MONTHS)]
    season_litres = logs.groupby(["tree_id", "year"])["recorded_litres"].sum().groupby("tree_id").max()
    out = cohort.copy()
    out["watered"] = out["pitid"].isin(season_litres.index)
    out["high_dose"] = out["pitid"].map(season_litres).fillna(0) >= HIGH_DOSE_L
    return out


def load_raw_logs(path: Path = RAW_LOGS) -> pd.DataFrame:
    """Logs from the platform export, cleaned as for the tree-day table but not matched to any inventory."""
    project = tomllib.loads(CONFIG.read_text())["project"]
    raw = pd.read_csv(path, sep=";", dtype=str).drop_duplicates()
    time = pd.to_datetime(raw["timestamp"], format="mixed", utc=True, errors="coerce").dt.tz_convert(project["timezone"])
    start = pd.Timestamp(project["recorded_watering_start"], tz=project["timezone"])
    end = pd.Timestamp(project["complete_recorded_watering_end_exclusive"], tz=project["timezone"])
    logs = pd.DataFrame({"tree_id": raw["id"].str.strip(), "year": time.dt.year, "calendar_month": time.dt.month,
                         "recorded_litres": pd.to_numeric(raw["bewaesserungsmenge_in_liter"], errors="coerce")})
    keep = time.ge(start) & time.lt(end) & logs["recorded_litres"].gt(0) & logs["tree_id"].fillna("").ne("")
    return logs[keep.fillna(False)]


def cluster_bootstrap(data: pd.DataFrame, treat: str, y: np.ndarray, strata: list[str], reps: int, seed: int) -> list[float]:
    """95% percentile interval for the risk difference, resampling planning areas with replacement."""
    cell = pd.DataFrame({"area": data["plr_id"].to_numpy(), "stratum": data.groupby(strata).ngroup().to_numpy(),
                         "treated": data[treat].to_numpy(), "y": y})
    areas = pd.Index(cell["area"].unique())
    k = cell["stratum"].max() + 1
    column = cell["stratum"].to_numpy() + k * cell["treated"].to_numpy()
    rows = areas.get_indexer(cell["area"])
    count = np.zeros((len(areas), 2 * k))
    events = np.zeros((len(areas), 2 * k))
    np.add.at(count, (rows, column), 1)
    np.add.at(events, (rows, column), cell["y"].to_numpy())
    draws = np.random.default_rng(seed).multinomial(len(areas), np.full(len(areas), 1 / len(areas)), size=reps)
    n, e = draws @ count, draws @ events
    n0, n1, e0, e1 = n[:, :k], n[:, k:], e[:, :k], e[:, k:]
    both = (n0 > 0) & (n1 > 0)
    treated = np.where(both, n1, 0).sum(axis=1)
    control_risk = np.where(both, n1 * e0 / np.where(n0 > 0, n0, 1), 0).sum(axis=1) / treated
    difference = np.where(both, e1, 0).sum(axis=1) / treated - control_risk
    return [round(100 * float(q), 2) for q in np.quantile(difference, [0.025, 0.975])]


def att(frame: pd.DataFrame, treat: str, outcome: str | None = None, p0: float | None = None,
        strata: list[str] = STRATUM, bootstrap: int = 0) -> dict:
    """Exact-stratum estimate of the risk difference for treated trees (treated minus matched controls).

    Strata without a control or without a treated tree drop out. Controls are weighted
    so each stratum counts in proportion to its treated trees. The variance is the
    linearised (influence-function) variance conditional on stratum counts, summed by
    planning area so trees in one area may be correlated. With no outcome, only sample
    sizes and the minimum detectable difference at baseline risk `p0` are returned.
    """
    data = frame.dropna(subset=["plr_id"]).copy()
    counts = data.groupby(strata)[treat].agg(n1="sum", n="size")
    counts["n0"] = counts["n"] - counts["n1"]
    kept = counts[(counts["n1"] > 0) & (counts["n0"] > 0)]
    data = data.join(kept[["n1", "n0"]], on=strata, how="inner")
    treated = data[treat].to_numpy()
    n1_total = int(treated.sum())
    weight = np.where(treated, 1 / n1_total, data["n1"] / n1_total / data["n0"])
    out = {
        "treated": n1_total,
        "treated_without_matching_control": int(frame[treat].sum() - n1_total),
        "controls": int((~treated).sum()),
        "effective_controls": round(1 / float((weight[~treated] ** 2).sum()), 1),  # control weights sum to 1
        "strata": int(len(kept)),
        "planning_areas": int(data["plr_id"].nunique()),
    }
    if p0 is not None:
        spread = (weight ** 2).sum()
        out["mde_pp_design_effect_1_and_2"] = [round(100 * Z_80 * math.sqrt(d * p0 * (1 - p0) * spread), 2) for d in (1, 2)]
    if outcome is None:
        return out
    y = data[outcome].astype(float).to_numpy()
    stratum_mean = data.assign(y=y).groupby(strata + [treat])["y"].transform("mean").to_numpy()
    risk_treated = float(y[treated].mean())
    risk_control = float((weight[~treated] * y[~treated]).sum())
    influence = np.where(treated, 1, -1) * weight * (y - stratum_mean)
    by_area = pd.Series(influence).groupby(data["plr_id"].to_numpy()).sum().to_numpy()
    areas = len(by_area)
    se = math.sqrt(areas / (areas - 1) * float((by_area ** 2).sum()))
    difference = risk_treated - risk_control
    out.update({
        "removals_treated": int(y[treated].sum()),
        "risk_treated_pct": round(100 * risk_treated, 2),
        "risk_matched_control_pct": round(100 * risk_control, 2),
        "risk_difference_pp": round(100 * difference, 2),
        "ci95_pp": [round(100 * (difference - 1.959964 * se), 2), round(100 * (difference + 1.959964 * se), 2)],
        "p_two_sided": round(math.erfc(abs(difference / se) / math.sqrt(2)), 4) if se > 0 else None,
    })
    if bootstrap:
        seed = tomllib.loads(CONFIG.read_text())["project"]["random_seed"]
        out["ci95_pp_cluster_bootstrap"] = cluster_bootstrap(data, treat, y, strata, bootstrap, seed)
    return out


def baseline_risks() -> dict:
    """Overall removal risks already reported for all street trees, never split by watering."""
    street = json.loads(BENCHMARKS.read_text())["design_feasibility"]["inventory_ids_2025_to_2026"]
    return {"young": street["young_street_age_le15"]["removed_pct"] / 100,
            "placebo": street["street"]["removed_pct_by_age_2025"]["16-40"] / 100}


def analyses(cohort: pd.DataFrame, outcome: str | None = None, outcome_any_absent: str | None = None, bootstrap: int = 0) -> dict:
    risk = baseline_risks()
    young = cohort[cohort["age"].between(*YOUNG_AGES)]
    placebo = cohort[cohort["age"].between(*PLACEBO_AGES)]
    return {
        "primary_any_log_2020_2024_age_0_15": att(young, "watered", outcome, risk["young"], bootstrap=bootstrap),
        "s1_identifier_absent_without_rekey_correction": att(young, "watered", outcome_any_absent, risk["young"], bootstrap=bootstrap) if outcome_any_absent else None,
        "s2_500_l_or_more_in_a_season": att(young.loc[young["watered"] == young["high_dose"]], "high_dose", outcome, risk["young"], bootstrap=bootstrap),
        "s3_placebo_age_16_40": att(placebo, "watered", outcome, risk["placebo"], bootstrap=bootstrap),
        "s4_matched_within_planning_area": att(young, "watered", outcome, risk["young"], LOCAL_STRATUM, bootstrap),
    }


def design() -> dict:
    cohort = add_exposure(load_cohort(), read_tree_day())
    result = {k: v for k, v in analyses(cohort).items() if v is not None}
    young = cohort[cohort["age"].between(*YOUNG_AGES)]
    return {
        "stage": "design (no outcome data opened)",
        "cohort": {
            "street_trees_age_0_40_2025": int(len(cohort)),
            "street_trees_age_0_15_2025": int(len(young)),
            "outside_planning_areas": int(cohort["plr_id"].isna().sum()),
            "age_0_15_watered_2020_2024": int(young["watered"].sum()),
            "age_0_15_500_l_or_more": int(young["high_dose"].sum()),
            "age_16_40_watered_2020_2024": int(cohort.loc[cohort["age"].between(*PLACEBO_AGES), "watered"].sum()),
            "genus_groups": sorted(cohort["genus_group"].unique().tolist()),
        },
        "analyses": result,
        "baseline_risks_used_for_detectability": baseline_risks(),
        "inputs_sha256": {"inventory_2025": sha256(INVENTORY_2025), "tree_day": sha256(TREE_DAY), "lor": sha256(LOR)},
    }


def registered_hash() -> str | None:
    return tomllib.loads(CONFIG.read_text()).get("project", {}).get("rq3_one_year_survival", {}).get("protocol_sha256")


def attach_outcomes(cohort: pd.DataFrame, inventory_path: Path) -> pd.DataFrame:
    """Removed: identifier absent from the 2026 inventory and not re-keyed. Absent: identifier absent."""
    before = pd.read_csv(INVENTORY_2025, dtype={"tree_id": str}).rename(columns={"x_25833": "x", "y_25833": "y"})
    after = pyogrio.read_dataframe(inventory_path, layer="Berlin_trees", columns=["id", "gattung", "pflanzjahr"])
    after = pd.DataFrame({"tree_id": after["id"], "genus": after["gattung"], "planting_year": pd.to_numeric(after["pflanzjahr"], errors="coerce"),
                          "x": after.geometry.x, "y": after.geometry.y})
    status = compare_identifiers(before, after).set_index("tree_id")
    out = cohort.copy()
    out["removed"] = (status["gone"] & ~status["rekeyed"]).loc[out["tree_id"]].to_numpy()
    out["absent"] = status["gone"].loc[out["tree_id"]].to_numpy()
    return out


def read_tree_day() -> pd.DataFrame:
    return pd.read_csv(TREE_DAY, dtype={"tree_id": str}, usecols=["tree_id", "year", "calendar_month", "recorded_litres"])


def outcome(inventory_path: Path) -> dict:
    expected = registered_hash()
    if not expected or sha256(PROTOCOL) != expected:
        raise SystemExit("Protocol hash does not match the registered hash in config/project.toml; not running the outcome stage.")
    saved = json.loads((OUT / "design.json").read_text())
    cohort = attach_outcomes(add_exposure(load_cohort(), read_tree_day()), inventory_path)
    result = analyses(cohort, "removed", "absent")
    for name, values in saved["analyses"].items():
        if any(result[name][k] != values[k] for k in ("treated", "controls", "strata")):
            raise SystemExit(f"{name}: cohort differs from the saved design; not reporting outcomes.")
    return {"stage": "outcome", "protocol_sha256": expected, "analyses": result,
            "inputs_sha256": {**saved["inputs_sha256"], "inventory_2026": sha256(inventory_path)}}


def corrected(inventory_path: Path) -> dict:
    """The registered analysis with exposure from the raw export and a cluster-bootstrap interval."""
    base = load_cohort()
    cohort = attach_outcomes(add_exposure(base, load_raw_logs()), inventory_path)
    registered = add_exposure(base, read_tree_day())
    young = cohort["age"].between(*YOUNG_AGES)
    return {
        "stage": "corrected (disclosed deviation; see docs/rq3_one_year_survival_deviation.md)",
        "protocol_sha256": registered_hash(),
        "exposure_source": str(RAW_LOGS.relative_to(ROOT)),
        "watered_age_0_15_raw_export_vs_tree_day": [int(cohort.loc[young, "watered"].sum()), int(registered.loc[young, "watered"].sum())],
        "analyses": analyses(cohort, "removed", "absent", BOOTSTRAP_REPS),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "unit": "planning area", "interval": "percentile"},
        "inputs_sha256": {"inventory_2025": sha256(INVENTORY_2025), "raw_logs": sha256(RAW_LOGS), "lor": sha256(LOR),
                          "inventory_2026": sha256(inventory_path)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stage", choices=["design", "outcome", "corrected"])
    parser.add_argument("--inventory", type=Path, default=ROOT / "data/Berlin_trees.gpkg", help="2026 inventory (outcome and corrected stages)")
    args = parser.parse_args()
    result = {"design": design, "outcome": outcome, "corrected": corrected}[args.stage](*([] if args.stage == "design" else [args.inventory]))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{args.stage}.json"
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
