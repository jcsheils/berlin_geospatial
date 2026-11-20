"""Projected sample for the RQ3 crown-health test (docs/rq3_crown_health_protocol.md).

The test compares the change in crown NDVI between the August 2020 and August 2025
aerial images for young street trees first watered after the 2020 flight and for trees
never watered. This script counts those trees and the detectable difference in units
of the outcome's residual standard deviation. It uses the 2025 inventory and the open
log export only and opens no image.
"""
from __future__ import annotations

import datetime as dt
import json
import math

import numpy as np
import pandas as pd

from analysis import rq3_four_year_projection as four_year
from analysis import rq3_one_year_survival as one_year
from analysis.build_feedback_benchmarks import Z_80

OUT = one_year.ROOT / "output/rq3_crown_health"
BASELINE_FLIGHT_END = dt.date(2020, 8, 16)  # flights on 1, 8, 12 and 16 August 2020
OUTCOME_FLIGHT_START = dt.date(2025, 8, 11)  # flights on 11 and 12 August 2025
BASELINE_YEAR = 2020
YOUNG_AGES = (1, 15)  # age in 2020; trees planted in 2020 may postdate the flight
OLDER_AGES = (16, 40)
PLACEBO_LAST_PLANTING = 2014  # standing at the August 2015 flight
FIXED_EFFECTS = [["plr_id"], ["planting_year", "genus_group"]]
EXACT_STRATA = ["plr_id", "planting_year", "genus_group"]


def exposure(cohort: pd.DataFrame, logs: pd.DataFrame) -> pd.DataFrame:
    """Flag trees watered between the two flights, before the first, or never before the second."""
    window = logs[logs["date"] < OUTCOME_FLIGHT_START]
    early = window["date"] <= BASELINE_FLIGHT_END
    between = window[~early]
    seasons = four_year.season_table(between).groupby("tree_id").agg(
        days=("days", "max"), litres=("litres", "max"), seasons=("year", "nunique"))
    tree = cohort["pitid"].map
    out = cohort.copy()
    out["watered_before_baseline"] = cohort["pitid"].isin(set(window.loc[early, "tree_id"]))
    out["watered"] = cohort["pitid"].isin(set(between["tree_id"])) & ~out["watered_before_baseline"]
    out["never"] = ~cohort["pitid"].isin(set(window["tree_id"]))
    out["three_days"] = out["watered"] & (tree(seasons["days"]).fillna(0) >= 3)
    out["two_seasons"] = out["watered"] & (tree(seasons["seasons"]).fillna(0) >= 2)
    out["high_dose"] = out["watered"] & (tree(seasons["litres"]).fillna(0) >= one_year.HIGH_DOSE_L)
    return out


def standardised_mde(frame: pd.DataFrame, treat: str, groups: list[list[str]] = FIXED_EFFECTS, sweeps: int = 50) -> list[float]:
    """Detectable difference (80% power, two-sided 5%) in residual-SD units, design effect 1 and 2.

    For a regression of the outcome on `treat` with additive fixed effects, the
    variance of the coefficient is sigma^2 / sum(r^2), where r is `treat` after
    sweeping out the fixed effects (Frisch-Waugh-Lovell).
    """
    r = frame[treat].astype(float).to_numpy()
    r = r - r.mean()
    keys = [frame.groupby(g).ngroup().to_numpy() for g in groups]
    for _ in range(sweeps):
        for key in keys:
            r = r - (np.bincount(key, r) / np.bincount(key))[key]
    return [round(Z_80 * math.sqrt(d / float((r ** 2).sum())), 3) for d in (1, 2)]


def describe(frame: pd.DataFrame, treat: str) -> dict:
    sample = frame[frame[treat] | frame["never"]].dropna(subset=["plr_id"])
    exact = one_year.att(sample, treat, strata=EXACT_STRATA)
    return {
        "treated": int(sample[treat].sum()),
        "controls": int(sample["never"].sum()),
        "mde_residual_sd_design_effect_1_and_2": standardised_mde(sample, treat),
        "exact_strata_treated_without_matching_control": exact["treated_without_matching_control"],
    }


def project() -> dict:
    trees = four_year.load_trees()
    trees = trees[trees["planting_year"] < BASELINE_YEAR].copy()
    trees["age_2020"] = BASELINE_YEAR - trees["planting_year"]
    trees = exposure(trees, one_year.load_raw_logs())
    young = trees[trees["age_2020"].between(*YOUNG_AGES)]
    older = trees[trees["age_2020"].between(*OLDER_AGES)]
    placebo = young[young["planting_year"] <= PLACEBO_LAST_PLANTING]
    return {
        "note": "Projection from the 2025 inventory and the open log export; no image opened, no outcome.",
        "inputs_sha256": {"inventory_2025": one_year.sha256(four_year.INVENTORY_2025), "log_export": one_year.sha256(one_year.RAW_LOGS)},
        "young_street_trees_age_1_15_in_2020": int(len(young)),
        "young_watered_before_the_2020_flight": int(young["watered_before_baseline"].sum()),
        "analyses": {
            "primary_watered_between_flights": describe(young, "watered"),
            "s_dose_three_log_days_in_a_season": describe(young, "three_days"),
            "s_dose_two_or_more_seasons": describe(young, "two_seasons"),
            "s_dose_500_l_or_more_in_a_season": describe(young, "high_dose"),
            "placebo_2015_2020_planted_by_2014": describe(placebo, "watered"),
            "negative_control_age_16_40": describe(older, "watered"),
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result = project()
    (OUT / "projection.json").write_text(json.dumps(result, indent=2) + "\n")
    primary = result["analyses"]["primary_watered_between_flights"]
    print(f"primary: {primary['treated']} watered, {primary['controls']} never watered, "
          f"detectable {primary['mde_residual_sd_design_effect_1_and_2']} residual SD")


if __name__ == "__main__":
    main()
