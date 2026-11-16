"""Order-of-magnitude benchmarks for the November 2026 policy-relevance memo.

Answers descriptive policy questions: how many catalogued trees the logs reach,
how much logged water a watered tree receives, how that compares with rainfall,
climatic demand, municipal watering and public supply, which effect sizes a
greenness analysis could detect, and how much precision the revised designs
(young-tree survival, municipal-care age limits) can offer.

Claim limit: logged platform activity only (not all watering); the current
inventory is not a historical stock; external municipal figures come from
district statements in parliamentary answers and serve as illustrations; the
evapotranspiration estimates are simple temperature/radiation approximations.
The design-feasibility section counts trees and treated units only. It never
tabulates watering by age near the municipal-care limits, so that comparison
can still be registered before it is examined. The identifier comparison
between the 2025 and 2026 inventories reports removals for all trees and never
by watering status, so the survival comparison also stays unexamined.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import pyogrio
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
SEASON_MONTHS = (4, 9)
AGE_BANDS = [-1, 3, 10, 20, 40, 500]
AGE_LABELS = ["0-3", "4-10", "11-20", "21-40", "41+"]
Z_80 = 1.959964 + 0.841621  # two-sided alpha 0.05, power 0.80
STATION_LATITUDE = 52.4675  # DWD 00433 Berlin-Tempelhof

# External benchmarks (see docs/policy_feedback_2026_11.md for sources).
GUIDANCE_L_PER_WEEK = (70, 100)  # Senate and district guidance for young trees
SEASON_WEEKS = (20, 26)
BWB_WATER_SOLD_M3 = 215e6  # Berliner Wasserbetriebe, water sold in 2021
CONTRACTOR_EUR_PER_LITRE = (0.05, 0.15)  # EUR 7-12 per watering of roughly 80-150 L
MUNICIPAL_PROGRAMMES = {  # tree-waterings per season x litres per watering
    "Lichtenberg: ~4,000 young trees, 10-12 rounds, 80-100 L": ((4000 * 10, 80), (4000 * 12, 100)),
    "Tempelhof-Schöneberg 2023: 1,500 trees x 10-12 + 2,600 x 6-8 rounds, 100-150 L": ((1500 * 10 + 2600 * 6, 100), (1500 * 12 + 2600 * 8, 150)),
    "Reinickendorf 2021: 25,764 watering passes, 100-150 L": ((25764, 100), (25764, 150)),
}
MUNICIPAL_COST_PER_WATERING_EUR = {
    "Lichtenberg (EUR 101,000 / 1,093 trees x 13 rounds)": round(101000 / (1093 * 13), 2),
    "Reinickendorf 2021 (EUR 240,120 / 25,764 passes)": round(240120.48 / 25764, 2),
    "Tempelhof-Schöneberg (stated)": "9-12",
}
# Years after planting up to which districts water young trees (Drucksache 19/16001, 2023);
# Steglitz-Zehlendorf extends care to 15 years on poor sites only. Other districts: not stated.
MUNICIPAL_CARE_LIMIT_YEARS = {
    "Pankow": 10, "Neukölln": 10, "Treptow-Köpenick": 10, "Lichtenberg": 10, "Reinickendorf": 10,
    "Friedrichshain-Kreuzberg": 12, "Tempelhof-Schöneberg": 12, "Steglitz-Zehlendorf": 15,
}
ANNUAL_STREET_TREE_MORTALITY = (0.035, 0.051)  # meta-analysis range, Roman and Scatena (2011)
INVENTORY_2025 = ROOT / "data/raw/tree_inventory/trees_2025_gbif.csv.gz"
SAME_SPOT_M = 1.0  # a 2026 tree with a new identifier this close to a vanished one occupies its site


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def pct(numerator: float, denominator: float, digits: int = 2) -> float:
    return round(100 * numerator / denominator, digits)


def load_inventory(path: Path) -> pd.DataFrame:
    expected = json.loads((ROOT / "data/raw/tree_inventory/snapshot.json").read_text())["uncompressed_sha256"]
    if sha256(path) != expected:
        raise ValueError(f"{path} is not the frozen inventory snapshot")
    columns = ["pitid", "source_layer", "pflanzjahr", "kronedurch", "bezirk"]  # bezirk feeds district reach
    inv = pyogrio.read_dataframe(path, layer="Berlin_trees", read_geometry=False, columns=columns)
    inv["layer"] = inv["source_layer"].str.replace("baumbestand:", "", regex=False)
    inv["pflanzjahr"] = pd.to_numeric(inv["pflanzjahr"], errors="coerce")
    inv.loc[(inv["pflanzjahr"] < 1700) | (inv["pflanzjahr"] > 2026), "pflanzjahr"] = np.nan
    # Prefer the street-tree row when an identifier occurs in both layers.
    return inv.dropna(subset=["pitid"]).sort_values("layer", ascending=False).drop_duplicates("pitid")


def season_weather() -> pd.DataFrame:
    """April-September rain and two reference-evapotranspiration approximations."""
    with zipfile.ZipFile(ROOT / "data/raw/dwd/tageswerte_KL_00433_19480101_20251231_hist.zip") as archive:
        name = next(n for n in archive.namelist() if n.startswith("produkt_klima_tag"))
        kl = pd.read_csv(io.BytesIO(archive.read(name)), sep=";", skipinitialspace=True)
    kl.columns = [c.strip() for c in kl.columns]
    kl["date"] = pd.to_datetime(kl["MESS_DATUM"].astype(str), format="%Y%m%d")
    for column in ["RSK", "TMK", "TXK", "TNK", "SDK"]:
        kl[column] = kl[column].where(kl[column] > -999)
    kl = kl[kl["date"].dt.year.between(1991, 2025) & kl["date"].dt.month.between(*SEASON_MONTHS)].copy()
    lat = math.radians(STATION_LATITUDE)
    doy = kl["date"].dt.dayofyear
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    dec = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(-np.tan(lat) * np.tan(dec))
    ra = 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.sin(ws))
    kl["et0_hargreaves"] = 0.0023 * (kl["TMK"] + 17.8) * np.sqrt((kl["TXK"] - kl["TNK"]).clip(lower=0)) * ra * 0.408
    daylight = 24 / np.pi * ws
    rg = ra * 100 * (0.19 + 0.55 * (kl["SDK"] / daylight).clip(upper=1))  # J cm-2 d-1
    kl["et0_turc_wendling"] = (rg + 93) * (kl["TMK"] + 22) / (150 * (kl["TMK"] + 123))
    weather = kl.groupby(kl["date"].dt.year).agg(
        rain_mm=("RSK", lambda s: s.sum(min_count=150)),
        rain_missing_days=("RSK", lambda s: int(s.isna().sum())),
        et0_hargreaves_mm=("et0_hargreaves", lambda s: s.sum(min_count=150)),
        et0_turc_wendling_mm=("et0_turc_wendling", lambda s: s.sum(min_count=150)),
        sunshine_missing_days=("SDK", lambda s: int(s.isna().sum())),
    )
    weather["deficit_hargreaves_mm"] = weather["et0_hargreaves_mm"] - weather["rain_mm"]
    weather["deficit_turc_wendling_mm"] = weather["et0_turc_wendling_mm"] - weather["rain_mm"]
    return weather


def design_feasibility(street: pd.DataFrame, ts: pd.DataFrame, per_season: dict) -> dict:
    """Sample sizes and minimum detectable effects for the revised designs.

    Counts trees and treated units only; watering by age near the municipal-care
    limits is not tabulated.
    """
    limit = street["bezirk"].map(MUNICIPAL_CARE_LIMIT_YEARS)
    seasons = pd.concat([pd.DataFrame({"limit": limit, "age": year - street["pflanzjahr"]}) for year in range(2020, 2026)])
    cells = {f"limit_{lim}_ages_{lo}_{hi}": int(((seasons["limit"] == lim) & seasons["age"].between(lo, hi)).sum())
             for lim in (10, 12) for lo, hi in ((9, 10), (11, 12))}
    inverse_n = math.sqrt(sum(1 / n for n in cells.values()))
    shares = [v["pct_of_street_age_le15"] / 100 for v in per_season.values()]
    share_points = {"min": min(shares), "median": float(np.median(shares)), "max": max(shares)}

    crown = street[street["kronedurch"] > 0]
    pixel_share = math.pi * (crown["kronedurch"] / 2) ** 2 / 100
    bands = pd.cut(2025 - crown["pflanzjahr"], [2, 5, 8, 10, 12, 15, 20, 30])
    by_band = pixel_share.groupby(bands, observed=True).median()

    young = ts[(ts["layer"] == "strassenbaeume") & (ts["age"] <= 15)]
    treated = {"any_log": int(young["tree_id"].nunique()),
               "ge_500_l_in_a_season": int(young.loc[young["litres"] >= 500, "tree_id"].nunique())}

    def survival_mde_pp(n: int, annual: float, design_effect: float) -> float:
        p0 = 1 - (1 - annual) ** 4
        return round(100 * Z_80 * math.sqrt(design_effect * p0 * (1 - p0) * (1 / n + 1 / (5 * n))), 1)

    return {
        "street_trees_by_municipal_care_limit": limit.map(lambda v: f"{int(v)} years", na_action="ignore").fillna("not stated").value_counts().to_dict(),
        "difference_in_discontinuities_at_10_years": {
            "tree_season_cells": cells,
            "seasonal_watered_share_age_le15_pct": {k: round(100 * v, 2) for k, v in share_points.items()},
            "mde_pp": {f"share_{k},design_effect_{d}": round(100 * Z_80 * math.sqrt(d * p * (1 - p)) * inverse_n, 2)
                       for k, p in share_points.items() for d in (1, 2)},
        },
        "median_crown_share_of_10m_pixel_by_age_2025": {f"{int(iv.left) + 1}-{int(iv.right)}": round(float(v), 2) for iv, v in by_band.items()},
        "young_street_trees_with_logged_watering": treated,
        "survival_mde_4yr_mortality_pp": {f"{k},annual_{a}": [survival_mde_pp(n, a, 1), survival_mde_pp(n, a, 2)]
                                          for k, n in treated.items() for a in ANNUAL_STREET_TREE_MORTALITY},
        "assumptions": ("Discontinuity cells are street tree-seasons 2020-2025 from the current inventory (trees removed earlier "
                        "are missing), ages 9-10 against 11-12 in districts with 10- and 12-year limits; watered shares are the "
                        "seasonal ranges for all street trees aged <=15. Survival: four-year cumulative mortality implied by "
                        "the annual range, five matched controls per young tree with an April-September log, design effect 1 "
                        "or 2 (pairs of values)."),
    }


def treated_needed(p0: float, relative_reduction: float, controls: int = 5) -> int:
    """Treated trees needed to detect a relative fall in removal risk (two-sided 5%, power 80%)."""
    p1 = p0 * (1 - relative_reduction)
    pooled = (p1 + controls * p0) / (1 + controls)
    spread = 1.959964 * math.sqrt(pooled * (1 - pooled) * (1 + 1 / controls)) + 0.841621 * math.sqrt(p1 * (1 - p1) + p0 * (1 - p0) / controls)
    return math.ceil(spread ** 2 / (p0 - p1) ** 2)


def compare_identifiers(before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    """Flag each earlier tree whose identifier is absent later, and what now stands on its site.

    Both frames need tree_id, genus, planting_year, x and y. `gone` trees are `rekeyed`
    when a later tree with a new identifier has the same site, genus and planting year,
    and `replanted` when a later tree planted in the last two years stands on the site.
    """
    out = before.copy()
    out["gone"] = ~out["tree_id"].isin(after["tree_id"])
    added = after[~after["tree_id"].isin(before["tree_id"]) & after["x"].notna()]
    out["rekeyed"] = out["replanted"] = False
    if out["gone"].any() and len(added):
        gone = out[out["gone"]]
        distance, index = cKDTree(added[["x", "y"]].to_numpy()).query(gone[["x", "y"]].to_numpy())
        nearest = added.iloc[index]
        same_site = distance <= SAME_SPOT_M
        same_tree = (gone["genus"].str.upper().to_numpy() == nearest["genus"].str.upper().to_numpy()) & (gone["planting_year"].to_numpy() == nearest["planting_year"].to_numpy())
        recent = nearest["planting_year"].to_numpy() >= after["planting_year"].max() - 2
        out.loc[gone.index, "rekeyed"] = same_site & same_tree
        out.loc[gone.index, "replanted"] = same_site & ~same_tree & recent
    return out


def inventory_id_stability(inventory_path: Path, ts: pd.DataFrame, treated_all_seasons: int) -> dict:
    """Whether a tree identifier missing from the 2026 inventory can stand for a removed tree.

    Compares the 2025 inventory with the 2026 one for all trees. Watering enters only as
    the count of treated trees in the 2025 season; removals are never split by watering.
    """
    before = pd.read_csv(INVENTORY_2025, dtype={"tree_id": str}).rename(columns={"x_25833": "x", "y_25833": "y"})
    after = pyogrio.read_dataframe(inventory_path, layer="Berlin_trees", columns=["id", "gattung", "pflanzjahr"])
    after = pd.DataFrame({"tree_id": after["id"], "genus": after["gattung"], "planting_year": pd.to_numeric(after["pflanzjahr"], errors="coerce"),
                          "x": after.geometry.x, "y": after.geometry.y})
    for frame in (before, after):
        frame.loc[(frame["planting_year"] < 1700) | (frame["planting_year"] > 2026), "planting_year"] = np.nan
        frame["street"] = frame["tree_id"].str.startswith("strassenbaeume.")
    trees = compare_identifiers(before, after)
    matched = trees[~trees["gone"]].merge(after, on="tree_id", suffixes=("", "_2026"))
    both_years = matched["planting_year"].notna() & matched["planting_year_2026"].notna()
    street = trees[trees["street"]].copy()
    street["removed"] = street["gone"] & ~street["rekeyed"]
    age = 2025 - street["planting_year"]
    street["band"] = pd.cut(age, [-np.inf, 15, 40, np.inf], labels=["le15", "16-40", "41+"]).astype(object).where(age.notna(), "unknown")
    young = street[street["band"] == "le15"]
    by_district = young.groupby("district")["removed"].agg(["size", "mean"])
    by_district = (by_district.loc[by_district["size"] >= 1000, "mean"] * 100).round(2).sort_values()
    street_after = after[after["street"]]
    risk = float(young["removed"].mean())
    treated = int(ts.loc[(ts["layer"] == "strassenbaeume") & (ts["age"] <= 15) & (ts["year"] == 2025), "tree_id"].nunique())
    four_year_risk = 1 - (1 - risk) ** 4
    return {
        "trees_2025": int(len(trees)),
        "ids_present_in_2026_pct": pct((~trees["gone"]).sum(), len(trees)),
        "ids_gone": {"all": int(trees["gone"].sum()), "street": int(street["gone"].sum()), "green_space": int((trees["gone"] & ~trees["street"]).sum())},
        "matched_trees_changed_pct": {
            "planting_year": pct((matched.loc[both_years, "planting_year"] != matched.loc[both_years, "planting_year_2026"]).sum(), both_years.sum()),
            "genus": pct((matched["genus"].str.upper() != matched["genus_2026"].str.upper()).sum(), len(matched)),
            "moved_over_1_m": pct((np.hypot(matched["x"] - matched["x_2026"], matched["y"] - matched["y_2026"]) > 1).sum(), len(matched)),
        },
        "street": {
            "trees_2025": int(len(street)), "ids_gone_pct": pct(street["gone"].sum(), len(street)),
            "rekeyed": int(street["rekeyed"].sum()), "replanted_on_site": int(street["replanted"].sum()),
            "removed_pct": pct(street["removed"].sum(), len(street)),
            "removed_pct_by_age_2025": {band: pct(group["removed"].sum(), len(group)) for band, group in street.groupby("band")},
            "trees_by_age_2025": street["band"].value_counts().sort_index().to_dict(),
        },
        "young_street_age_le15": {
            "trees_2025": int(len(young)), "removed": int(young["removed"].sum()), "removed_pct": pct(young["removed"].sum(), len(young)),
            "replanted_on_site": int(young["replanted"].sum()),
            "removed_pct_by_district_1000plus_trees": by_district.to_dict(),
        },
        "archive_vintage_and_coverage": {
            "street_trees_planted_2025": {"archive_2025": int((street["planting_year"] == 2025).sum()), "inventory_2026": int((street_after["planting_year"] == 2025).sum())},
            "street_trees_2026_planted_le2022_with_ids_absent_from_archive": int((~street_after["tree_id"].isin(before["tree_id"]) & (street_after["planting_year"] <= 2022)).sum()),
        },
        "one_year_survival_2025_season": {
            "young_street_trees_with_logged_watering": treated,
            "expected_removals_at_overall_rate": round(treated * risk, 1),
            "mde_pp_design_effect_1_and_2": [round(100 * Z_80 * math.sqrt(d * risk * (1 - risk) * (1 / treated + 1 / (5 * treated))), 2) for d in (1, 2)],
            "treated_trees_needed_to_detect_halving": treated_needed(risk, 0.5),
        },
        "four_year_design_if_this_rate_persists": {
            "young_street_trees_with_logged_watering": treated_all_seasons,
            "baseline_removed_pct": round(100 * four_year_risk, 1),
            "mde_pp_design_effect_1_and_2": [round(100 * Z_80 * math.sqrt(d * four_year_risk * (1 - four_year_risk) * (1 / treated_all_seasons + 1 / (5 * treated_all_seasons))), 1) for d in (1, 2)],
        },
        "assumptions": ("2025 inventory: third-party archive of the official cadastre (data/raw/tree_inventory/snapshot_2025.json), which predates "
                        "the 2025 season and omits some trees. Removed: identifier absent from the 2026 inventory and not re-keyed. Re-keyed: a "
                        "2026 tree with a new identifier within 1 m, same genus and planting year. Replanted: such a tree planted 2024 or later. "
                        "Ages are 2025 minus planting year. A removal is not a death: felling reasons are unknown and removal can lag death. "
                        "Detectability uses five matched controls per watered tree, as in the four-year design."),
    }


def build(inventory_path: Path) -> dict:
    inv = load_inventory(inventory_path)
    street = inv[inv["layer"] == "strassenbaeume"]
    out: dict = {"inventory": {
        "catalogued_unique_ids": int(len(inv)),
        "street_trees": int(len(street)),
        "green_space_trees": int((inv["layer"] == "anlagenbaeume").sum()),
        "street_planting_year_coverage": round(float(street["pflanzjahr"].notna().mean()), 3),
        "street_crown_diameter_coverage": round(float((street["kronedurch"] > 0).mean()), 3),
        "green_space_crown_diameter_coverage": round(float((inv.loc[inv["layer"] == "anlagenbaeume", "kronedurch"] > 0).mean()), 3),
        "street_age_le10_2025": int(((2025 - street["pflanzjahr"]) <= 10).sum()),
        "street_age_le15_2025": int(((2025 - street["pflanzjahr"]) <= 15).sum()),
    }}
    crown = inv[inv["kronedurch"] > 0].assign(area=lambda d: math.pi * (d["kronedurch"] / 2) ** 2, age=lambda d: 2025 - d["pflanzjahr"])
    street_crown = crown[crown["layer"] == "strassenbaeume"]
    out["inventory"]["recorded_crown_area_km2"] = {
        "street": round(float(street_crown["area"].sum() / 1e6), 2),
        "street_age_le15": round(float(street_crown.loc[street_crown["age"] <= 15, "area"].sum() / 1e6), 2),
        "green_space": round(float(crown.loc[crown["layer"] == "anlagenbaeume", "area"].sum() / 1e6), 2),
    }

    tree_day = pd.read_csv(ROOT / "data/processed/temporal/recorded_tree_day_watering_2020_2025.csv", dtype={"tree_id": str, "plr_id": str})
    tree_day = tree_day.merge(inv[["pitid", "layer", "kronedurch"]].rename(columns={"pitid": "tree_id"}), on="tree_id", how="left")
    watered = tree_day.drop_duplicates("tree_id")
    out["reach_2020_2025"] = {
        "distinct_watered_trees": int(len(watered)),
        "pct_of_catalogued": pct(len(watered), len(inv)),
        "street_watered": int((watered["layer"] == "strassenbaeume").sum()),
        "pct_of_street": pct((watered["layer"] == "strassenbaeume").sum(), len(street)),
        "green_space_watered": int((watered["layer"] == "anlagenbaeume").sum()),
        "pct_of_green_space": pct((watered["layer"] == "anlagenbaeume").sum(), (inv["layer"] == "anlagenbaeume").sum(), 3),
    }
    by_tree = tree_day.groupby("tree_id")["recorded_litres"].sum().sort_values(ascending=False)
    out["reach_2020_2025"]["litres_share_top10pct_trees"] = round(float(by_tree.iloc[: len(by_tree) // 10].sum() / by_tree.sum()), 3)
    street_watered = watered[watered["layer"] == "strassenbaeume"].merge(street[["pitid", "bezirk"]].rename(columns={"pitid": "tree_id"}), on="tree_id", how="left")
    out["reach_2020_2025"]["pct_of_street_by_district"] = (street_watered["bezirk"].value_counts() / street["bezirk"].value_counts() * 100).round(2).sort_values(ascending=False).to_dict()

    season = tree_day[tree_day["calendar_month"].between(*SEASON_MONTHS)]
    ts = season.groupby(["tree_id", "year"]).agg(
        litres=("recorded_litres", "sum"), days=("local_date", "nunique"), age=("age_at_watering", "first"),
        layer=("layer", "first"), plr_id=("plr_id", "first"), crown_d=("kronedurch", "first")).reset_index()
    ts["band"] = pd.cut(ts["age"], AGE_BANDS, labels=AGE_LABELS)
    seasons_per_tree = ts.groupby("tree_id")["year"].nunique()
    out["reach_2020_2025"]["share_of_season_watered_trees_in_one_season_only"] = round(float((seasons_per_tree == 1).mean()), 3)

    per_season = {}
    for year, group in ts.groupby("year"):
        age = int(year) - street["pflanzjahr"]
        stock = pd.cut(age, AGE_BANDS, labels=AGE_LABELS).value_counts()
        reached = group[group["layer"] == "strassenbaeume"]["band"].value_counts()
        per_season[int(year)] = {
            "watered_trees": int(len(group)),
            "litres": float(group["litres"].sum()),
            "pct_of_catalogued": pct(len(group), len(inv), 3),
            "pct_of_street": pct((group["layer"] == "strassenbaeume").sum(), len(street), 3),
            "pct_of_street_age_le15": pct(((group["layer"] == "strassenbaeume") & (group["age"] <= 15)).sum(), (age <= 15).sum()),
            "pct_of_street_by_age_band": {band: pct(reached.get(band, 0), stock[band]) for band in AGE_LABELS},
        }
    out["per_season_apr_sep"] = per_season

    litres = ts["litres"]
    out["dose_per_watered_tree_season"] = {
        "tree_seasons": int(len(ts)),
        "median_l": float(litres.median()), "mean_l": round(float(litres.mean()), 1), "p90_l": float(litres.quantile(0.9)),
        "share_ge_100_l": round(float((litres >= 100).mean()), 3), "share_ge_250_l": round(float((litres >= 250).mean()), 3),
        "share_ge_500_l": round(float((litres >= 500).mean()), 3), "share_ge_1000_l": round(float((litres >= 1000).mean()), 3),
        "share_with_one_logged_day": round(float((ts["days"] == 1).mean()), 3),
        "median_l_age_le15": float(ts.loc[ts["age"] <= 15, "litres"].median()),
        "share_ge_500_l_age_le15": round(float((ts.loc[ts["age"] <= 15, "litres"] >= 500).mean()), 3),
        "tree_season_share_by_age_band": ts["band"].value_counts(normalize=True).reindex(AGE_LABELS).round(3).to_dict(),
        "litres_share_by_age_band": (ts.groupby("band", observed=True)["litres"].sum() / litres.sum()).reindex(AGE_LABELS).round(3).to_dict(),
        "median_l_by_age_band": ts.groupby("band", observed=True)["litres"].median().reindex(AGE_LABELS).to_dict(),
    }

    weather = season_weather()
    out["weather_apr_sep"] = {
        "by_year": weather.loc[2020:2025].round(0).astype(object).where(weather.loc[2020:2025].notna(), None).to_dict(orient="index"),
        "mean_1991_2020": weather.loc[1991:2020, ["rain_mm", "et0_hargreaves_mm", "et0_turc_wendling_mm"]].mean().round(0).to_dict(),
        "note": "Turc-Wendling needs sunshine duration, missing at the station from 2023; Hargreaves overstates humid-climate ET0 and is an upper bound.",
    }
    with_crown = ts[ts["crown_d"] > 0].copy()
    with_crown["crown_m2"] = math.pi * (with_crown["crown_d"] / 2) ** 2
    rain = with_crown["year"].map(weather["rain_mm"]) * with_crown["crown_m2"]
    deficit = with_crown["year"].map(weather["deficit_hargreaves_mm"]).clip(lower=0) * with_crown["crown_m2"]
    young = with_crown["age"] <= 15
    out["logged_vs_rain_and_demand"] = {
        "tree_seasons_with_crown_diameter": int(len(with_crown)),
        "median_crown_m2": round(float(with_crown["crown_m2"].median()), 1),
        "median_crown_m2_age_le15": round(float(with_crown.loc[young, "crown_m2"].median()), 1),
        "median_pct_of_rain_on_own_crown": round(float((with_crown["litres"] / rain).median() * 100), 1),
        "median_pct_of_hargreaves_deficit_on_own_crown": round(float((with_crown["litres"] / deficit).median() * 100), 1),
        "median_pct_of_hargreaves_deficit_on_own_crown_age_le15": round(float((with_crown.loc[young, "litres"] / deficit[young]).median() * 100), 1),
        "rain_on_6m2_tree_pit_l_by_year": (weather.loc[2020:2025, "rain_mm"] * 6).round(0).astype(int).to_dict(),
    }

    need = [GUIDANCE_L_PER_WEEK[0] * SEASON_WEEKS[0], GUIDANCE_L_PER_WEEK[1] * SEASON_WEEKS[1]]
    young_stock = out["inventory"]["street_age_le15_2025"]
    season_litres = ts.groupby("year")["litres"].sum()
    out["water_budget"] = {
        "guidance_season_need_per_young_tree_l": need,
        "street_age_le15_season_need_million_l": [round(young_stock * n / 1e6, 1) for n in need],
        "logged_season_million_l": (season_litres / 1e6).round(3).to_dict(),
        "municipal_programme_million_l_per_season": {k: [round(a * b / 1e6, 2), round(c * d / 1e6, 2)] for k, ((a, b), (c, d)) in MUNICIPAL_PROGRAMMES.items()},
        "municipal_cost_per_tree_watering_eur": MUNICIPAL_COST_PER_WATERING_EUR,
        "logged_contractor_value_keur": {int(y): [round(v * CONTRACTOR_EUR_PER_LITRE[0] / 1e3), round(v * CONTRACTOR_EUR_PER_LITRE[1] / 1e3)] for y, v in season_litres.items()},
        "logged_pct_of_bwb_2021_water_sold": {int(y): round(v / (BWB_WATER_SOLD_M3 * 1000) * 100, 5) for y, v in season_litres.items()},
    }

    coefficients = pd.read_csv(ROOT / "output/rq1_daily/tables/model_coefficients.csv")
    beta = float(coefficients.query("sample == 'linked_baseline' and specification == 'baseline' and outcome == 'litres' and term == 'tmax_per_5c' and hac_lag_days == 14")["coefficient_log1p"].iloc[0])
    mean_day = season_litres.sum() / 1051
    out["heat_response_in_litres"] = {
        "pilot_log1p_litres_per_5c": round(beta, 3),
        "mean_logged_l_per_season_day": round(mean_day),
        "approx_extra_l_on_5c_warmer_day": round(mean_day * (math.exp(beta) - 1)),
        "street_age_le15_need_l_per_day": [round(young_stock * w / 7) for w in GUIDANCE_L_PER_WEEK],
    }

    lor = pd.read_csv(ROOT / "output/spatial/tables/lor_watering_metrics_2020_2025.csv", dtype={"plr_id": str})
    street_seasons = ts[ts["layer"] == "strassenbaeume"].groupby(["plr_id", "year"]).size().rename("watered").reset_index()
    grid = pd.MultiIndex.from_product([lor["plr_id"], sorted(ts["year"].unique())], names=["plr_id", "year"]).to_frame(index=False)
    grid = grid.merge(street_seasons, how="left").fillna({"watered": 0}).merge(lor[["plr_id", "street_inventory_trees"]], how="left")
    grid = grid[grid["street_inventory_trees"] >= 50]
    share = grid["watered"] / grid["street_inventory_trees"]
    sigma_area = (0.01, 0.02, 0.03)
    out["detectability"] = {
        "lor_seasons_with_50plus_street_trees": int(len(grid)),
        "lor_season_watered_street_share_pct": {"median": round(float(share.median() * 100), 2), "p90": round(float(share.quantile(0.9) * 100), 2), "max": round(float(share.max() * 100), 2), "share_of_lor_seasons_with_none": round(float((share == 0).mean()), 2)},
        "lor_mde_per_watered_tree_pixel_ndvi_one_season": {str(s): round(Z_80 * s / (float(share.std()) * math.sqrt(542)), 3) for s in sigma_area},
        "tree_mde_pixel_ndvi": {f"n_watered={n},sd={s},design_effect={d}": round(Z_80 * s * math.sqrt(d * (1 / n + 1 / (5 * n))), 4) for n in (1000, 4000) for s in (0.03, 0.08) for d in (1, 3)},
        "young_crown_fraction_of_10m_pixel": {q: round(float((with_crown.loc[young, "crown_m2"] / 100).clip(upper=1).quantile(p)), 3) for q, p in (("p25", 0.25), ("median", 0.5), ("p75", 0.75))},
        "assumptions": "Area model: one season, 542 areas, outcome is the mean NDVI change of street-tree pixels; tree model: five matched controls per watered tree. The standard deviations are placeholders to be replaced by pre-2020 Sentinel-2 estimates.",
    }
    out["design_feasibility"] = design_feasibility(street, ts, per_season)
    out["design_feasibility"]["inventory_ids_2025_to_2026"] = inventory_id_stability(
        inventory_path, ts, out["design_feasibility"]["young_street_trees_with_logged_watering"]["any_log"])

    equity = pd.read_csv(ROOT / "output/equity/tables/lor_watering_equity_metrics.csv", dtype={"plr_id": str})
    geometry = pyogrio.read_dataframe(ROOT / "data/spatial/lor_planungsraeume_2021.gpkg")
    geometry["area_km2"] = geometry.to_crs(25833).area / 1e6
    areas = lor.merge(equity[["plr_id", "mss_population", "social_status_score"]], on="plr_id").merge(geometry[["plr_id", "area_km2"]], on="plr_id")
    areas = areas[(areas["street_inventory_trees"] >= 50) & (areas["mss_population"] >= 300)].copy()
    areas["density"] = areas["mss_population"] / areas["area_km2"]
    areas["watered_per_100_street"] = 100 * areas["watered_trees"] / areas["street_inventory_trees"]
    areas["residents_per_street_tree"] = areas["mss_population"] / areas["street_inventory_trees"]
    quintile = pd.qcut(areas["density"], 5, labels=[f"Q{i}" for i in range(1, 6)])
    out["population_density"] = {
        "areas": int(len(areas)),
        "spearman_with_watered_per_100_street": {c: round(float(spearmanr(areas[c], areas["watered_per_100_street"])[0]), 2) for c in ("density", "residents_per_street_tree", "social_status_score")},
        "by_density_quintile": areas.groupby(quintile, observed=True).agg(median_residents_per_km2=("density", "median"), median_watered_per_100_street=("watered_per_100_street", "median")).round(2).to_dict(orient="index"),
    }
    out["metadata"] = {
        "grain": "tree-season (April-September) unless stated; planning area for density comparisons",
        "period": "2020-05-18 to 2025-12-31 logs; 2020 is a partial season",
        "zero_semantics": "no logged watering, not no watering",
        "denominators": "current catalogued inventory (not historical stock); watered_trees in area tables include green-space trees",
        "inventory_sha256": sha256(inventory_path),
        "inventory_2025_sha256": sha256(INVENTORY_2025),
    }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--inventory", type=Path, default=ROOT / "data/Berlin_trees.gpkg")
    parser.add_argument("--out", type=Path, default=ROOT / "output/feedback_benchmarks/benchmarks.json")
    args = parser.parse_args()
    result = build(args.inventory)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
