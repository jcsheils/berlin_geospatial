"""Daily pilot coverage, causal ordering of features, and numerical safeguards."""
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from berlin_heat.rq1_daily import (aggregate_daily, balanced_area_days, clean_events,
                                    season_calendar, weather_features)
from berlin_heat.watering_response import calendar_hac_ols

ROOT = Path(__file__).resolve().parents[1]


class DailyPilotTests(unittest.TestCase):
    def weather(self, rain):
        return pd.DataFrame({"date": pd.date_range("2021-03-27", periods=len(rain)),
                             "rainfall_mm": rain, "air_temperature_max_c": 20.0})

    def test_dry_spell_is_antecedent_and_unknown_until_wet_reset(self):
        data = weather_features(self.weather([0, 2, 0, 0, np.nan, 0, 3, 0]))
        np.testing.assert_allclose(data.antecedent_dry_days,
                                   [np.nan, np.nan, 0, 1, 2, np.nan, np.nan, 0], equal_nan=True)
        # Today's wet weather must not change the antecedent value.
        changed = self.weather([0, 2, 0, 100, np.nan, 0, 3, 0])
        self.assertEqual(weather_features(changed).antecedent_dry_days.iloc[3], 1)

    def test_weather_lags_cross_season_boundary_not_missing_day(self):
        source = self.weather([2, 0, 0, 0, 0, 0, 0, 0, 0])
        data = weather_features(source).set_index("date")
        self.assertEqual(data.loc["2021-04-01", "antecedent_dry_days"], 4)
        self.assertEqual(data.loc["2021-04-03", "previous_7d_rain_mm"], 2)
        gap = weather_features(source.drop(index=3)).set_index("date")
        self.assertTrue(pd.isna(gap.loc["2021-03-31", "previous_day_rain_mm"]))
        self.assertTrue(pd.isna(gap.loc["2021-04-03", "previous_7d_rain_mm"]))

    def test_prelaunch_and_outages_are_not_zero_observations(self):
        calendar = season_calendar(pd.DatetimeIndex(["2020-05-19"]))
        self.assertEqual(calendar.date.min(), pd.Timestamp("2020-05-18"))
        self.assertEqual(len(calendar), 1051)
        self.assertFalse(calendar.date.dt.month.isin([1, 2, 3, 10, 11, 12]).any())
        events = pd.DataFrame({"date": pd.to_datetime(["2020-05-18", "2020-05-18", "2020-05-19"]),
                               "tree_id": ["a", "a", "b"], "litres": [10., 20., 40.],
                               "plr_id": ["01", "01", "01"]})
        areas = pd.DataFrame({"plr_id": ["01", "02"], "current_inventory_trees": [20, 5]})
        city = aggregate_daily(events, calendar).set_index("date")
        area = balanced_area_days(events, areas, calendar)
        self.assertEqual(city.loc["2020-05-18", "events"], 2)
        self.assertEqual(city.loc["2020-05-18", "distinct_trees"], 1)
        self.assertTrue(pd.isna(city.loc["2020-05-19", "events"]))
        self.assertEqual(city.loc["2020-05-19", "extract_events"], 1)
        self.assertEqual(city.loc["2020-05-20", "events"], 0)
        self.assertEqual(len(area), 2 * len(calendar))
        self.assertTrue(area.loc[area.plr_id.eq("02") & area.outcome_available, "events"].eq(0).all())
        self.assertTrue(area.loc[~area.outcome_available, "events"].isna().all())

    def test_source_duplicates_local_dates_and_volume_sensitivity(self):
        raw = pd.DataFrame({"id": ["a", "a", "b", "c", "d", "e"],
                            "timestamp": ["2021-04-01T23:30:00Z"] * 6,
                            "bewaesserungsmenge_in_liter": [20, 20, 600, -1, np.inf, 0]})
        crosswalk = pd.DataFrame({"tree_id": ["a", "b"], "plr_id": ["01", "01"]})
        logs, audit = clean_events(raw, crosswalk)
        self.assertEqual(audit["exact_duplicates_removed"], 1)
        self.assertEqual(audit["invalid_id_or_volume_in_window"], 3)
        self.assertEqual(len(logs), 2)
        self.assertTrue(logs.date.eq("2021-04-02").all())
        calendar = pd.DataFrame({"date": pd.to_datetime(["2021-04-02"]), "outcome_available": [True]})
        self.assertEqual(aggregate_daily(logs, calendar).litres.iloc[0], 620)
        self.assertEqual(aggregate_daily(logs[logs.litres.le(500)], calendar).litres.iloc[0], 20)
        with self.assertRaises(ValueError):
            clean_events(raw, pd.concat([crosswalk, crosswalk]))

    def test_daily_hac_matches_pairwise_reference_across_season_gaps(self):
        rng = np.random.default_rng(19)
        time = np.r_[np.arange(40), np.arange(220, 260)]
        x = np.column_stack([np.ones(80), rng.normal(size=80)])
        y = rng.normal(size=80)
        beta, cov = calendar_hac_ols(x, y, time, max_lag=14)
        residual = y - x @ beta
        weights = np.maximum(0, 1 - abs(time[:, None] - time[None, :]) / 15)
        bread = np.linalg.inv(x.T @ x)
        expected = bread @ x.T @ (np.outer(residual, residual) * weights) @ x @ bread * 80 / 78
        np.testing.assert_allclose(cov, expected, atol=1e-12)

    def test_built_panel_reconciles_and_all_sensitivities_are_reported(self):
        directory = ROOT / "output/rq1_daily/tables"
        if not directory.exists():
            self.skipTest("Daily pilot not built")
        city = pd.read_csv(directory / "city_day_linked_baseline.csv")
        area = pd.read_csv(ROOT / "data/processed/rq1/lor_day_recorded_watering_apr_sep_2020_2025.csv.gz")
        for column in ["events", "litres", "distinct_trees"]:
            np.testing.assert_allclose(area.groupby("date")[column].sum(), city.set_index("date")[column])
        self.assertEqual(area.groupby("date").size().unique().tolist(), [542])
        fits = pd.read_csv(directory / "model_coefficients.csv")
        self.assertEqual(len(fits), 216)
        self.assertTrue(np.isfinite(fits.coefficient_log1p).all())
        self.assertEqual(set(fits.hac_lag_days), {7, 14, 28})
        annual = pd.read_csv(directory / "annual_summary.csv")
        self.assertTrue((annual.distinct_trees < city.groupby(pd.to_datetime(city.date).dt.year).distinct_trees.sum().to_numpy()).all())


if __name__ == "__main__":
    unittest.main()
