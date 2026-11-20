import datetime as dt
import json
from pathlib import Path
import unittest

import pandas as pd

from analysis import rq3_crown_health_projection as crown

ROOT = Path(__file__).resolve().parents[1]


def logs(rows):
    """rows: (tree_id, date, litres)."""
    frame = pd.DataFrame(rows, columns=["tree_id", "date", "recorded_litres"])
    frame["year"] = [d.year for d in frame["date"]]
    frame["calendar_month"] = [d.month for d in frame["date"]]
    return frame


class ExposureTests(unittest.TestCase):
    def test_flight_dates_bound_the_exposure_window(self):
        cohort = pd.DataFrame({"pitid": ["before", "after", "late", "never"]})
        out = crown.exposure(cohort, logs([
            ("before", dt.date(2020, 8, 16), 50.0), ("before", dt.date(2021, 6, 1), 50.0),
            ("after", dt.date(2020, 8, 17), 50.0),
            ("late", dt.date(2025, 8, 11), 50.0),
        ])).set_index("pitid")
        self.assertEqual(out["watered"].to_dict(), {"before": False, "after": True, "late": False, "never": False})
        self.assertEqual(out["watered_before_baseline"].to_dict(), {"before": True, "after": False, "late": False, "never": False})
        self.assertEqual(out["never"].to_dict(), {"before": False, "after": False, "late": True, "never": True})

    def test_dose_counts_only_logs_between_the_flights(self):
        cohort = pd.DataFrame({"pitid": ["a", "b"]})
        out = crown.exposure(cohort, logs([
            ("a", dt.date(2022, 6, 1), 300.0), ("a", dt.date(2022, 6, 2), 300.0), ("a", dt.date(2022, 7, 1), 10.0),
            ("b", dt.date(2021, 6, 1), 20.0), ("b", dt.date(2023, 6, 1), 20.0),
        ])).set_index("pitid")
        self.assertEqual(out["three_days"].to_dict(), {"a": True, "b": False})
        self.assertEqual(out["high_dose"].to_dict(), {"a": True, "b": False})
        self.assertEqual(out["two_seasons"].to_dict(), {"a": False, "b": True})


class DetectabilityTests(unittest.TestCase):
    def test_more_watered_trees_lower_the_detectable_difference(self):
        def frame(n_watered):
            return pd.DataFrame({"watered": [i < n_watered for i in range(400)], "plr_id": [i % 10 for i in range(400)],
                                 "planting_year": 2010, "genus_group": "TILIA"})
        self.assertGreater(crown.standardised_mde(frame(20), "watered")[0], crown.standardised_mde(frame(80), "watered")[0])

    def test_saved_projection_holds_no_outcomes(self):
        saved = json.loads((ROOT / "output/rq3_crown_health/projection.json").read_text())
        for analysis in saved["analyses"].values():
            self.assertFalse({key for key in analysis if key.startswith(("ndvi", "difference", "ci95", "p_"))})
        self.assertGreater(saved["analyses"]["primary_watered_between_flights"]["treated"], 0)


if __name__ == "__main__":
    unittest.main()
