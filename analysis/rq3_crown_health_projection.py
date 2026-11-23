"""Projected sample for the RQ3 crown-health test (docs/rq3_crown_health_protocol.md).

The test relates the change in crown greenness between the August 2020 and August 2025
aerial images to the level of logged care between the flights (none, occasional,
repeated, sustained) for young street trees. This script counts those trees and the
detectable differences in units of the outcome's residual standard deviation. It uses
the 2025 inventory and the open log export only and opens no image.
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
REPEATED_DAYS = 3  # log days in one season that make care repeated
SUSTAINED_SEASONS = 3  # seasons with logs that make care sustained
TOP_LEVEL = 3  # sustained; the primary estimate is the trend's gain from none to sustained
DRY_SEASON = 2022


def dose_level(watered: pd.Series, days: pd.Series, seasons: pd.Series) -> pd.Series:
    """0 never, 1 occasional, 2 repeated (three or more log days in a season, or two seasons),
    3 sustained (three or more seasons). Missing for trees watered before the first flight."""
    level = pd.Series(np.where(watered, 1.0, 0.0), index=watered.index)
    level[watered & ((days >= REPEATED_DAYS) | (seasons >= 2))] = 2.0
    level[watered & (seasons >= SUSTAINED_SEASONS)] = 3.0
    return level


def exposure(cohort: pd.DataFrame, logs: pd.DataFrame) -> pd.DataFrame:
    """Flag trees watered between the two flights, before the first, or never before the second,
    and the level of care between the flights."""
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
    level = dose_level(out["watered"], tree(seasons["days"]).fillna(0), tree(seasons["seasons"]).fillna(0))
    out["dose"] = level.where(out["watered"] | out["never"])
    for value, name in ((1, "occasional"), (2, "repeated"), (3, "sustained")):
        out[name] = out["dose"].eq(value)
    out["dry_2022"] = out["watered"] & cohort["pitid"].isin(set(between.loc[between["year"] == DRY_SEASON, "tree_id"]))
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


def describe_trend(frame: pd.DataFrame) -> dict:
    """Trees per level of care and the detectable gain from none to sustained implied by a linear trend."""
    sample = frame[frame["dose"].notna()].dropna(subset=["plr_id"])
    per_step = standardised_mde(sample, "dose")
    return {
        "trees_by_level": {name: int(sample["dose"].eq(v).sum()) for v, name in enumerate(("never", "occasional", "repeated", "sustained"))},
        "mde_residual_sd_design_effect_1_and_2": [round(TOP_LEVEL * m, 3) for m in per_step],
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
            "primary_dose_trend": describe_trend(young),
            "s_any_log_between_flights": describe(young, "watered"),
            "s_level_occasional": describe(young, "occasional"),
            "s_level_repeated": describe(young, "repeated"),
            "s_level_sustained": describe(young, "sustained"),
            "s_timing_logs_in_dry_2022": describe(young, "dry_2022"),
            "s_dose_500_l_or_more_in_a_season": describe(young, "high_dose"),
            "placebo_2015_2020_planted_by_2014": describe_trend(placebo),
            "negative_control_age_16_40": describe_trend(older),
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result = project()
    (OUT / "projection.json").write_text(json.dumps(result, indent=2) + "\n")
    primary = result["analyses"]["primary_dose_trend"]
    print(f"primary: {primary['trees_by_level']}, detectable gain at sustained care "
          f"{primary['mde_residual_sd_design_effect_1_and_2']} residual SD")


if __name__ == "__main__":
    main()
