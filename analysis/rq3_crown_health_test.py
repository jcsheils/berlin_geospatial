"""Check, design and outcome stages of the RQ3 crown-health test (docs/rq3_crown_health_protocol.md).

The stages read the per-tree tables that analysis/rq3_crown_health_extract.py writes on
GitHub Actions (copied to data/processed/rq3_crown_health/), never an image.

  check    image checks and consistency between flights, without any comparison by watering
  design   cohort and levels of care, validity of the outcome against later removal,
           smallest effect, noise floor, detectable differences and power
  outcome  primary tests, selection checks, survivor bounds and secondary analyses

Each stage needs the one before it, and every stage needs the frozen plan.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import rq3_crown_health_extract as extract
from analysis import rq3_crown_health_projection as crown
from analysis import rq3_four_year_projection as four_year
from analysis import rq3_one_year_survival as one_year
from analysis.build_feedback_benchmarks import Z_80

DATA = one_year.ROOT / "data/processed/rq3_crown_health"
OUT = crown.OUT
INVENTORY_2026 = one_year.ROOT / "data/Berlin_trees.gpkg"  # python tools/restore_tree_inventory.py
ONE_YEAR_RESULT = one_year.OUT / "corrected.json"
REPS = 5000
SEED = 42
Z95, Z90 = 1.959964, 1.644854
MIN_COVERAGE = 0.98
MAX_EYE_MISSES = 0.10
DELTA_AGES = (3, 15)
FALLBACK_SD = 0.2
MIN_CROWN_2025 = 0.1  # canopy fraction of the 2 m disc that still shows a crown at the 2025 flight
MIN_VALIDITY_REMOVALS = 30
MAX_SHADOW = 0.5
YEARS_BETWEEN_FLIGHTS = 5
FLIGHT_2023_START = dt.date(2023, 8, 14)  # flown 14 and 15 August 2023
INFRARED = ("2015", "2020", "2025")
FLIGHTS = ("2015", "2020", "2020rgb", "2023", "2025")
PAIRS = (("2015", "2020"), ("2020", "2025"))
REGIONS = extract.REGIONS
LEVELS = ("never", "occasional", "repeated", "sustained")

BASE = {"ages": crown.YOUNG_AGES, "last_planting": None, "treat": "dose", "later": "2025", "earlier": "2020",
        "region": "2m", "measure": "veg_ndvi", "method": "fe", "covariate": False, "minus_placebo": False,
        "minus_ring": False, "stable": False, "max_shadow": None}
SPECS = {
    "primary": {},
    "placebo_2015_2020": {"last_planting": crown.PLACEBO_LAST_PLANTING, "later": "2020", "earlier": "2015"},
    "older_16_40": {"ages": crown.OLDER_AGES},
    "primary_minus_placebo": {"last_planting": crown.PLACEBO_LAST_PLANTING, "minus_placebo": True},
    "s1_1m_circle": {"region": "1m"},
    "s2_3m_circle": {"region": "3m"},
    "s3_occasional": {"treat": "occasional"},
    "s3_repeated": {"treat": "repeated"},
    "s3_sustained": {"treat": "sustained"},
    "s4_any_log": {"treat": "watered"},
    "s5_500_l_or_more": {"treat": "high_dose"},
    "s6_logs_in_dry_2022": {"treat": "dry_2022"},
    "s7_with_trees_watered_before_2020": {"treat": "watered_any"},
    "s8_exact_matching": {"treat": "watered", "method": "exact"},
    "s9_adjusted_level": {"covariate": True},
    "s10_canopy_fraction": {"measure": "veg_frac"},
    "s11_disc_mean_ndvi": {"measure": "ndvi"},
    "s12_minus_background_ring": {"minus_ring": True},
    "s13_stable_surface_covariate": {"stable": True},
    "s14_without_shaded_discs": {"max_shadow": MAX_SHADOW},
    "s15_planted_by_2014": {"last_planting": crown.PLACEBO_LAST_PLANTING},
    "s16_2020_2023_green_share": {"treat": "watered_2023", "later": "2023", "earlier": "2020rgb", "measure": "gcc"},
}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp() -> dict:
    return {"protocol_sha256": file_hash(extract.PROTOCOL), "code_sha256": file_hash(Path(__file__))}


def index_of(flight: str) -> str:
    return extract.FLIGHTS[flight]["index"]


def measures(flight: str) -> tuple[str, ...]:
    return ("ndvi", "veg_frac", "veg_ndvi", "shadow_frac") if index_of(flight) == "ndvi" else ("gcc", "shadow_frac")


def spec_of(name_or_spec) -> dict:
    return {**BASE, **(SPECS[name_or_spec] if isinstance(name_or_spec, str) else name_or_spec)}


def is_trend(spec: dict) -> bool:
    return spec["treat"] == "dose"


def scale_of(spec: dict) -> float:
    """The trend coefficient is reported as the gain from no care to sustained care."""
    return float(crown.TOP_LEVEL) if is_trend(spec) else 1.0


def circles(flight: str, data: Path) -> pd.DataFrame | None:
    path = data / f"crown_circles_{flight}.csv.gz"
    return pd.read_csv(path, dtype={"tree_id": str, "window": str}).set_index("tree_id") if path.exists() else None


def window_table(flight: str, data: Path) -> pd.DataFrame | None:
    path = data / f"crown_windows_{flight}.csv.gz"
    return pd.read_csv(path, dtype={"window": str}, keep_default_na=False, na_values=[""]).set_index("window") if path.exists() else None


def full(table: pd.DataFrame, region: str) -> pd.Series:
    """True where the region lies wholly inside the image."""
    return table[f"in_image_{region}"].eq(table[f"pixels_{region}"]) & table[f"pixels_{region}"].gt(0)


def street_trees() -> pd.DataFrame:
    """Street trees planted 1980-2019 inside a planning area, with age in 2020."""
    trees = four_year.load_trees()
    trees = trees[trees["planting_year"].between(*extract.PLANTED) & trees["plr_id"].notna()].copy()
    trees["age_2020"] = crown.BASELINE_YEAR - trees["planting_year"]
    return trees


def attach_images(trees: pd.DataFrame, data: Path) -> pd.DataFrame:
    """Region values, full-region flags, window and stable-surface NDVI per flight. No watering data."""
    trees = trees.copy()
    for flight in FLIGHTS:
        table = circles(flight, data)
        if table is None:
            continue
        for region in REGIONS:
            for measure in measures(flight):
                if f"{measure}_{region}" in table:
                    trees[f"{measure}_{region}_{flight}"] = trees["tree_id"].map(table[f"{measure}_{region}"])
            trees[f"full_{region}_{flight}"] = trees["tree_id"].map(full(table, region)).fillna(False).astype(bool)
        trees[f"window_{flight}"] = trees["tree_id"].map(table["window"])
        log = window_table(flight, data)
        if log is not None and "stable_ndvi" in log:
            trees[f"stable_ndvi_{flight}"] = trees[f"window_{flight}"].map(pd.to_numeric(log["stable_ndvi"], errors="coerce"))
    return trees


def thresholds(data: Path) -> dict:
    out = {}
    for flight in FLIGHTS:
        path = data / f"crown_circles_{flight}.json"
        if path.exists():
            out[flight] = json.loads(path.read_text()).get("thresholds")
    return out


# ---------------------------------------------------------------- check

def flight_consistency(young: pd.DataFrame) -> dict:
    """Per pair of infrared flights: the shift in stable-surface NDVI between windows, and how it
    tracks the window's mean change in crown greenness. Descriptive; no watering data."""
    out = {}
    for earlier, later in PAIRS:
        columns = [f"stable_ndvi_{earlier}", f"stable_ndvi_{later}", f"veg_ndvi_2m_{earlier}", f"veg_ndvi_2m_{later}", f"window_{later}"]
        if any(c not in young for c in columns):
            continue
        frame = young[young[f"full_2m_{earlier}"] & young[f"full_2m_{later}"]]
        windows = (frame.assign(stable=frame[columns[1]] - frame[columns[0]], green=frame[columns[3]] - frame[columns[2]])
                   .groupby(columns[4]).agg(stable=("stable", "first"), green=("green", "mean")).dropna())
        if windows.empty:
            continue
        q = windows["stable"].quantile([0.25, 0.5, 0.75])
        out[f"{earlier}_{later}"] = {
            "windows": int(len(windows)),
            "stable_ndvi_shift_median": float(q[0.5]), "stable_ndvi_shift_iqr": [float(q[0.25]), float(q[0.75])],
            "spearman_stable_shift_vs_mean_greenness_change": float(windows["stable"].corr(windows["green"], method="spearman"))
            if len(windows) > 2 else None,
        }
    return out


def check(data: Path = DATA, out: Path = OUT) -> dict:
    """Image checks and consistency between flights, without any comparison by watering; no logs are read."""
    extract.require_freeze()
    trees = attach_images(street_trees(), data)
    young = trees[trees["age_2020"].between(*crown.YOUNG_AGES)]
    responses = {}
    for flight in FLIGHTS:
        path = data / f"crown_windows_{flight}.csv.gz"
        if path.exists():
            log = pd.read_csv(path, dtype=str, keep_default_na=False)
            responses[flight] = {"windows": int(len(log)), "failed": int(log["error"].ne("").sum()),
                                 "wrong_image": int(log["error"].str.contains("expected").sum())}
    cross = {f: json.loads((data / f"{f}_crosscheck.json").read_text()) for f in INFRARED if (data / f"{f}_crosscheck.json").exists()}
    covered = pd.Series(True, index=young.index)
    for flight in ("2020", "2025"):
        column = f"full_2m_{flight}"
        covered &= young[column] if column in young else False
    coverage = float(covered.mean()) if len(covered) else 0.0
    eye_path = data / "eye_check.csv"
    eye = pd.read_csv(eye_path, dtype=str, keep_default_na=False) if eye_path.exists() else pd.DataFrame({"on_tree": []})
    answers = eye["on_tree"].str.strip().str.lower()
    eye_complete = len(eye) == extract.EYE_CHECK_TREES and bool(answers.isin(["yes", "no"]).all())
    misses = float((answers == "no").mean()) if len(eye) else 1.0
    set_thresholds = thresholds(data)
    checks = {
        "responses_are_three_band_images_of_the_requested_size": set(INFRARED) <= set(responses) and all(r["wrong_image"] == 0 for r in responses.values()),
        "colour_infrared_and_colour_layers_agree": set(cross) == set(INFRARED) and all(c["passes"] for c in cross.values()),
        "thresholds_set_for_every_infrared_flight": all((set_thresholds.get(f) or {}).get("vegetation") is not None for f in INFRARED),
        "young_circles_inside_2020_and_2025_images_at_least_98_pct": coverage >= MIN_COVERAGE,
        "eye_check_at_most_10_pct_miss": eye_complete and misses <= MAX_EYE_MISSES,
    }
    result = {
        "stage": "check", "passes": all(checks.values()), "checks": checks,
        "responses": responses,
        "layer_differences": {f: {"red": c["red_median_abs_diff"], "green": c["green_median_abs_diff"]} for f, c in cross.items()},
        "thresholds": set_thresholds,
        "flight_consistency": flight_consistency(young),
        "young_trees": int(len(young)), "young_circles_inside_both_images_pct": round(100 * coverage, 2),
        "eye_check": {"complete": eye_complete, "rated": int(answers.isin(["yes", "no"]).sum()), "miss_pct": round(100 * misses, 1)},
        **stamp(),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "check.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


# ---------------------------------------------------------------- tables

def tree_table(data: Path) -> pd.DataFrame:
    """Street trees with levels of care, exposure flags and image values per flight and region."""
    trees = street_trees()
    logs = one_year.load_raw_logs()
    trees = crown.exposure(trees, logs)
    trees["watered_any"] = trees["watered"] | trees["watered_before_baseline"]
    by_2023 = logs[(logs["date"] > crown.BASELINE_FLIGHT_END) & (logs["date"] < FLIGHT_2023_START)]
    trees["watered_2023"] = trees["pitid"].isin(set(by_2023["tree_id"])) & ~trees["watered_before_baseline"]
    return attach_images(trees, data)


def build(trees: pd.DataFrame, spec) -> pd.DataFrame | None:
    """Analysis sample: outcome y, care t (level 0-3 or 0/1), optional covariates x and s, grouping columns."""
    s = spec_of(spec)
    flights = [s["earlier"], s["later"]] + (["2015"] if s["minus_placebo"] else [])
    region, measure = s["region"], s["measure"]
    regions = [region] + (["ring"] if s["minus_ring"] else [])
    needed = [f"{kind}_{r}_{f}" for r in regions for f in flights for kind in (measure, "full")]
    needed += [f"stable_ndvi_{f}" for f in flights] if s["stable"] else []
    needed += [f"shadow_frac_{region}_{f}" for f in flights] if s["max_shadow"] is not None else []
    if any(c not in trees for c in needed):
        return None
    frame = trees[trees["age_2020"].between(*s["ages"])]
    if s["last_planting"] is not None:
        frame = frame[frame["planting_year"] <= s["last_planting"]]
    frame = frame[frame["dose"].notna()] if is_trend(s) else frame[frame[s["treat"]] | frame["never"]]
    t = frame["dose" if is_trend(s) else s["treat"]].to_numpy(float)

    def value(r: str, f: str) -> np.ndarray:
        return frame[f"{measure}_{r}_{f}"].to_numpy(float)

    def change(r: str) -> np.ndarray:
        step = value(r, s["later"]) - value(r, s["earlier"])
        return step - (value(r, s["earlier"]) - value(r, "2015")) if s["minus_placebo"] else step

    y = value(region, s["later"]) if s["covariate"] else change(region)
    if s["minus_ring"]:
        y = y - change("ring")
    keep = np.isfinite(y) & np.logical_and.reduce([frame[f"full_{r}_{f}"].to_numpy(bool) for r in regions for f in flights])
    sample = pd.DataFrame({"y": y, "t": t, "plr_id": frame["plr_id"].to_numpy(),
                           "planting_year": frame["planting_year"].to_numpy(), "genus_group": frame["genus_group"].to_numpy()})
    if s["covariate"]:
        sample["x"] = value(region, s["earlier"])
    if s["stable"]:
        sample["s"] = frame[f"stable_ndvi_{s['later']}"].to_numpy(float) - frame[f"stable_ndvi_{s['earlier']}"].to_numpy(float)
    for column in ("x", "s"):
        if column in sample:
            keep &= np.isfinite(sample[column].to_numpy(float))
    if s["max_shadow"] is not None:
        for f in flights:
            keep &= frame[f"shadow_frac_{region}_{f}"].to_numpy(float) <= s["max_shadow"]
    return sample[keep].reset_index(drop=True)


def counts(sample: pd.DataFrame, spec) -> dict:
    t = sample["t"].to_numpy(float)
    out = {"treated": int((t > 0).sum()), "controls": int((t == 0).sum())}
    if is_trend(spec_of(spec)):
        out["by_level"] = {name: int((t == value).sum()) for value, name in enumerate(LEVELS)}
    return out


def keys(sample: pd.DataFrame) -> list[np.ndarray]:
    return [sample.groupby(g).ngroup().to_numpy() for g in crown.FIXED_EFFECTS]


# ---------------------------------------------------------------- estimators

def demean(matrix: np.ndarray, groups: list[np.ndarray], tol: float = 1e-10, max_sweeps: int = 1000) -> np.ndarray:
    """Columns of `matrix` with additive fixed effects swept out (alternating projections)."""
    x = matrix - matrix.mean(axis=0)
    counts_ = [np.maximum(np.bincount(g), 1) for g in groups]
    for _ in range(max_sweeps):
        worst = 0.0
        for g, count in zip(groups, counts_):
            for j in range(x.shape[1]):
                means = np.bincount(g, x[:, j], minlength=len(count)) / count
                x[:, j] -= means[g]
                worst = max(worst, float(np.abs(means).max()))
        if worst < tol:
            break
    return x


def fe_fit(y: np.ndarray, X: np.ndarray, groups: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Coefficients on X after the fixed effects, the residuals and the swept regressors."""
    z = demean(np.column_stack([y, X]), groups)
    rx = z[:, 1:]
    beta = np.linalg.lstsq(rx, z[:, 0], rcond=None)[0]
    return beta, z[:, 0] - rx @ beta, rx


def cluster_se(rx: np.ndarray, residual: np.ndarray, cluster: np.ndarray) -> float:
    """Cluster-robust standard error of the first coefficient (small-sample factor G / (G - 1))."""
    ids, index = np.unique(cluster, return_inverse=True)
    scores = np.zeros((len(ids), rx.shape[1]))
    np.add.at(scores, index, rx * residual[:, None])
    bread = np.linalg.inv(rx.T @ rx)
    variance = len(ids) / (len(ids) - 1) * bread @ (scores.T @ scores) @ bread
    return math.sqrt(float(variance[0, 0]))


def exact_att(y: np.ndarray, t: np.ndarray, stratum: np.ndarray) -> float:
    """Treated minus matched-control mean, weighting strata by their treated trees."""
    k = int(stratum.max()) + 1
    n1, n0 = np.bincount(stratum, t, k), np.bincount(stratum, ~t, k)
    s1, s0 = np.bincount(stratum, y * t, k), np.bincount(stratum, y * ~t, k)
    both = (n1 > 0) & (n0 > 0)
    return float(((s1[both] / n1[both]) - (s0[both] / n0[both])) @ n1[both] / n1[both].sum())


def regressors(sample: pd.DataFrame) -> np.ndarray:
    return np.column_stack([sample["t"].to_numpy(float)] + [sample[c].to_numpy(float) for c in ("x", "s") if c in sample])


def estimator(sample: pd.DataFrame, spec):
    """A function of row indices returning the care coefficient, scaled to the reported estimate."""
    s = spec_of(spec)
    y, t = sample["y"].to_numpy(float), sample["t"].to_numpy(float)
    if s["method"] == "exact":
        stratum = sample.groupby(crown.EXACT_STRATA).ngroup().to_numpy()
        treated = t > 0
        return lambda rows: exact_att(y[rows], treated[rows], stratum[rows])
    X, groups, scale = regressors(sample), keys(sample), scale_of(s)
    return lambda rows: scale * float(fe_fit(y[rows], X[rows], [g[rows] for g in groups])[0][0])


def bootstrap(sample: pd.DataFrame, fit, reps: int, seed: int = SEED) -> np.ndarray:
    """Coefficients from resampling planning areas with replacement."""
    cluster = sample["plr_id"].to_numpy()
    order = np.argsort(cluster, kind="stable")
    ids, starts = np.unique(cluster[order], return_index=True)
    members = np.split(order, starts[1:])
    rng = np.random.default_rng(seed)
    draws = np.empty(reps)
    for rep in range(reps):
        rows = np.concatenate([members[i] for i in rng.integers(0, len(ids), len(ids))])
        draws[rep] = fit(rows)
    return draws


def interpret(ci95: list[float], upper90: float, delta: float) -> str:
    if ci95[0] > 0:
        return ("More care went with greener crowns, by less than Δ at sustained care" if upper90 < delta
                else "More care went with greener crowns; whether by Δ or more at sustained care stays open")
    if ci95[1] < 0:
        return "More care went with less green crowns; residents may water trees that look stressed"
    if upper90 < delta:
        return "No gain detected; a gain of Δ or more at sustained care is ruled out"
    return "Inconclusive; report the largest gain the interval does not exclude"


def same_direction(ci95: list[float], primary: float) -> bool:
    """True when an interval excludes zero on the side of the primary estimate."""
    return (primary > 0 and ci95[0] > 0) or (primary < 0 and ci95[1] < 0)


def residual_sd(sample: pd.DataFrame) -> float:
    return float(np.sqrt((demean(sample[["y"]].to_numpy(float), keys(sample)) ** 2).sum() / (len(sample) - 1)))


# ---------------------------------------------------------------- design

def smallest_effect(trees: pd.DataFrame, primary: pd.DataFrame) -> dict:
    """Half the one-year gain in 2020 crown greenness with age (ages 3-15, pooled over watering)."""
    column = "veg_ndvi_2m_2020"
    base = trees[trees["age_2020"].between(*DELTA_AGES) & trees["full_2m_2020"] & trees[column].notna()]
    age, green = base["age_2020"].to_numpy(float), base[column].to_numpy(float)
    slope = float(np.polyfit(age, green, 1)[0]) if len(base) > 2 and age.std() > 0 else float("nan")
    pooled_sd = float(primary["y"].std(ddof=1))
    if slope > 0:
        return {"delta": slope / 2, "rule": "half the one-year gain with age", "age_slope": slope, "trees_for_slope": int(len(base)), "pooled_sd_of_change": pooled_sd}
    return {"delta": FALLBACK_SD * pooled_sd, "rule": "0.2 SD of the pooled change (age slope not positive)", "age_slope": slope,
            "trees_for_slope": int(len(base)), "pooled_sd_of_change": pooled_sd}


def removal_status(tree_ids: pd.Series, inventory: Path) -> np.ndarray:
    """Removed between the 2025 and 2026 inventories (identifier gone and not re-keyed)."""
    if not inventory.exists():
        raise SystemExit(f"The validity check needs the 2026 inventory at {inventory}; run python tools/restore_tree_inventory.py.")
    return one_year.attach_outcomes(pd.DataFrame({"tree_id": tree_ids.to_numpy()}), inventory)["removed"].to_numpy(bool)


def auc(score: np.ndarray, event: np.ndarray) -> float:
    """Probability that a removed tree scores higher than a kept one (ties count half)."""
    ranks = pd.Series(score).rank().to_numpy()
    n1, n0 = int(event.sum()), int((~event).sum())
    return float((ranks[event].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")


def validity(trees: pd.DataFrame, removed_of) -> dict:
    """Does a fall in crown greenness from 2020 to 2025 predict removal by the 2026 inventory?

    Young trees whose 2 m discs lie inside both images and still show a crown in 2025.
    A linear probability model with the primary fixed effects; no watering data.
    """
    young = trees[trees["age_2020"].between(*crown.YOUNG_AGES)]
    columns = ["veg_ndvi_2m_2020", "veg_ndvi_2m_2025", "veg_frac_2m_2020", "veg_frac_2m_2025"]
    if any(c not in young for c in columns):
        return {"passes": False, "evaluable": False, "reason": "image tables missing"}
    frame = young[young["full_2m_2020"] & young["full_2m_2025"] & young[columns].notna().all(axis=1)
                  & (young["veg_frac_2m_2025"] >= MIN_CROWN_2025)].copy()
    removed = removed_of(frame["tree_id"])
    frame["removed"] = removed.astype(float)
    sample = frame.rename(columns={"removed": "y"})
    groups = keys(sample)
    out = {"trees": int(len(frame)), "removals": int(removed.sum()), "removal_pct": round(100 * float(removed.mean()), 2) if len(frame) else None,
           "min_canopy_fraction_2025": MIN_CROWN_2025}
    if out["removals"] < MIN_VALIDITY_REMOVALS:
        return {**out, "passes": False, "evaluable": False, "reason": f"fewer than {MIN_VALIDITY_REMOVALS} removals"}
    predictors = {
        "greenness_change": frame["veg_ndvi_2m_2025"] - frame["veg_ndvi_2m_2020"],
        "canopy_fraction_change": frame["veg_frac_2m_2025"] - frame["veg_frac_2m_2020"],
        "greenness_2025": frame["veg_ndvi_2m_2025"],
    }
    models = {}
    for name, predictor in predictors.items():
        z = ((predictor - predictor.mean()) / predictor.std(ddof=1)).to_numpy(float)
        beta, residual, rx = fe_fit(sample["y"].to_numpy(float), z[:, None], groups)
        se = cluster_se(rx, residual, sample["plr_id"].to_numpy())
        models[name] = {"pp_per_sd": 100 * float(beta[0]), "ci95_pp": [100 * float(beta[0] - Z95 * se), 100 * float(beta[0] + Z95 * se)],
                        "auc_lower_scores_removed": auc(-z, removed)}
    passes = models["greenness_change"]["ci95_pp"][1] < 0
    return {**out, "passes": bool(passes), "evaluable": True, "models": models,
            "rule": "passes if the 95% interval for greenness change lies below zero (a fall goes with removal)"}


def analysis_entry(sample: pd.DataFrame | None, name: str) -> dict:
    if sample is None:
        return {"available": False}
    spec = spec_of(name)
    entry = {"available": True, **counts(sample, spec)}
    if not (entry["treated"] and entry["controls"]):
        entry["available"] = False
    elif spec["method"] == "fe":
        per = crown.standardised_mde(sample.assign(care=sample["t"]), "care")
        entry["mde_residual_sd_design_effect_1_and_2"] = [round(scale_of(spec) * m, 3) for m in per]
    return entry


def design(data: Path = DATA, out: Path = OUT, inventory: Path = INVENTORY_2026, removed_of=None) -> dict:
    extract.require_freeze()
    checked = json.loads((out / "check.json").read_text()) if (out / "check.json").exists() else {}
    if not checked.get("passes"):
        raise SystemExit("The check stage has not passed; the design stage does not run.")
    trees = tree_table(data)
    valid = validity(trees, removed_of or (lambda ids: removal_status(ids, inventory)))
    samples = {name: build(trees, name) for name in SPECS}
    primary = samples["primary"]
    effect = smallest_effect(trees, primary)
    sd = residual_sd(primary)
    floor = build(trees, {"ages": crown.OLDER_AGES, "treat": "watered"})
    floor = floor[floor["t"] == 0] if floor is not None else None
    analyses = {name: analysis_entry(sample, name) for name, sample in samples.items()}
    mde_sd = analyses["primary"]["mde_residual_sd_design_effect_1_and_2"]
    se = [m * sd / Z_80 for m in mde_sd]
    result = {
        "stage": "design",
        "validity": valid,
        "smallest_effect": effect,
        "primary_residual_sd_of_change": sd,
        "noise_floor_residual_sd_never_watered_16_40": residual_sd(floor) if floor is not None and len(floor) > 2 else None,
        "primary_mde_greenness_design_effect_1_and_2": [round(m * sd, 5) for m in mde_sd],
        "power_pct_test_a_if_gain_equals_delta": [round(100 * four_year.power(s, effect["delta"], Z95), 1) for s in se],
        "power_pct_test_b_if_no_difference": [round(100 * four_year.power(s, effect["delta"], Z90), 1) for s in se],
        "analyses": analyses,
        "inputs_sha256": {f.name: file_hash(f) for f in sorted(data.glob("crown_*.csv.gz"))},
        **stamp(),
    }
    (out / "design.json").write_text(json.dumps(result, indent=2, default=float) + "\n")
    return result


# ---------------------------------------------------------------- outcome

def estimate(sample: pd.DataFrame, name: str, reps: int) -> dict:
    spec = spec_of(name)
    fit = estimator(sample, spec)
    point = fit(np.arange(len(sample)))
    draws = bootstrap(sample, fit, reps)
    out = {
        **counts(sample, spec), "planning_areas": int(sample["plr_id"].nunique()),
        "estimand": "gain from no care to sustained care (3 x trend)" if is_trend(spec) else "treated minus never watered",
        "difference": point,
        "ci95_bootstrap": [float(q) for q in np.quantile(draws, [0.025, 0.975])],
        "ci90_bootstrap": [float(q) for q in np.quantile(draws, [0.05, 0.95])],
    }
    if spec["method"] == "fe":
        _, residual, rx = fe_fit(sample["y"].to_numpy(float), regressors(sample), keys(sample))
        se = scale_of(spec) * cluster_se(rx, residual, sample["plr_id"].to_numpy())
        out["ci95_cluster_robust"] = [point - Z95 * se, point + Z95 * se]
    return out


def survivor_bounds(sample: pd.DataFrame, primary: dict, one_year_result: Path = ONE_YEAR_RESULT) -> dict:
    """The primary estimate if trees removed before 2025 had been seen, over a grid of assumptions.

    G_full = G (1 - r_t) + (r_c - r_t)(m_c - L): r_t and r_c are the shares removed over five
    years among cared-for and never-watered trees, m_c the never-watered mean change and L
    the change a removed tree would show. Treats the gain at sustained care as a two-group
    difference, so it is approximate for the trend.
    """
    rates = json.loads(one_year_result.read_text())["analyses"]["primary_any_log_2020_2024_age_0_15"]
    p_t, p_c = rates["risk_treated_pct"] / 100, rates["risk_matched_control_pct"] / 100
    five = lambda p: 1 - (1 - p) ** YEARS_BETWEEN_FLIGHTS
    shares = {"observed_rates": (five(p_t), five(p_c)), "rates_swapped": (five(p_c), five(p_t)), "equal_rates": (five(p_c), five(p_c))}
    control = sample.loc[sample["t"] == 0, "y"]
    m_c = float(control.mean())
    losses = {"removed_tree_at_1st_percentile": float(control.quantile(0.01)), "removed_tree_at_median": float(control.median())}
    adjust = lambda g, rt, rc, loss: g * (1 - rt) + (rc - rt) * (m_c - loss)
    grid = []
    for share, (rt, rc) in shares.items():
        for name, loss in losses.items():
            grid.append({"shares": share, "removed_cared_for": rt, "removed_never_watered": rc, "removed_outcome": name,
                         "difference": adjust(primary["difference"], rt, rc, loss),
                         "ci95": [adjust(primary["ci95_bootstrap"][0], rt, rc, loss), adjust(primary["ci95_bootstrap"][1], rt, rc, loss)]})
    return {"grid": grid, "difference_range": [min(g["difference"] for g in grid), max(g["difference"] for g in grid)],
            "widest_ci95": [min(g["ci95"][0] for g in grid), max(g["ci95"][1] for g in grid)],
            "removal_rates_from": str(one_year_result.relative_to(one_year.ROOT)) if one_year_result.is_relative_to(one_year.ROOT) else str(one_year_result)}


def outcome(data: Path = DATA, out: Path = OUT, reps: int = REPS, one_year_result: Path = ONE_YEAR_RESULT) -> dict:
    extract.require_freeze()
    planned = json.loads((out / "design.json").read_text())
    if planned["protocol_sha256"] != stamp()["protocol_sha256"]:
        raise SystemExit("The plan changed after the design stage; the outcome stage does not run.")
    trees = tree_table(data)
    samples = {name: build(trees, name) for name in SPECS}
    for name, sample in samples.items():
        expected = planned["analyses"][name]
        found = {"available": False} if sample is None else counts(sample, name)
        if any(expected.get(k) != v for k, v in found.items()):
            raise SystemExit(f"{name}: the sample differs from the design stage ({found} against {expected}).")
    if not planned["analyses"]["primary"]["available"]:
        raise SystemExit("The primary sample has no cared-for or no control trees.")
    delta = planned["smallest_effect"]["delta"]
    results = {name: (estimate(sample, name, reps) if planned["analyses"][name]["available"] else planned["analyses"][name])
               for name, sample in samples.items()}
    primary = results["primary"]
    primary["test_a_gain"] = primary["ci95_bootstrap"][0] > 0
    primary["test_b_gain_of_delta_ruled_out"] = primary["ci90_bootstrap"][1] < delta
    primary["report"] = interpret(primary["ci95_bootstrap"], primary["ci90_bootstrap"][1], delta)
    primary["largest_gain_not_excluded"] = primary["ci95_bootstrap"][1]
    flags = {name: same_direction(results[name]["ci95_bootstrap"], primary["difference"])
             for name in ("placebo_2015_2020", "older_16_40") if "difference" in results[name]}
    valid = planned["validity"]["passes"]
    result = {
        "stage": "outcome", "delta": delta,
        "outcome_reading": "crown condition" if valid else "crown greenness only; the validity check did not link it to removal",
        "bootstrap": {"reps": reps, "seed": SEED, "cluster": "planning area"},
        "primary": primary,
        "selection_checks": {"same_direction_as_primary": flags, "primary_reported_as_likely_selection": any(flags.values())},
        "s17_survivor_bounds": survivor_bounds(samples["primary"], primary, one_year_result),
        "secondary": {name: r for name, r in results.items() if name != "primary"},
        "s18_without_survivor_selection": "awaits CityLAB's 2020 tree table and full log history",
        "inputs_sha256": planned["inputs_sha256"],
        **stamp(),
    }
    (out / "outcome.json").write_text(json.dumps(result, indent=2, default=float) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["check", "design", "outcome"])
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_2026, help="2026 inventory (design stage)")
    args = parser.parse_args()
    if args.stage == "design":
        result = design(args.data, inventory=args.inventory)
    else:
        result = {"check": check, "outcome": outcome}[args.stage](args.data)
    summary = {k: result[k] for k in ("passes", "checks", "validity", "smallest_effect", "primary_mde_greenness_design_effect_1_and_2",
                                      "outcome_reading", "primary") if k in result}
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
