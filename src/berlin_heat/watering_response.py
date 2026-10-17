"""Exploratory monthly recorded-care panel and station-weather associations.

This module deliberately keeps air-temperature response separate from LST
cooling. See docs/watering_response_exploratory_protocol.md for the protocol.
"""
from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

DWD_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/historical/tageswerte_KL_00433_19480101_20251231_hist.zip"
)
DWD_DESCRIPTION = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/DESCRIPTION_obsgermany-climate-daily-kl_en.pdf"
)
METRICS = ["recorded_watering_events", "recorded_litres", "recorded_watered_trees"]
STATUS_LABELS = {
    "hoch": "High", "mittel": "Middle", "niedrig": "Low",
    "sehr niedrig": "Very low",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rates(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    denominator = result.current_inventory_trees.where(result.current_inventory_trees.gt(0))
    result["recorded_events_per_1000_current_inventory_trees"] = (
        1000 * result.recorded_watering_events / denominator
    )
    result["recorded_litres_per_current_inventory_tree"] = result.recorded_litres / denominator
    result["recorded_reach_pct_current_inventory"] = 100 * result.recorded_watered_trees / denominator
    return result


def aggregate_monthly(foundation: pd.DataFrame, tree_day: pd.DataFrame,
                      geography: str) -> pd.DataFrame:
    """Aggregate disjoint assigned trees, then verify distinct IDs directly."""
    base = foundation.copy()
    days = tree_day.copy()
    if geography == "city":
        base[geography] = "Berlin"
        days[geography] = "Berlin"
    keys = ["month", geography]
    grouped = base.groupby(keys, as_index=False).agg(
        current_inventory_trees=("current_inventory_trees", "sum"),
        recorded_watering_events=(METRICS[0], "sum"),
        recorded_litres=(METRICS[1], "sum"),
        foundation_distinct_trees=(METRICS[2], "sum"),
        platform_month_status=("platform_month_status", "first"),
        platform_live_days=("platform_live_days", "first"),
    )
    distinct = days.groupby(keys).tree_id.nunique().rename(METRICS[2])
    grouped = grouped.merge(distinct, on=keys, how="left", validate="one_to_one")
    grouped[METRICS[2]] = grouped[METRICS[2]].fillna(0).astype(int)
    if not grouped[METRICS[2]].eq(grouped.foundation_distinct_trees).all():
        raise ValueError(f"Distinct tree counts do not reconcile for {geography}.")
    grouped = grouped.drop(columns="foundation_distinct_trees")
    grouped["year"] = grouped.month.dt.year
    grouped["calendar_month"] = grouped.month.dt.month
    return rates(grouped).sort_values(keys).reset_index(drop=True)


def read_weather(archive: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    with zipfile.ZipFile(archive) as source:
        members = [n for n in source.namelist() if n.startswith("produkt_klima_tag_")]
        if len(members) != 1:
            raise ValueError("Expected one DWD daily product.")
        raw = pd.read_csv(io.BytesIO(source.read(members[0])), sep=";")
        raw.columns = raw.columns.str.strip()
        geography = source.read("Metadaten_Geographie_00433.txt").decode("latin1")
    if set(raw.STATIONS_ID) != {433}:
        raise ValueError("Unexpected station in DWD archive.")
    raw["date"] = pd.to_datetime(raw.MESS_DATUM.astype(str), format="%Y%m%d")
    if raw.date.duplicated().any():
        raise ValueError("Duplicate DWD daily dates.")
    raw = raw.set_index("date").reindex(pd.date_range("2020-01-01", "2025-12-31"))
    raw.index.name = "date"
    columns = {"TMK": "air_temperature_mean_c", "TXK": "air_temperature_max_c",
               "RSK": "rainfall_mm", "QN_3": "quality_code_wind",
               "QN_4": "quality_code_climate"}
    daily = raw[list(columns)].rename(columns=columns).replace(-999, np.nan).reset_index()
    daily["station_id"] = "00433"
    daily["month"] = daily.date.dt.to_period("M").dt.to_timestamp()
    rows = []
    for month, group in daily.groupby("month"):
        n = month.days_in_month
        temp_days = int(group.air_temperature_mean_c.count())
        rain_days = int(group.rainfall_mm.count())
        max_days = int(group.air_temperature_max_c.count())
        rows.append({
            "month": month, "station_id": "00433", "expected_days": n,
            "valid_temperature_days": temp_days, "valid_rainfall_days": rain_days,
            "valid_max_temperature_days": max_days,
            "air_temperature_mean_c": group.air_temperature_mean_c.mean() if temp_days == n else np.nan,
            "rainfall_mm": group.rainfall_mm.sum() if rain_days == n else np.nan,
            "days_max_temperature_ge_30c": int(group.air_temperature_max_c.ge(30).sum()) if max_days == n else np.nan,
        })
    monthly = pd.DataFrame(rows)
    # Reindexed complete calendar ensures shift means previous month, not previous available row.
    for column in ["air_temperature_mean_c", "rainfall_mm"]:
        monthly[f"previous_month_{column}"] = monthly[column].shift(1)
    audit = {
        "station_name": "Berlin-Tempelhof", "station_id": "00433",
        "daily_rows": len(daily), "monthly_rows": len(monthly),
        "missing_temperature_days": int(daily.air_temperature_mean_c.isna().sum()),
        "missing_rainfall_days": int(daily.rainfall_mm.isna().sum()),
        "incomplete_rainfall_months": monthly.loc[monthly.rainfall_mm.isna(), "month"].dt.strftime("%Y-%m").tolist(),
        "climate_quality_codes": {str(k): int(v) for k, v in daily.quality_code_climate.value_counts(dropna=False).items()},
        "station_geography_metadata": geography,
        "monthly_completeness_rule": "100% valid daily values, separately per variable",
    }
    return daily, monthly, audit


def calendar_hac_ols(x: np.ndarray, y: np.ndarray, time: np.ndarray,
                     max_lag: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """OLS with Bartlett HAC by actual monthly distance and n/(n-k) correction.

    Missing calendar months contribute no score; gaps are never collapsed.
    """
    x, y, time = np.asarray(x, float), np.asarray(y, float), np.asarray(time, int)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) < k:
        raise ValueError("Insufficient observations or rank-deficient design.")
    if len(np.unique(time)) != n or np.any(np.diff(time) <= 0):
        raise ValueError("HAC dates must be unique and strictly increasing.")
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    scores = x * (y - x @ beta)[:, None]
    meat = scores.T @ scores
    positions = {int(t): i for i, t in enumerate(time)}
    for lag in range(1, max_lag + 1):
        pairs = [(i, positions[int(t) - lag]) for i, t in enumerate(time) if int(t) - lag in positions]
        if pairs:
            left, right = zip(*pairs)
            cross = scores[list(left)].T @ scores[list(right)]
            meat += (1 - lag / (max_lag + 1)) * (cross + cross.T)
    bread = np.linalg.inv(x.T @ x)
    covariance = bread @ meat @ bread * n / (n - k)
    return beta, covariance


def fit_monthly_associations(city: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, raw_rows = [], []
    eligible = city[city.year.between(2021, 2025)].copy()
    for sample in ["2021-2025", "excluding_2022"]:
        sample_rows = eligible if sample == "2021-2025" else eligible[eligible.year.ne(2022)]
        for timing in ["same_month", "previous_month"]:
            prefix = "" if timing == "same_month" else "previous_month_"
            temp = prefix + "air_temperature_mean_c"
            rain = prefix + "rainfall_mm"
            for outcome in METRICS:
                for weather_column in [temp, rain]:
                    available = sample_rows[[outcome, weather_column]].dropna()
                    rho = available.rank().corr().iloc[0, 1]
                    raw_rows.append({"sample": sample, "timing": timing, "outcome": outcome,
                                     "weather_variable": weather_column, "n_months": len(available),
                                     "spearman_rho": rho})
                data = sample_rows.dropna(subset=[outcome, temp, rain]).sort_values("month")
                controls = pd.get_dummies(data[["calendar_month", "year"]].astype(str), drop_first=True, dtype=float)
                design = pd.concat([
                    pd.Series(1.0, index=data.index, name="intercept"),
                    (data[temp] / 5).rename("temperature_per_5c"),
                    (data[rain] / 10).rename("rainfall_per_10mm"), controls], axis=1)
                time = data.month.dt.year * 12 + data.month.dt.month
                beta, covariance = calendar_hac_ols(design.to_numpy(), np.log1p(data[outcome]), time.to_numpy())
                for index, term in [(1, "temperature_per_5c"), (2, "rainfall_per_10mm")]:
                    se = np.sqrt(max(0, covariance[index, index]))
                    rows.append({
                        "sample": sample, "timing": timing, "outcome": outcome, "term": term,
                        "n_months": len(data), "n_parameters": design.shape[1],
                        "coefficient_log1p": beta[index], "standard_error_hac3": se,
                        "approx_95_low": beta[index] - 1.96 * se,
                        "approx_95_high": beta[index] + 1.96 * se,
                        "month_controls": True, "year_controls": True,
                        "interpretation": "exploratory association in log(1+outcome) units; not a causal effect",
                    })
    return pd.DataFrame(rows), pd.DataFrame(raw_rows)


def build_response_tables(root: Path, output: Path) -> dict:
    table_dir = output / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    foundation_path = root / "data/processed/foundation/lor_month_recorded_watering_2020_2025.csv"
    tree_day_path = root / "data/processed/temporal/recorded_tree_day_watering_2020_2025.csv"
    equity_path = root / "output/equity/tables/lor_watering_equity_metrics.csv"
    archive = root / "data/raw/dwd/tageswerte_KL_00433_19480101_20251231_hist.zip"
    foundation = pd.read_csv(foundation_path, dtype={"plr_id": str, "bzr_id": str}, parse_dates=["month"])
    tree_day = pd.read_csv(tree_day_path, dtype={"tree_id": str, "plr_id": str, "bzr_id": str}, parse_dates=["local_date"])
    tree_day["month"] = tree_day.local_date.dt.to_period("M").dt.to_timestamp()
    equity = pd.read_csv(equity_path, dtype={"plr_id": str})
    if foundation.duplicated(["month", "plr_id"]).any() or equity.plr_id.duplicated().any():
        raise ValueError("Non-unique geography/month or social-status keys.")
    if not np.isclose(foundation.recorded_litres.sum(), tree_day.recorded_litres.sum()):
        raise ValueError("Tree-day and foundation litres disagree.")
    if foundation.recorded_watering_events.sum() != tree_day.recorded_watering_events.sum():
        raise ValueError("Tree-day and foundation events disagree.")
    city = aggregate_monthly(foundation, tree_day, "city")
    districts = aggregate_monthly(foundation, tree_day, "district")
    lor = foundation.merge(equity[["plr_id", "si_v", "s4", "thermal_burden"]],
                           on="plr_id", how="left", validate="many_to_one")
    lor["social_status_2024"] = lor.si_v.map(STATUS_LABELS).fillna("Unclassified")
    lor = lor.rename(columns={"s4": "child_poverty_pct_2024", "thermal_burden": "thermal_burden_2023_24"}).drop(columns="si_v")
    tree_day = tree_day.merge(lor[["plr_id", "social_status_2024"]].drop_duplicates(),
                              on="plr_id", how="left", validate="many_to_one")
    social = aggregate_monthly(lor, tree_day, "social_status_2024")
    daily_weather, monthly_weather, weather_audit = read_weather(archive)
    city = city.merge(monthly_weather, on="month", how="left", validate="one_to_one")
    district_weather = districts.merge(monthly_weather, on="month", how="left", validate="many_to_one")
    district_weather["weather_scope"] = "shared_Berlin_Tempelhof_station_context_not_district_temperature"
    annual = tree_day.groupby("year", as_index=False).agg(
        recorded_watering_events=(METRICS[0], "sum"), recorded_litres=(METRICS[1], "sum"),
        recorded_watered_trees=("tree_id", "nunique"))
    annual["period"] = np.where(annual.year.eq(2020), "18 May–31 December (partial year)", "January–December")
    season_days = tree_day[tree_day.local_date.dt.month.between(6, 9)].copy()
    summer = season_days.groupby("year", as_index=False).agg(
        recorded_watering_events=(METRICS[0], "sum"), recorded_litres=(METRICS[1], "sum"),
        recorded_watered_trees=("tree_id", "nunique"))
    summer_weather = daily_weather[daily_weather.date.dt.month.between(6, 9)].copy()
    summer_weather["year"] = summer_weather.date.dt.year
    summer_weather = summer_weather.groupby("year", as_index=False).agg(
        mean_air_temperature_c=("air_temperature_mean_c", "mean"),
        valid_temperature_days=("air_temperature_mean_c", "count"),
        rainfall_mm=("rainfall_mm", "sum"), valid_rainfall_days=("rainfall_mm", "count"),
        hot_days_ge_30c=("air_temperature_max_c", lambda s: int(s.ge(30).sum())),
        valid_max_temperature_days=("air_temperature_max_c", "count"))
    summer_weather.loc[summer_weather.valid_rainfall_days.ne(122), "rainfall_mm"] = np.nan
    summer_weather.loc[summer_weather.valid_temperature_days.ne(122), "mean_air_temperature_c"] = np.nan
    summer_weather.loc[summer_weather.valid_max_temperature_days.ne(122), "hot_days_ge_30c"] = np.nan
    summer = summer.merge(summer_weather, on="year", validate="one_to_one")
    coefficients, correlations = fit_monthly_associations(city)
    district_changes = districts[districts.calendar_month.between(6, 9)].groupby(["district", "year"])[METRICS[:2]].sum().reset_index()
    unique_season = season_days.groupby(["district", "year"]).tree_id.nunique().rename(METRICS[2])
    district_changes = district_changes.merge(unique_season, on=["district", "year"], validate="one_to_one")
    tables = {
        "berlin_month_weather_watering": city,
        "district_month_watering": districts,
        "district_month_station_context": district_weather,
        "lor_month_watering_social_context": lor,
        "social_status_month_watering": social,
        "berlin_year_watering": annual,
        "berlin_june_september_comparison": summer,
        "district_june_september_comparison": district_changes,
        "dwd_00433_daily_2020_2025": daily_weather,
        "dwd_00433_monthly_2020_2025": monthly_weather,
        "monthly_adjusted_associations": coefficients,
        "monthly_raw_correlations": correlations,
    }
    for name, frame in tables.items():
        frame.to_csv(table_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "weather_archive_retrieved_date": "2026-09-29",
        "protocol": "docs/watering_response_exploratory_protocol.md",
        "source_urls": {"dwd_archive": DWD_URL, "dwd_description": DWD_DESCRIPTION},
        "inputs": {str(p.relative_to(root)): sha256(p) for p in [foundation_path, tree_day_path, equity_path, archive]},
        "code_and_protocol_sha256": {str(p.relative_to(root)): sha256(p) for p in [
            root / "src/berlin_heat/watering_response.py", root / "docs/watering_response_exploratory_protocol.md"]},
        "weather_audit": weather_audit,
        "audit": {"months": len(city), "districts": int(districts.district.nunique()),
                  "district_months": len(districts), "lor_months": len(lor),
                  "events": int(city.recorded_watering_events.sum()),
                  "litres": float(city.recorded_litres.sum()),
                  "unique_trees_entire_period": int(tree_day.tree_id.nunique()),
                  "unclassified_lors": int(lor.loc[lor.social_status_2024.eq("Unclassified"), "plr_id"].nunique()),
                  "model_eligible_months_before_weather_exclusions": 60},
        "table_rows": {name: len(frame) for name, frame in tables.items()},
        "output_sha256": {name: sha256(table_dir / f"{name}.csv") for name in tables},
        "limits": ["Matched recorded activity only; unlogged and municipal watering unobserved.",
                   "Current tree inventory denominators are not historical coverage.",
                   "MSS 2025 categories refer to end-2024, not historical district income.",
                   "DWD station air temperature is shared temporal context, not Landsat LST.",
                   "No causal cooling or municipal allocation result is estimated.",
                   ("Supplied Ortsteil LST/rainfall CSV is available; see the separately audited provisional extension."
                    if (root / "data/raw/supervisor/berlin_ortsteile_LST_rain_2018_2025_LNDSAT.csv").exists()
                    else "The supplied Ortsteil LST/rainfall CSV is unavailable behind sign-in.")],
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    return {"tables": tables, "metadata": metadata}
