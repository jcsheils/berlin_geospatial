from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from berlin_heat.ortsteil_lst import audit_source, exact_calendar_join, residualise_two_way

ROOT = Path(__file__).resolve().parents[1]


class OrtsteilLSTTests(unittest.TestCase):
    def test_duplicate_outcomes_are_quarantined_not_averaged(self):
        raw = pd.DataFrame({"ortsteil": ["Buckow", "Buckow", "Mitte", "Zehlendorf"],
                            "bezirk": ["Neukölln", "Neukölln", "Mitte", "Steglitz-Zehlendorf"],
                            "year": [2022] * 4, "month": [6] * 4,
                            "LST_C_mean": [30, 32, 29, 28], "LST_C_count": [100, 300, 100, 100],
                            "rain_mm_mean": [20] * 4})
        audit, usable, meta = audit_source(raw)
        self.assertEqual(len(audit), 4)
        self.assertEqual(usable.ortsteil.tolist(), ["Mitte"])
        self.assertEqual(meta["duplicate_key_rows"], 2)
        self.assertEqual(meta["duplicate_keys"], 1)

    def test_exact_month_join_does_not_skip_missing_outcome(self):
        panel = pd.DataFrame({"ortsteil": ["Mitte"] * 3, "district": ["Mitte"] * 3,
                              "month_date": pd.to_datetime(["2021-12-01", "2022-01-01", "2022-02-01"])})
        outcome = pd.DataFrame({"ortsteil": ["Mitte"] * 3, "district": ["Mitte"] * 3,
                                "month_date": pd.to_datetime(["2021-12-01", "2022-02-01", "2022-03-01"]),
                                "lst_c": [10, 12, 13], "source_lst_count": [10] * 3,
                                "relative_source_count": [1] * 3,
                                "source_rain_mm_mean_unverified": [20] * 3})
        joined = exact_calendar_join(panel, outcome)
        self.assertTrue(pd.isna(joined.loc[0, "next_month_lst_c"]))
        self.assertEqual(joined.loc[1, "previous_month_lst_c"], 10)
        self.assertEqual(joined.loc[1, "next_month_lst_c"], 12)
        self.assertTrue(pd.isna(joined.loc[2, "previous_month_lst_c"]))
        with self.assertRaises(ValueError):
            exact_calendar_join(panel, pd.concat([outcome, outcome.iloc[:1]]))

    def test_unbalanced_residualisation_matches_dummy_projection(self):
        area = np.array(["a", "a", "a", "b", "b", "c", "c", "c"])
        date = np.array([1, 2, 4, 1, 3, 2, 3, 4])
        values = np.random.default_rng(18).normal(size=(8, 2))
        x = pd.get_dummies(pd.DataFrame({"area": area, "date": date.astype(str)}), dtype=float)
        expected = values - x.to_numpy() @ np.linalg.lstsq(x, values, rcond=None)[0]
        actual = residualise_two_way(values, area, date)
        np.testing.assert_allclose(actual, expected, atol=1e-9)

    def test_saved_panel_reconciles_and_excludes_ambiguous_outcomes(self):
        path = ROOT / "output/watering_response/ortsteil/tables/ortsteil_month_watering_lst_2020_2025.csv"
        if not path.exists():
            self.skipTest("Run the Ortsteil pipeline before checking outputs")
        panel = pd.read_csv(path)
        self.assertEqual(len(panel), 97 * 68)
        self.assertFalse(panel.duplicated(["ortsteil", "month_date"]).any())
        self.assertEqual(int(panel.recorded_watering_events.sum()), 57786)
        self.assertAlmostEqual(panel.recorded_litres.sum(), 2249502)
        self.assertTrue(panel.loc[~panel.comparison_eligible, "lst_c"].isna().all())
        self.assertEqual(panel.loc[panel.comparison_eligible, "ortsteil"].nunique(), 93)
        days = pd.read_csv(ROOT / "data/processed/temporal/recorded_tree_day_watering_2020_2025.csv")
        days["month_date"] = pd.to_datetime(days.local_date).dt.to_period("M").astype(str)
        expected = days.groupby("month_date").tree_id.nunique()
        actual = panel.assign(month_date=panel.month_date.str[:7]).groupby("month_date").recorded_watered_trees.sum()
        expected = expected.reindex(actual.index, fill_value=0)
        pd.testing.assert_series_equal(actual, expected, check_names=False)


if __name__ == "__main__":
    unittest.main()
