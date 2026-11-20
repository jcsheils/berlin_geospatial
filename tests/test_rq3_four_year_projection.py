import json
from pathlib import Path
import unittest

import pandas as pd

from analysis import rq3_four_year_projection as rq3

ROOT = Path(__file__).resolve().parents[1]


class ExposureTests(unittest.TestCase):
    def test_only_seasons_before_the_landmark_count(self):
        cohort = pd.DataFrame({"pitid": ["a", "b", "c", "d"]})
        seasons = pd.DataFrame({
            "tree_id": ["a", "a", "b", "c"], "year": [2020, 2022, 2023, 2021],
            "days": [1, 3, 5, 2], "litres": [100.0, 600.0, 900.0, 80.0],
        })
        out = rq3.landmark_exposure(cohort, seasons, 2023).set_index("pitid")
        self.assertEqual(out["watered"].to_dict(), {"a": True, "b": False, "c": True, "d": False})
        self.assertEqual(out["last_season"].to_dict(), {"a": True, "b": False, "c": False, "d": False})
        self.assertEqual(out["three_days"].to_dict(), {"a": True, "b": False, "c": False, "d": False})
        self.assertEqual(out["two_seasons"].to_dict(), {"a": True, "b": False, "c": False, "d": False})
        self.assertEqual(out["high_dose"].to_dict(), {"a": True, "b": False, "c": False, "d": False})

    def test_season_table_counts_distinct_days_in_april_to_september(self):
        logs = pd.DataFrame({
            "tree_id": ["a", "a", "a", "a"], "year": [2021] * 4, "calendar_month": [5, 5, 6, 10],
            "date": pd.to_datetime(["2021-05-01", "2021-05-01", "2021-06-02", "2021-10-01"]).date,
            "recorded_litres": [50.0, 30.0, 20.0, 999.0],
        })
        row = rq3.season_table(logs).iloc[0]
        self.assertEqual((row["days"], row["litres"]), (2, 100.0))


class PlanTests(unittest.TestCase):
    def test_smallest_effect_is_half_a_point_a_year(self):
        self.assertAlmostEqual(rq3.smallest_effect(), 0.005)

    def test_power_rises_with_precision(self):
        self.assertLess(rq3.power(0.004, 0.005, 1.96), rq3.power(0.002, 0.005, 1.96))

    def test_saved_projection_holds_no_outcomes(self):
        saved = json.loads((ROOT / "output/rq3_four_year_survival/projection.json").read_text())
        for analysis in saved["analyses"].values():
            self.assertFalse({key for key in analysis if key.startswith(("risk", "removals", "ci95", "p_"))})
        self.assertGreater(saved["analyses"]["primary_any_earlier_log_district"]["treated"], 0)


if __name__ == "__main__":
    unittest.main()
