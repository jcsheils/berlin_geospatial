"""Check, design and outcome stages of the RQ3 crown-health test (docs/rq3_crown_health_protocol.md).

The stages read the per-tree circle tables that analysis/rq3_crown_health_extract.py
writes on GitHub Actions (copied to data/processed/rq3_crown_health/), never an image.

  check    image checks, without any comparison by watering
  design   cohort, exposure, smallest effect, detectable differences and power
  outcome  primary tests, selection checks and secondary analyses

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
REPS = 5000
SEED = 42
Z95, Z90 = 1.959964, 1.644854
MIN_COVERAGE = 0.98
MAX_EYE_MISSES = 0.10
DELTA_AGES = (3, 15)
FALLBACK_SD = 0.2
FLIGHT_2023_START = dt.date(2023, 8, 14)  # flown 14 and 15 August 2023
INFRARED = ("2015", "2020", "2025")
FLIGHTS = ("2015", "2020", "2020rgb", "2023", "2025")
RADII = ("1m", "2m", "3m")

BASE = {"ages": crown.YOUNG_AGES, "last_planting": None, "treat": "watered", "later": "2025", "earlier": "2020",
        "radius": "2m", "index": "ndvi", "method": "fe", "covariate": False, "minus_placebo": False}
SPECS = {
    "primary": {},
    "placebo_2015_2020": {"last_planting": crown.PLACEBO_LAST_PLANTING, "later": "2020", "earlier": "2015"},
    "older_16_40": {"ages": crown.OLDER_AGES},
    "primary_minus_placebo": {"last_planting": crown.PLACEBO_LAST_PLANTING, "minus_placebo": True},
    "s1_1m_circle": {"radius": "1m"},
    "s2_3m_circle": {"radius": "3m"},
    "s3_three_log_days": {"treat": "three_days"},
    "s3_two_or_more_seasons": {"treat": "two_seasons"},
    "s3_500_l_or_more": {"treat": "high_dose"},
    "s4_with_trees_watered_before_2020": {"treat": "watered_any"},
    "s5_exact_matching": {"method": "exact"},
    "s6_adjusted_level": {"covariate": True},
    "s7_2020_2023_green_share": {"treat": "watered_2023", "later": "2023", "earlier": "2020rgb", "index": "gcc"},
    "s9_planted_by_2014": {"last_planting": crown.PLACEBO_LAST_PLANTING},
}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp() -> dict:
    return {"protocol_sha256": file_hash(extract.PROTOCOL), "code_sha256": file_hash(Path(__file__))}


def index_of(flight: str) -> str:
    return extract.FLIGHTS[flight]["index"]


def circles(flight: str, data: Path) -> pd.DataFrame | None:
    path = data / f"crown_circles_{flight}.csv.gz"
    return pd.read_csv(path, dtype={"tree_id": str, "window": str}).set_index("tree_id") if path.exists() else None


def full(table: pd.DataFrame, radius: str) -> pd.Series:
    """True where the circle lies wholly inside the image."""
    return table[f"in_image_{radius}"].eq(table[f"pixels_{radius}"]) & table[f"pixels_{radius}"].gt(0)


def street_trees() -> pd.DataFrame:
    """Street trees planted 1980-2019 inside a planning area, with age in 2020."""
    trees = four_year.load_trees()
    trees = trees[trees["planting_year"].between(*extract.PLANTED) & trees["plr_id"].notna()].copy()
    trees["age_2020"] = crown.BASELINE_YEAR - trees["planting_year"]
    return trees


# ---------------------------------------------------------------- check

def check(data: Path = DATA, out: Path = OUT) -> dict:
    """Image checks without any comparison by watering; no logs are read."""
    extract.require_freeze()
    trees = street_trees()
    young = trees[trees["age_2020"].between(*crown.YOUNG_AGES)]
    responses = {}
    for flight in FLIGHTS:
        path = data / f"crown_windows_{flight}.csv.gz"
        if path.exists():
            log = pd.read_csv(path, dtype=str, keep_default_na=False)
            responses[flight] = {"windows": int(len(log)), "failed": int(log["error"].ne("").sum()),
                                 "wrong_image": int(log["error"].str.contains("expected").sum())}
    cross = {f: json.loads((data / f"{f}_crosscheck.json").read_text()) for f in INFRARED if (data / f"{f}_crosscheck.json").exists()}
    covered = pd.Series(True, index=young["tree_id"])
    for flight in ("2020", "2025"):
        table = circles(flight, data)
        covered &= young["tree_id"].map(full(table, "2m")).fillna(False).astype(bool).to_numpy() if table is not None else False
    coverage = float(covered.mean()) if len(covered) else 0.0
    eye_path = data / "eye_check.csv"
    eye = pd.read_csv(eye_path, dtype=str, keep_default_na=False) if eye_path.exists() else pd.DataFrame({"on_tree": []})
    answers = eye["on_tree"].str.strip().str.lower()
    eye_complete = len(eye) == extract.EYE_CHECK_TREES and bool(answers.isin(["yes", "no"]).all())
    misses = float((answers == "no").mean()) if len(eye) else 1.0
    checks = {
        "responses_are_three_band_images_of_the_requested_size": set(INFRARED) <= set(responses) and all(r["wrong_image"] == 0 for r in responses.values()),
        "colour_infrared_and_colour_layers_agree": set(cross) == set(INFRARED) and all(c["passes"] for c in cross.values()),
        "young_circles_inside_2020_and_2025_images_at_least_98_pct": coverage >= MIN_COVERAGE,
        "eye_check_at_most_10_pct_miss": eye_complete and misses <= MAX_EYE_MISSES,
    }
    result = {
        "stage": "check", "passes": all(checks.values()), "checks": checks,
        "responses": responses,
        "layer_differences": {f: {"red": c["red_median_abs_diff"], "green": c["green_median_abs_diff"]} for f, c in cross.items()},
        "young_trees": int(len(young)), "young_circles_inside_both_images_pct": round(100 * coverage, 2),
        "eye_check": {"complete": eye_complete, "rated": int(answers.isin(["yes", "no"]).sum()), "miss_pct": round(100 * misses, 1)},
        **stamp(),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "check.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


# ---------------------------------------------------------------- tables

def tree_table(data: Path) -> pd.DataFrame:
    """Street trees with exposure flags and circle values per flight and radius."""
    trees = street_trees()
    logs = one_year.load_raw_logs()
    trees = crown.exposure(trees, logs)
    trees["watered_any"] = trees["watered"] | trees["watered_before_baseline"]
    by_2023 = logs[(logs["date"] > crown.BASELINE_FLIGHT_END) & (logs["date"] < FLIGHT_2023_START)]
    trees["watered_2023"] = trees["pitid"].isin(set(by_2023["tree_id"])) & ~trees["watered_before_baseline"]
    for flight in FLIGHTS:
        table = circles(flight, data)
        if table is None:
            continue
        for radius in RADII:
            trees[f"{index_of(flight)}_{radius}_{flight}"] = trees["tree_id"].map(table[f"{index_of(flight)}_{radius}"])
            trees[f"full_{radius}_{flight}"] = trees["tree_id"].map(full(table, radius)).fillna(False).astype(bool)
    return trees


def build(trees: pd.DataFrame, spec: dict) -> pd.DataFrame | None:
    """Analysis sample: outcome y, treatment t, optional covariate x and the grouping columns."""
    s = {**BASE, **spec}
    flights = [s["earlier"], s["later"]] + (["2015"] if s["minus_placebo"] else [])
    radius, index = s["radius"], s["index"]
    if any(f"full_{radius}_{f}" not in trees for f in flights):
        return None
    frame = trees[trees["age_2020"].between(*s["ages"])]
    if s["last_planting"] is not None:
        frame = frame[frame["planting_year"] <= s["last_planting"]]
    frame = frame[frame[s["treat"]] | frame["never"]]
    value = {f: frame[f"{index}_{radius}_{f}"] for f in flights}
    y = value[s["later"]] if s["covariate"] else value[s["later"]] - value[s["earlier"]]
    if s["minus_placebo"]:
        y = y - (value[s["earlier"]] - value["2015"])
    keep = np.logical_and.reduce([frame[f"full_{radius}_{f}"].to_numpy() for f in flights]) & y.notna().to_numpy()
    keep &= np.logical_and.reduce([v.notna().to_numpy() for v in value.values()])
    sample = pd.DataFrame({"y": y.to_numpy(), "t": frame[s["treat"]].to_numpy(), "plr_id": frame["plr_id"].to_numpy(),
                           "planting_year": frame["planting_year"].to_numpy(), "genus_group": frame["genus_group"].to_numpy()})
    if s["covariate"]:
        sample["x"] = value[s["earlier"]].to_numpy()
    return sample[keep].reset_index(drop=True)


def keys(sample: pd.DataFrame) -> list[np.ndarray]:
    return [sample.groupby(g).ngroup().to_numpy() for g in crown.FIXED_EFFECTS]


# ---------------------------------------------------------------- estimators

def demean(matrix: np.ndarray, groups: list[np.ndarray], tol: float = 1e-10, max_sweeps: int = 1000) -> np.ndarray:
    """Columns of `matrix` with additive fixed effects swept out (alternating projections)."""
    x = matrix - matrix.mean(axis=0)
    counts = [np.maximum(np.bincount(g), 1) for g in groups]
    for _ in range(max_sweeps):
        worst = 0.0
        for g, count in zip(groups, counts):
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


def estimator(sample: pd.DataFrame, method: str):
    """A function of row indices returning the watering coefficient."""
    y, t = sample["y"].to_numpy(float), sample["t"].to_numpy(bool)
    if method == "exact":
        stratum = sample.groupby(crown.EXACT_STRATA).ngroup().to_numpy()
        return lambda rows: exact_att(y[rows], t[rows], stratum[rows])
    X = np.column_stack([t.astype(float)] + ([sample["x"].to_numpy(float)] if "x" in sample else []))
    groups = keys(sample)
    return lambda rows: float(fe_fit(y[rows], X[rows], [g[rows] for g in groups])[0][0])


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
        return "Watered crowns became greener, by less than Δ" if upper90 < delta else "Watered crowns became greener; whether by Δ or more stays open"
    if ci95[1] < 0:
        return "Watered crowns lost greenness; residents may water trees that look stressed"
    if upper90 < delta:
        return "No gain detected; a gain of Δ or more is ruled out"
    return "Inconclusive; report the largest gain the interval does not exclude"


def same_direction(ci95: list[float], primary: float) -> bool:
    """True when an interval excludes zero on the side of the primary estimate."""
    return (primary > 0 and ci95[0] > 0) or (primary < 0 and ci95[1] < 0)


# ---------------------------------------------------------------- design

def smallest_effect(trees: pd.DataFrame, primary: pd.DataFrame) -> dict:
    """Half the one-year gain in 2020 circle NDVI with age (ages 3-15, pooled over watering)."""
    base = trees[trees["age_2020"].between(*DELTA_AGES) & trees["full_2m_2020"] & trees["ndvi_2m_2020"].notna()]
    age, ndvi = base["age_2020"].to_numpy(float), base["ndvi_2m_2020"].to_numpy(float)
    slope = float(np.polyfit(age, ndvi, 1)[0]) if len(base) > 2 and age.std() > 0 else float("nan")
    pooled_sd = float(primary["y"].std(ddof=1))
    if slope > 0:
        return {"delta": slope / 2, "rule": "half the one-year gain with age", "age_slope": slope, "trees_for_slope": int(len(base)), "pooled_sd_of_change": pooled_sd}
    return {"delta": FALLBACK_SD * pooled_sd, "rule": "0.2 SD of the pooled change (age slope not positive)", "age_slope": slope,
            "trees_for_slope": int(len(base)), "pooled_sd_of_change": pooled_sd}


def design(data: Path = DATA, out: Path = OUT) -> dict:
    extract.require_freeze()
    checked = json.loads((out / "check.json").read_text()) if (out / "check.json").exists() else {}
    if not checked.get("passes"):
        raise SystemExit("The check stage has not passed; the design stage does not run.")
    trees = tree_table(data)
    samples = {name: build(trees, spec) for name, spec in SPECS.items()}
    primary = samples["primary"]
    effect = smallest_effect(trees, primary)
    residual_sd = float(np.sqrt((demean(primary[["y"]].to_numpy(float), keys(primary)) ** 2).sum() / (len(primary) - 1)))
    analyses = {}
    for name, sample in samples.items():
        if sample is None:
            analyses[name] = {"available": False}
            continue
        entry = {"available": True, "treated": int(sample["t"].sum()), "controls": int((~sample["t"]).sum())}
        if not (entry["treated"] and entry["controls"]):
            entry["available"] = False
        elif SPECS[name].get("method", "fe") == "fe":
            entry["mde_residual_sd_design_effect_1_and_2"] = crown.standardised_mde(sample.assign(watered=sample["t"]), "watered")
        analyses[name] = entry
    mde_sd = analyses["primary"]["mde_residual_sd_design_effect_1_and_2"]
    se = [m * residual_sd / Z_80 for m in mde_sd]
    result = {
        "stage": "design",
        "smallest_effect": effect,
        "primary_residual_sd_of_change": residual_sd,
        "primary_mde_ndvi_design_effect_1_and_2": [round(m * residual_sd, 5) for m in mde_sd],
        "power_pct_test_a_if_gain_equals_delta": [round(100 * four_year.power(s, effect["delta"], Z95), 1) for s in se],
        "power_pct_test_b_if_no_difference": [round(100 * four_year.power(s, effect["delta"], Z90), 1) for s in se],
        "analyses": analyses,
        "inputs_sha256": {f.name: file_hash(f) for f in sorted(data.glob("crown_circles_*.csv.gz"))},
        **stamp(),
    }
    (out / "design.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


# ---------------------------------------------------------------- outcome

def estimate(sample: pd.DataFrame, method: str, reps: int) -> dict:
    fit = estimator(sample, method)
    rows = np.arange(len(sample))
    point = fit(rows)
    draws = bootstrap(sample, fit, reps)
    out = {
        "treated": int(sample["t"].sum()), "controls": int((~sample["t"]).sum()), "planning_areas": int(sample["plr_id"].nunique()),
        "difference": point,
        "ci95_bootstrap": [float(q) for q in np.quantile(draws, [0.025, 0.975])],
        "ci90_bootstrap": [float(q) for q in np.quantile(draws, [0.05, 0.95])],
    }
    if method == "fe":
        X = np.column_stack([sample["t"].to_numpy(float)] + ([sample["x"].to_numpy(float)] if "x" in sample else []))
        _, residual, rx = fe_fit(sample["y"].to_numpy(float), X, keys(sample))
        se = cluster_se(rx, residual, sample["plr_id"].to_numpy())
        out["ci95_cluster_robust"] = [point - Z95 * se, point + Z95 * se]
    return out


def outcome(data: Path = DATA, out: Path = OUT, reps: int = REPS) -> dict:
    extract.require_freeze()
    planned = json.loads((out / "design.json").read_text())
    if planned["protocol_sha256"] != stamp()["protocol_sha256"]:
        raise SystemExit("The plan changed after the design stage; the outcome stage does not run.")
    trees = tree_table(data)
    samples = {name: build(trees, spec) for name, spec in SPECS.items()}
    for name, sample in samples.items():
        expected = planned["analyses"][name]
        found = {"available": False} if sample is None else {"treated": int(sample["t"].sum()), "controls": int((~sample["t"]).sum())}
        if any(expected.get(k) != v for k, v in found.items()):
            raise SystemExit(f"{name}: the sample differs from the design stage ({found} against {expected}).")
    if not planned["analyses"]["primary"]["available"]:
        raise SystemExit("The primary sample has no watered or no control trees.")
    delta = planned["smallest_effect"]["delta"]
    results = {name: (estimate(sample, SPECS[name].get("method", "fe"), reps) if planned["analyses"][name]["available"]
                      else planned["analyses"][name]) for name, sample in samples.items()}
    primary = results["primary"]
    primary["test_a_gain"] = primary["ci95_bootstrap"][0] > 0
    primary["test_b_gain_of_delta_ruled_out"] = primary["ci90_bootstrap"][1] < delta
    primary["report"] = interpret(primary["ci95_bootstrap"], primary["ci90_bootstrap"][1], delta)
    primary["largest_gain_not_excluded"] = primary["ci95_bootstrap"][1]
    flags = {name: same_direction(results[name]["ci95_bootstrap"], primary["difference"])
             for name in ("placebo_2015_2020", "older_16_40") if "difference" in results[name]}
    result = {
        "stage": "outcome", "delta": delta, "bootstrap": {"reps": reps, "seed": SEED, "cluster": "planning area"},
        "primary": primary,
        "selection_checks": {"same_direction_as_primary": flags, "primary_reported_as_likely_selection": any(flags.values())},
        "secondary": {name: r for name, r in results.items() if name != "primary"},
        "s8_without_survivor_selection": "awaits CityLAB's 2020 tree table and full log history",
        "inputs_sha256": planned["inputs_sha256"],
        **stamp(),
    }
    (out / "outcome.json").write_text(json.dumps(result, indent=2, default=float) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["check", "design", "outcome"])
    parser.add_argument("--data", type=Path, default=DATA)
    args = parser.parse_args()
    result = {"check": check, "design": design, "outcome": outcome}[args.stage](args.data)
    summary = {k: result[k] for k in ("passes", "checks", "smallest_effect", "primary_mde_ndvi_design_effect_1_and_2", "primary") if k in result}
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
