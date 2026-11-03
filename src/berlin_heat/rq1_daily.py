"""Audited daily RQ1 pilot; see docs/rq1_daily_exploratory_protocol.md."""
from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from .watering_response import calendar_hac_ols, read_weather, sha256

START = pd.Timestamp("2020-05-18")
END = pd.Timestamp("2025-12-31")
OUTCOMES = ["events", "litres", "distinct_trees"]
BASE_TERMS = ["tmax_per_5c", "rain_per_10mm", "previous_rain_per_10mm", "dry_spell_per_7d"]


def weather_features(daily: pd.DataFrame) -> pd.DataFrame:
    """Use exact calendar lags; unknown rain breaks dry-spell ascertainment."""
    data = daily.copy().sort_values("date")
    if data.date.duplicated().any():
        raise ValueError("Duplicate weather dates")
    data = data.set_index("date").reindex(pd.date_range(data.date.min(), data.date.max()))
    data.index.name = "date"
    rain = data.rainfall_mm
    dry, state = [], np.nan
    for value in rain:
        dry.append(state)  # ending yesterday, before seeing today's rain
        if pd.isna(value):
            state = np.nan
        elif value >= 1:
            state = 0.0
        elif np.isfinite(state):
            state += 1
    data["antecedent_dry_days"] = dry
    data["previous_day_rain_mm"] = rain.shift(1)
    data["previous_7d_rain_mm"] = rain.shift(1).rolling(7, min_periods=7).sum()
    data["tmax_per_5c"] = data.air_temperature_max_c / 5
    data["rain_per_10mm"] = rain / 10
    data["previous_rain_per_10mm"] = data.previous_day_rain_mm / 10
    data["dry_spell_per_7d"] = data.antecedent_dry_days / 7
    data["previous_7d_rain_per_10mm"] = data.previous_7d_rain_mm / 10
    data["tmax_centered_20c_squared_per_25"] = ((data.air_temperature_max_c - 20) / 5) ** 2
    return data.reset_index()


def clean_events(raw: pd.DataFrame, crosswalk: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if crosswalk.tree_id.isna().any() or crosswalk.tree_id.duplicated().any():
        raise ValueError("Crosswalk tree IDs must be unique and nonmissing")
    data = raw.drop_duplicates().copy()
    timestamp = pd.to_datetime(data.timestamp, format="mixed", utc=True, errors="coerce")
    data["date"] = timestamp.dt.tz_convert("Europe/Berlin").dt.tz_localize(None).dt.normalize()
    data["tree_id"] = data.id.astype("string").str.strip().replace("", pd.NA)
    data["litres"] = pd.to_numeric(data.bewaesserungsmenge_in_liter, errors="coerce")
    in_window = data.date.between(START, END)
    valid = data.tree_id.notna() & np.isfinite(data.litres) & data.litres.gt(0)
    audit = {
        "raw_rows": len(raw), "exact_duplicates_removed": len(raw) - len(data),
        "invalid_timestamps": int(timestamp.isna().sum()),
        "in_window_before_validity_filter": int(in_window.sum()),
        "invalid_id_or_volume_in_window": int((in_window & ~valid).sum()),
    }
    data = data[in_window & valid].copy()
    data["utc_midnight"] = timestamp.loc[data.index].eq(timestamp.loc[data.index].dt.normalize())
    data = data.merge(crosswalk, on="tree_id", how="left", validate="many_to_one")
    data["linked"] = data.plr_id.notna()
    audit.update(valid_events=len(data), linked_events=int(data.linked.sum()),
                 unassigned_events=int((~data.linked).sum()),
                 valid_litres=float(data.litres.sum()),
                 linked_litres=float(data.loc[data.linked, "litres"].sum()),
                 events_above_500l=int(data.litres.gt(500).sum()))
    return data, audit


def season_calendar(unavailable_dates: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    dates = pd.date_range(START, END)
    dates = dates[dates.month.isin(range(4, 10))]
    unavailable = pd.DatetimeIndex([]) if unavailable_dates is None else unavailable_dates
    return pd.DataFrame({"date": dates, "outcome_available": ~dates.isin(unavailable)})


def aggregate_daily(events: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    totals = events.groupby("date").agg(events=("tree_id", "size"), litres=("litres", "sum"),
                                        distinct_trees=("tree_id", "nunique"))
    result = calendar.merge(totals, on="date", how="left", validate="one_to_one")
    for column in OUTCOMES:
        result["extract_" + column] = result[column].fillna(0)
        result[column] = result["extract_" + column].where(result.outcome_available)
    return result


def balanced_area_days(events: pd.DataFrame, areas: pd.DataFrame,
                       calendar: pd.DataFrame) -> pd.DataFrame:
    if areas.plr_id.duplicated().any():
        raise ValueError("Area metadata must be unique")
    if not events.plr_id.isin(areas.plr_id).all():
        raise ValueError("Linked events outside area universe")
    counts = events.groupby(["date", "plr_id"]).agg(
        events=("tree_id", "size"), litres=("litres", "sum"), distinct_trees=("tree_id", "nunique"))
    result = calendar.merge(areas, how="cross").merge(
        counts, on=["date", "plr_id"], how="left", validate="one_to_one")
    for column in OUTCOMES:
        result["extract_" + column] = result[column].fillna(0)
        result[column] = result["extract_" + column].where(result.outcome_available)
    return result.sort_values(["date", "plr_id"]).reset_index(drop=True)


def fit_association(data: pd.DataFrame, *, sample: str, lags: int = 14,
                    specification: str = "baseline") -> tuple[pd.DataFrame, dict]:
    terms = list(BASE_TERMS)
    if specification == "antecedent_rain":
        terms = ["tmax_per_5c", "rain_per_10mm", "previous_7d_rain_per_10mm"]
    if specification == "quadratic_temperature":
        terms += ["tmax_centered_20c_squared_per_25"]
    complete = data.dropna(subset=terms + OUTCOMES).sort_values("date").copy()
    controls = pd.DataFrame({"year": complete.date.dt.year.astype(str),
                             "month": complete.date.dt.month.astype(str),
                             "weekday": complete.date.dt.dayofweek.astype(str)}, index=complete.index)
    if specification == "year_month":
        controls = controls.drop(columns=["year", "month"])
        controls["year_month"] = complete.date.dt.strftime("%Y-%m")
    x = pd.concat([pd.Series(1.0, index=complete.index, name="intercept"), complete[terms],
                   ((complete.date.dt.day - 15) / 30).rename("within_month_trend"),
                   pd.get_dummies(controls, drop_first=True, dtype=float)], axis=1)
    rows = []
    for outcome in OUTCOMES:
        beta, cov = calendar_hac_ols(x.to_numpy(), np.log1p(complete[outcome]),
                                    (complete.date - START).dt.days.to_numpy(), max_lag=lags)
        for term in terms:
            i = x.columns.get_loc(term)
            se = np.sqrt(max(0.0, cov[i, i]))
            rows.append({"sample": sample, "specification": specification, "outcome": outcome,
                         "term": term, "n_days": len(complete), "n_parameters": x.shape[1],
                         "hac_lag_days": lags, "coefficient_log1p": beta[i], "standard_error": se,
                         "approx_95_low": beta[i] - 1.96 * se, "approx_95_high": beta[i] + 1.96 * se})
    audit = {"sample": sample, "specification": specification, "hac_lag_days": lags,
             "candidate_days": len(data), "complete_days": len(complete),
             "excluded_dates": data.loc[~data.date.isin(complete.date), "date"].dt.strftime("%Y-%m-%d").tolist(),
             "design_condition_number": float(np.linalg.cond(x.to_numpy()))}
    return pd.DataFrame(rows), audit


def annual_summary(city: pd.DataFrame, events: pd.DataFrame, area: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, days in city.groupby(city.date.dt.year):
        available = days[days.outcome_available]
        logs = events[events.date.isin(available.date)]
        area_days = area[area.date.isin(available.date)]
        rows.append({"year": year, "calendar_days": len(days), "available_days": len(available),
                     "events": int(available.events.sum()), "litres": float(available.litres.sum()),
                     "distinct_trees": int(logs.tree_id.nunique()),
                     "mean_events_per_day": available.events.mean(),
                     "event_variance_to_mean": available.events.var() / available.events.mean(),
                     "zero_city_day_share": available.events.eq(0).mean(),
                     "zero_area_day_share": area_days.events.eq(0).mean(),
                     "active_areas": int(logs.plr_id.nunique()),
                     "share_events_at_utc_midnight": logs.utc_midnight.mean(),
                     "days_with_missing_weather_features": int(days[BASE_TERMS].isna().any(axis=1).sum())})
    return pd.DataFrame(rows)


def write_figures(output: Path, city: pd.DataFrame, annual: pd.DataFrame, fits: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    colors = ["#006d77", "#457b9d", "#e29578", "#b56576", "#6d597a", "#d49b00"]
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
    for color, (year, days) in zip(colors, city.groupby(city.date.dt.year)):
        rolling = days.set_index("date").events.rolling(7, min_periods=7).mean()
        axes[0].plot(days.date.dt.dayofyear, rolling.to_numpy(), label=str(year), color=color, lw=1.5)
    axes[0].set(xlabel="Day of year", ylabel="Events/day · trailing 7-day mean",
                title="Logged watering varies strongly across seasons")
    axes[0].legend(ncol=6, frameon=False)
    axes[1].bar(annual.year.astype(str), annual.mean_events_per_day, color=colors)
    axes[1].set(ylabel="Mean events per observed season day", xlabel="Year (2020 starts 18 May)")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.18)
    fig.suptitle("RQ1 pilot · linked logs · April–September", fontsize=16)
    fig.savefig(output / "seasonal_activity.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)
    for ax, term, title in zip(axes, ["tmax_per_5c", "dry_spell_per_7d"],
                               ["Tmax: +5°C", "Antecedent dry spell: +7 days"]):
        values = fits[(fits.outcome == "events") & (fits.term == term)
                      & fits["sample"].str.startswith("year_")]
        y = np.arange(len(values))
        ax.errorbar(values.coefficient_log1p, y,
                    xerr=np.vstack([values.coefficient_log1p - values.approx_95_low,
                                    values.approx_95_high - values.coefficient_log1p]),
                    fmt="o", color="#006d77", capsize=4)
        ax.set_yticks(y, values["sample"].str.replace("year_", ""))
        ax.axvline(0, color="#999999", lw=1)
        ax.set(title=title, xlabel="Change in log(1 + daily events)")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Year-specific adjusted associations · approximate 95% HAC intervals\n"
                 "Exploratory estimates; interval overlap does not establish stability", fontsize=13)
    fig.savefig(output / "annual_associations.png", dpi=170)
    plt.close(fig)


def write_report(output: Path, annual: pd.DataFrame, fits: pd.DataFrame, audit: dict) -> None:
    lines = ["# RQ1: daily civic climate response — initial results", "",
             "Exploratory pilot · 26 October 2026. Reproduce with "
             "`PYTHONPATH=src .venv/bin/python pipelines/08_build_rq1_daily.py`.", "",
             "## What this analysis establishes", "",
             "A reconciled daily input panel and adjusted citywide associations for the refined proposal's RQ1. "
             "These are linked all-tree logs, not the final street-tree rate sample. "
             "The hierarchical negative-binomial and two-part volume models remain to be fitted.", "",
             "## Sample audit", "",
             f"- {audit['events']['raw_rows']:,} source rows; {audit['events']['exact_duplicates_removed']:,} exact duplicates removed.",
             f"- {audit['events']['valid_events']:,} valid positive source logs in the platform window; "
             f"{audit['events']['linked_events']:,} linked events and {audit['events']['linked_litres']:,.0f} linked litres reconcile to the canonical daily product.",
             f"- The April–September panel has {audit['season_days']:,} calendar days × {audit['areas']} planning areas = {audit['area_day_rows']:,} rows.",
             f"- {audit['unavailable_days']} days are explicitly unavailable. Without an outage calendar, zeros mean no log in the extract under assumed platform availability.",
             "- Citywide source totals also retain unassigned logs as a coverage sensitivity, not verified Berlin events.",
             "- Dates before 18 May 2020 are absent. 2020 is a partial season. Current inventory is contextual, not a historical risk set.", "",
             "## Seasonal activity", "",
             "| Year | Days | Events | Litres | Distinct trees | Events/day | Variance/mean | Zero area-days |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in annual.itertuples():
        lines.append(f"| {r.year} | {r.available_days} | {r.events:,} | {r.litres:,.0f} | {r.distinct_trees:,} | "
                     f"{r.mean_events_per_day:.1f} | {r.event_variance_to_mean:.1f} | {r.zero_area_day_share:.1%} |")
    lines += ["", "![Seasonal activity](seasonal_activity.png)", "", "## Calendar-adjusted baseline", "",
              "OLS outcomes are log(1 + daily total). Controls are year, month, weekday and a common "
              "within-month linear trend. All four weather terms enter together. Approximate 95% intervals "
              "use 14 actual calendar-day HAC lags. These coefficients are not exact percentage changes "
              "in mean counts or litres, and intervals are not multiplicity-adjusted.", "",
              "| Outcome | Weather increment | Days | Coefficient | Approx. 95% interval |",
              "| --- | --- | ---: | ---: | --- |"]
    labels = {"tmax_per_5c": "Tmax +5°C", "rain_per_10mm": "Today's rain +10 mm",
              "previous_rain_per_10mm": "Yesterday's rain +10 mm", "dry_spell_per_7d": "Prior dry spell +7 days"}
    baseline = fits[(fits["sample"] == "linked_baseline") & (fits.hac_lag_days == 14)]
    for r in baseline.itertuples():
        lines.append(f"| {r.outcome} | {labels[r.term]} | {r.n_days} | {r.coefficient_log1p:.3f} | "
                     f"[{r.approx_95_low:.3f}, {r.approx_95_high:.3f}] |")
    event_fits = fits[(fits.outcome == "events") & (fits.hac_lag_days == 14)]
    annual_heat = event_fits[(event_fits.term == "tmax_per_5c") & event_fits["sample"].str.startswith("year_")]
    lines += ["", "## Initial interpretation", "",
              f"The annual temperature coefficients range from {annual_heat.coefficient_log1p.min():.3f} "
              f"to {annual_heat.coefficient_log1p.max():.3f} log1p units per +5°C. "
              f"{int(annual_heat.coefficient_log1p.gt(0).sum())} of {len(annual_heat)} annual estimates are positive. "
              "The magnitude varies, so a common direction is not evidence of a constant response.", "",
              "The event model remains strongly overdispersed in the raw annual summaries, "
              "and most area-days have no recorded event. This supports proceeding to the planned "
              "hierarchical count model rather than interpreting the citywide baseline as local response estimates.", "",
              "Selected sensitivity estimates below are prespecified specifications, all reported for "
              "the event outcome. Full results for all three outcomes are in the coefficient table.", "",
              "| Specification | Tmax +5°C | Prior dry spell +7 days |",
              "| --- | --- | --- |"]
    for name in ["linked_baseline", "exclude_2020", "exclude_2022", "exclude_over_500l",
                 "all_valid_source_logs", "linked_year_month", "early_2020_2022", "late_2023_2025"]:
        cells = []
        for term in ["tmax_per_5c", "dry_spell_per_7d"]:
            row = event_fits[(event_fits["sample"] == name) & (event_fits.term == term)].iloc[0]
            cells.append(f"{row.coefficient_log1p:.3f} [{row.approx_95_low:.3f}, {row.approx_95_high:.3f}]")
        lines.append(f"| {name} | {' | '.join(cells)} |")
    lines += ["", "## Temporal stability and sensitivity", "",
              "![Annual associations](annual_associations.png)", "",
              "The complete grid in [model_coefficients.csv](tables/model_coefficients.csv) includes "
              "annual and early/late fits, removal of 2020 or 2022, exclusion of >500 L logs, source-coverage "
              "sensitivity, HAC bandwidths, year-by-month controls, quadratic temperature and antecedent rain. "
              "Annual fits describe heterogeneity; they do not establish stability or formally compare slopes. "
              "Quadratic temperature makes the linear term a slope at 20°C; read both terms together.", "",
              "## Limits and next analysis", "",
              "1. Treat weather associations as descriptive. Day-level logging dates need not be actual watering dates. "
              "Most 2024 and all 2025 source timestamps are UTC midnight; hourly comparisons are unsupported.",
              "2. Verify platform availability and match street-tree logs to a street-tree stock. Include never-active eligible areas; "
              "flag their partially pooled slopes as weakly identified. Inventory age alone does not identify municipal care.",
              "3. Add documented holiday, campaign and participation covariates; specify nonlinear terms and formal annual contrasts "
              "before fitting the hierarchical count and two-part volume models.",
              "4. Validate across held-out seasons and spatial blocks. All 2020–2025 seasons have now been inspected; "
              "future validation on these seasons is retrospective, not an untouched confirmatory test.",
              "5. Weather comes from one station. Missing rainfall propagates into lag/dryness features; "
              "it is not filled with zero. A dry spell is a meteorological proxy, not measured tree water stress.", "",
              "See [protocol](../../docs/rq1_daily_exploratory_protocol.md), "
              "[annual audit](tables/annual_summary.csv), [fit inclusion audit](model_audit.json), "
              "and [source checksums](metadata.json).", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def build_daily_pilot(root: Path, *, unavailable_path: Path | None = None) -> dict:
    output = root / "output/rq1_daily"
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    processed = root / "data/processed/rq1"
    processed.mkdir(parents=True, exist_ok=True)
    paths = {
        "logs": root / "data/giessdenkiez_bewässerungsdaten (1).csv",
        "crosswalk": root / "data/processed/foundation/recorded_tree_lor_crosswalk_2020_2025.csv",
        "foundation": root / "data/processed/foundation/lor_month_recorded_watering_2020_2025.csv",
        "tree_day": root / "data/processed/temporal/recorded_tree_day_watering_2020_2025.csv",
        "weather": root / "data/raw/dwd/tageswerte_KL_00433_19480101_20251231_hist.zip",
    }
    raw = pd.read_csv(paths["logs"], sep=";", dtype={"id": "string"})
    crosswalk = pd.read_csv(paths["crosswalk"], dtype="string")
    events, event_audit = clean_events(raw, crosswalk)
    linked = events[events.linked].copy()
    canonical = pd.read_csv(paths["tree_day"], dtype={"tree_id": str}, parse_dates=["local_date"])
    expected = canonical.groupby("local_date")[["recorded_watering_events", "recorded_litres"]].sum()
    actual = linked.groupby("date").agg(recorded_watering_events=("tree_id", "size"), recorded_litres=("litres", "sum"))
    pd.testing.assert_frame_equal(actual.rename_axis("local_date"), expected, check_dtype=False)
    foundation = pd.read_csv(paths["foundation"], dtype={"plr_id": str, "bzr_id": str})
    area_columns = ["plr_id", "plr_name", "bzr_id", "bzr_name", "district", "current_inventory_trees"]
    areas = foundation[area_columns].drop_duplicates()
    unavailable = None
    if unavailable_path is not None:
        unavailable_frame = pd.read_csv(unavailable_path, parse_dates=["date"])
        unavailable = pd.DatetimeIndex(unavailable_frame.date)
        if unavailable.has_duplicates or unavailable.isna().any() or not unavailable.equals(unavailable.normalize()):
            raise ValueError("Unavailable dates must be unique valid calendar dates")
        paths["unavailable_dates"] = unavailable_path
    calendar = season_calendar(unavailable)
    weather, _, weather_audit = read_weather(paths["weather"])
    weather = weather_features(weather)
    weather.to_csv(tables / "daily_weather_features.csv", index=False)
    variants = {}
    for name, logs in [("linked_baseline", linked), ("exclude_over_500l", linked[linked.litres.le(500)]),
                       ("all_valid_source_logs", events)]:
        variants[name] = aggregate_daily(logs, calendar).merge(weather, on="date", how="left", validate="one_to_one")
        variants[name].to_csv(tables / f"city_day_{name}.csv", index=False)
    city = variants["linked_baseline"]
    area = balanced_area_days(linked, areas, calendar)
    for metric in OUTCOMES:
        np.testing.assert_allclose(area.groupby("date")["extract_" + metric].sum(),
                                   city.set_index("date")["extract_" + metric])
    area.to_csv(processed / "lor_day_recorded_watering_apr_sep_2020_2025.csv.gz", index=False,
                compression={"method": "gzip", "mtime": 0})
    annual = annual_summary(city, linked, area)
    annual.to_csv(tables / "annual_summary.csv", index=False)
    specs = [(name, data, 14, "baseline") for name, data in variants.items()]
    specs += [("exclude_2020", city[city.date.dt.year.ge(2021)], 14, "baseline"),
              ("exclude_2022", city[city.date.dt.year.ne(2022)], 14, "baseline")]
    specs += [("linked_baseline", city, lag, "baseline") for lag in [7, 28]]
    specs += [("linked_" + spec, city, 14, spec) for spec in
              ["year_month", "quadratic_temperature", "antecedent_rain"]]
    specs += [(f"year_{year}", city[city.date.dt.year.eq(year)], 14, "baseline") for year in range(2020, 2026)]
    specs += [("early_2020_2022", city[city.date.dt.year.le(2022)], 14, "baseline"),
              ("late_2023_2025", city[city.date.dt.year.ge(2023)], 14, "baseline")]
    fits, fit_audit = [], []
    for name, data, lag, spec in specs:
        result, inclusion = fit_association(data, sample=name, lags=lag, specification=spec)
        fits.append(result)
        fit_audit.append(inclusion)
    fits = pd.concat(fits, ignore_index=True)
    fits.to_csv(tables / "model_coefficients.csv", index=False)
    (output / "model_audit.json").write_text(json.dumps(fit_audit, indent=2) + "\n")
    audit = {"protocol": "docs/rq1_daily_exploratory_protocol.md", "events": event_audit,
             "season_days": len(calendar), "areas": len(areas), "area_day_rows": len(area),
             "unavailable_days": int((~calendar.outcome_available).sum()),
             "outage_calendar_supplied": unavailable_path is not None,
             "season_events": int(city.extract_events.sum()), "season_litres": float(city.extract_litres.sum()),
             "weather": weather_audit,
             "software": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
             "code_sha256": {name: sha256(root / name) for name in
                             ["src/berlin_heat/rq1_daily.py", "src/berlin_heat/watering_response.py",
                              "pipelines/08_build_rq1_daily.py", "docs/rq1_daily_exploratory_protocol.md"]},
             "source_sha256": {str(path.relative_to(root)) if path.is_relative_to(root) else str(path): sha256(path)
                                                         for path in paths.values()},
             "semantics": "No-log zeros conditional on assumed availability; all-tree linked sample, no historical offset; exploratory log1p OLS, not hierarchical NB."}
    (output / "metadata.json").write_text(json.dumps(audit, indent=2) + "\n")
    write_figures(output, city, annual, fits)
    write_report(output, annual, fits, audit)
    return audit
