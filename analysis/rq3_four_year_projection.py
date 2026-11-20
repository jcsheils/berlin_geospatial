"""Projected detectability for the four-year RQ3 test (docs/rq3_four_year_survival_protocol.md).

The plan compares, at each yearly tree table from 2021 to 2024, young street trees
logged in any earlier season with trees never logged, and follows both to the next
table. Until CityLAB supplies those tables and the full log history, this script
projects the sample from what the repository holds:

- the 2025 inventory stands in for each earlier table (trees planted by that year);
- the open log export stands in for the full log history.

Both miss trees removed before 2025, so the projected counts are lower bounds. The
script opens no removal data: detectability uses the pooled 2025-2026 removal risk
already reported in the benchmarks.
"""
from __future__ import annotations

import json
import math
import tomllib

import geopandas as gpd
import pandas as pd

from analysis import rq3_one_year_survival as one_year
from analysis.build_feedback_benchmarks import INVENTORY_2025, Z_80

ROOT = one_year.ROOT
OUT = ROOT / "output/rq3_four_year_survival"
LANDMARKS = (2021, 2022, 2023, 2024)
YOUNG_AGES = one_year.YOUNG_AGES
OLDER_AGES = one_year.PLACEBO_AGES
STRATA = {
    "district": ["landmark", "district", "planting_year", "genus_group"],
    "bezirksregion": ["landmark", "bzr_id", "planting_year", "genus_group"],
    "planning_area": ["landmark", "plr_id", "planting_year", "genus_group"],
}


def smallest_effect() -> float:
    """Smallest effect of interest, as a removal risk per year."""
    plan = tomllib.loads(one_year.CONFIG.read_text())["project"]["rq3_four_year_survival"]
    return plan["smallest_effect_pp_per_year"] / 100


def load_trees() -> pd.DataFrame:
    """All street trees in the 2025 inventory with a planting year, genus group, planning area and Bezirksregion."""
    trees = pd.read_csv(INVENTORY_2025, dtype={"tree_id": str})
    street = trees[trees["tree_id"].str.startswith("strassenbaeume.") & trees["planting_year"].notna()].copy()
    street["pitid"] = one_year.pitid(street["tree_id"])
    young = (one_year.COHORT_YEAR - street["planting_year"]).between(*YOUNG_AGES)
    common = street.loc[young, "genus"].value_counts().head(one_year.TOP_GENERA).index
    street["genus_group"] = street["genus"].where(street["genus"].isin(common), "OTHER")
    points = gpd.GeoDataFrame(street[["tree_id"]], geometry=gpd.points_from_xy(street["x_25833"], street["y_25833"]), crs="EPSG:25833")
    areas = gpd.read_file(one_year.LOR)[["plr_id", "bzr_id", "geometry"]]
    located = gpd.sjoin(points, areas, how="left", predicate="within").drop_duplicates("tree_id").set_index("tree_id")
    for column in ("plr_id", "bzr_id"):
        street[column] = located.loc[street["tree_id"], column].to_numpy()
    return street


def season_table(logs: pd.DataFrame) -> pd.DataFrame:
    """Log days and litres per tree and April-September season."""
    in_season = logs[logs["calendar_month"].between(*one_year.SEASON_MONTHS)]
    return (in_season.groupby(["tree_id", "year"])
            .agg(days=("date", "nunique"), litres=("recorded_litres", "sum")).reset_index())


def landmark_exposure(cohort: pd.DataFrame, seasons: pd.DataFrame, landmark: int) -> pd.DataFrame:
    """Exposure from seasons before the landmark year only; logs from the landmark season onwards never count."""
    earlier = (seasons[seasons["year"] < landmark].groupby("tree_id")
               .agg(days=("days", "max"), litres=("litres", "max"), seasons=("year", "nunique"), last=("year", "max")))
    tree = cohort["pitid"].map
    out = cohort.copy()
    out["watered"] = cohort["pitid"].isin(earlier.index)
    out["last_season"] = tree(earlier["last"]).eq(landmark - 1)
    out["three_days"] = tree(earlier["days"]).fillna(0) >= 3
    out["two_seasons"] = tree(earlier["seasons"]).fillna(0) >= 2
    out["high_dose"] = tree(earlier["litres"]).fillna(0) >= one_year.HIGH_DOSE_L
    return out


def stack(trees: pd.DataFrame, seasons: pd.DataFrame) -> pd.DataFrame:
    """One row per tree and landmark: trees planted by the landmark year, aged 0-40 in it."""
    frames = []
    for landmark in LANDMARKS:
        cohort = trees[trees["planting_year"] <= landmark].copy()
        cohort["age"] = landmark - cohort["planting_year"]
        cohort = cohort[cohort["age"].between(YOUNG_AGES[0], OLDER_AGES[1])].assign(landmark=landmark)
        frames.append(landmark_exposure(cohort, seasons, landmark))
    return pd.concat(frames, ignore_index=True)


def power(se: float, effect: float, z: float) -> float:
    """Probability that an interval clears `effect` when the estimate is normal with standard error `se`."""
    return 0.5 * (1 + math.erf((effect / se - z) / math.sqrt(2)))


def detectability(frame: pd.DataFrame, treat: str, strata: list[str], p0: float, delta: float) -> dict:
    """Sample sizes, detectable difference and the power of both primary tests, without and with a design effect of 2."""
    out = one_year.att(frame, treat, p0=p0, strata=strata)
    se = [mde / 100 / Z_80 for mde in out["mde_pp_design_effect_1_and_2"]]
    out["power_pct_test_a_if_reduction_equals_delta"] = [round(100 * power(s, delta, 1.959964), 1) for s in se]
    out["power_pct_test_b_if_no_difference"] = [round(100 * power(s, delta, 1.644854), 1) for s in se]
    return out


def project() -> dict:
    risk = one_year.baseline_risks()
    delta = smallest_effect()
    rows = stack(load_trees(), season_table(one_year.load_raw_logs()))
    young = rows[rows["age"].between(*YOUNG_AGES)]
    older = rows[rows["age"].between(*OLDER_AGES)]
    against_never = lambda frame, treat: frame[frame[treat] | ~frame["watered"]]  # noqa: E731
    young_test = lambda frame, treat, strata="district": detectability(frame, treat, STRATA[strata], risk["young"], delta)  # noqa: E731
    analyses = {
        "primary_any_earlier_log_district": young_test(young, "watered"),
        "s2_three_log_days_in_a_season": young_test(against_never(young, "three_days"), "three_days"),
        "s2_two_or_more_seasons": young_test(against_never(young, "two_seasons"), "two_seasons"),
        "s2_500_l_or_more_in_a_season": young_test(against_never(young, "high_dose"), "high_dose"),
        "s3_older_trees_16_40": detectability(older, "watered", STRATA["district"], risk["placebo"], delta),
        "s4_bezirksregion_strata": young_test(young, "watered", "bezirksregion"),
        "s5_planning_area_strata": young_test(young, "watered", "planning_area"),
        "s6_logged_in_the_last_season": young_test(against_never(young, "last_season"), "last_season"),
    }
    young_mde = analyses["primary_any_earlier_log_district"]["mde_pp_design_effect_1_and_2"]
    older_mde = analyses["s3_older_trees_16_40"]["mde_pp_design_effect_1_and_2"]
    return {
        "note": "Projection from the 2025 inventory and the open log export; lower bounds. No removal data opened.",
        "inputs_sha256": {"inventory_2025": one_year.sha256(INVENTORY_2025), "log_export": one_year.sha256(one_year.RAW_LOGS)},
        "landmarks": list(LANDMARKS),
        "baseline_removal_risk_per_year": risk,
        "smallest_effect_pp_per_year": round(100 * delta, 2),
        "young_trees_by_landmark": young.groupby("landmark").size().to_dict(),
        "young_watered_by_landmark": young.groupby("landmark")["watered"].sum().astype(int).to_dict(),
        "analyses": analyses,
        "s3_young_minus_older_mde_pp": [round(math.hypot(a, b), 2) for a, b in zip(young_mde, older_mde)],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result = project()
    (OUT / "projection.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    primary = result["analyses"]["primary_any_earlier_log_district"]
    print(f"primary: {primary['treated']} watered tree-years, detectable {primary['mde_pp_design_effect_1_and_2']} pp per year")


if __name__ == "__main__":
    main()
