"""Checks for temporal leakage, missing rainfall and non-additive tree counts."""
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from berlin_heat.watering_response import aggregate_monthly, calendar_hac_ols, read_weather

ROOT = Path(__file__).resolve().parents[1]


class WateringResponseTests(unittest.TestCase):
    def test_hac_respects_calendar_gaps(self):
        rng = np.random.default_rng(33)
        x = np.column_stack([np.ones(20), rng.normal(size=20)])
        y = x @ [1.3, 0.8] + rng.normal(size=20)
        time = np.r_[np.arange(10), np.arange(22, 32)]
        beta, covariance = calendar_hac_ols(x, y, time)
        residual = y - x @ beta
        # Independent pairwise sandwich reference with actual-date weights.
        distance = np.abs(time[:, None] - time[None, :])
        weights = np.maximum(0, 1 - distance / 4)
        error_cov = np.outer(residual, residual) * weights
        bread = np.linalg.inv(x.T @ x)
        expected = bread @ x.T @ error_cov @ x @ bread * 20 / 18
        np.testing.assert_allclose(covariance, expected, atol=1e-12)
        collapsed = calendar_hac_ols(x, y, np.arange(20))[1]
        self.assertFalse(np.allclose(covariance, collapsed))

    def test_exact_linear_model_and_invalid_dates(self):
        x = np.column_stack([np.ones(8), np.arange(8)])
        beta, covariance = calendar_hac_ols(x, 3 + 2 * np.arange(8), np.arange(8))
        np.testing.assert_allclose(beta, [3, 2], atol=1e-10)
        np.testing.assert_allclose(covariance, 0, atol=1e-20)
        with self.assertRaises(ValueError):
            calendar_hac_ols(x, np.arange(8), np.zeros(8))

    def test_distinct_trees_are_not_events(self):
        month = pd.Timestamp("2021-06-01")
        foundation = pd.DataFrame({
            "month": [month], "district": ["Example"], "current_inventory_trees": [20],
            "recorded_watering_events": [3], "recorded_litres": [90],
            "recorded_watered_trees": [2], "platform_month_status": ["complete"],
            "platform_live_days": [30],
        })
        days = pd.DataFrame({"month": [month] * 3, "district": ["Example"] * 3,
                             "tree_id": ["a", "a", "b"]})
        row = aggregate_monthly(foundation, days, "district").iloc[0]
        self.assertEqual(row.recorded_watered_trees, 2)
        self.assertEqual(row.recorded_reach_pct_current_inventory, 10)
        foundation.loc[0, "recorded_watered_trees"] = 3
        with self.assertRaises(ValueError):
            aggregate_monthly(foundation, days, "district")

    def test_missing_rain_and_previous_month_alignment(self):
        path = ROOT / "data/raw/dwd/tageswerte_KL_00433_19480101_20251231_hist.zip"
        if not path.exists():
            self.skipTest("DWD archive not downloaded")
        daily, monthly, audit = read_weather(path)
        self.assertEqual(audit["missing_rainfall_days"], 10)
        june = monthly[monthly.month.eq("2023-06-01")].iloc[0]
        july = monthly[monthly.month.eq("2023-07-01")].iloc[0]
        self.assertTrue(pd.isna(june.rainfall_mm))
        self.assertTrue(pd.isna(july.previous_month_rainfall_mm))
        self.assertFalse(pd.isna(july.rainfall_mm))
        self.assertFalse(daily.rainfall_mm.eq(-999).any())
        self.assertEqual(monthly.month.nunique(), 72)


if __name__ == "__main__":
    unittest.main()
