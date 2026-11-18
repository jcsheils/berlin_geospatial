import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import pandas as pd

from analysis import rq3_one_year_survival as rq3

ROOT = Path(__file__).resolve().parents[1]


def trees(rows):
    """rows: (district, planting_year, plr_id, watered, removed)."""
    frame = pd.DataFrame(rows, columns=["district", "planting_year", "plr_id", "watered", "removed"])
    frame["genus_group"] = "TILIA"
    return frame


class EstimatorTests(unittest.TestCase):
    def test_controls_are_weighted_to_the_treated_strata(self):
        # Stratum A: 1 watered (kept), 2 controls (1 removed). Stratum B: 3 watered (none removed), 1 control (removed).
        frame = trees([
            ("A", 2015, "p1", True, False), ("A", 2015, "p1", False, True), ("A", 2015, "p2", False, False),
            ("B", 2016, "p2", True, False), ("B", 2016, "p3", True, False), ("B", 2016, "p3", True, False),
            ("B", 2016, "p4", False, True),
        ])
        result = rq3.att(frame, "watered", "removed")
        self.assertEqual(result["treated"], 4)
        self.assertEqual(result["risk_treated_pct"], 0.0)
        self.assertEqual(result["risk_matched_control_pct"], 87.5)  # 1/4 * 0.5 + 3/4 * 1
        self.assertEqual(result["risk_difference_pp"], -87.5)
        low, high = result["ci95_pp"]
        self.assertLess(low, -87.5)
        self.assertGreater(high, -87.5)

    def test_strata_without_both_groups_drop_out(self):
        frame = trees([
            ("A", 2015, "p1", True, False), ("A", 2015, "p1", False, False),
            ("C", 2020, "p2", True, False),  # no control
            ("D", 2021, "p3", False, True),  # no watered tree
        ])
        result = rq3.att(frame, "watered", p0=0.015)
        self.assertEqual((result["treated"], result["treated_without_matching_control"], result["controls"]), (1, 1, 1))
        self.assertNotIn("risk_difference_pp", result)

    def test_more_watered_trees_lower_the_detectable_difference(self):
        small = trees([("A", 2015, f"p{i}", i < 2, False) for i in range(20)])
        large = trees([("A", 2015, f"p{i}", i < 8, False) for i in range(80)])
        self.assertGreater(rq3.att(small, "watered", p0=0.015)["mde_pp_design_effect_1_and_2"][0],
                           rq3.att(large, "watered", p0=0.015)["mde_pp_design_effect_1_and_2"][0])


class ExposureTests(unittest.TestCase):
    def test_only_april_to_september_logs_from_2020_to_2024_count(self):
        cohort = pd.DataFrame({"pitid": ["a", "b", "c", "d"]})
        logs = pd.DataFrame({
            "tree_id": ["a", "a", "b", "c"], "year": [2021, 2021, 2025, 2023],
            "calendar_month": [6, 7, 7, 10], "recorded_litres": [300.0, 250.0, 900.0, 900.0],
        })
        out = rq3.add_exposure(cohort, logs).set_index("pitid")
        self.assertEqual(out["watered"].to_dict(), {"a": True, "b": False, "c": False, "d": False})
        self.assertEqual(out["high_dose"].to_dict(), {"a": True, "b": False, "c": False, "d": False})

    def test_inventory_identifier_maps_to_log_identifier(self):
        ids = pd.Series(["strassenbaeume.00008100_0012abcd"])
        self.assertEqual(rq3.pitid(ids).tolist(), ["00008100:0012abcd"])


class CorrectionTests(unittest.TestCase):
    def test_raw_logs_are_deduplicated_windowed_and_positive(self):
        text = (
            "id;timestamp;bewaesserungsmenge_in_liter\n"
            "a;2021-06-01 10:00:00+00:00;50\n"
            "a;2021-06-01 10:00:00+00:00;50\n"  # exact duplicate
            "b;2020-05-17 10:00:00+00:00;50\n"  # before the platform window
            "c;2026-01-02 10:00:00+00:00;50\n"  # after the analysis window
            "d;2022-07-01 00:00:00+00:00;0\n"  # no volume
            "e;2024-09-30 22:30:00+00:00;80\n"  # 1 October in Berlin
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "logs.csv"
            path.write_text(text, encoding="utf-8")
            logs = rq3.load_raw_logs(path)
        self.assertEqual(logs["tree_id"].tolist(), ["a", "e"])
        self.assertEqual(logs["calendar_month"].tolist(), [6, 10])

    def test_bootstrap_interval_collapses_without_removals(self):
        frame = trees([("A", 2015, f"p{i}", i % 2 == 0, False) for i in range(40)])
        self.assertEqual(rq3.att(frame, "watered", "removed", bootstrap=200)["ci95_pp_cluster_bootstrap"], [0.0, 0.0])

    def test_corrected_run_reports_both_intervals(self):
        saved = json.loads((ROOT / "output/rq3_one_year_survival/corrected.json").read_text())
        primary = saved["analyses"]["primary_any_log_2020_2024_age_0_15"]
        self.assertIn("ci95_pp_cluster_bootstrap", primary)
        self.assertGreater(primary["removals_treated"], 0)
        self.assertGreaterEqual(*saved["watered_age_0_15_raw_export_vs_tree_day"])


class RegistrationTests(unittest.TestCase):
    def test_outcome_stage_refuses_an_unregistered_protocol(self):
        with mock.patch.object(rq3, "registered_hash", return_value="0" * 64), self.assertRaises(SystemExit):
            rq3.outcome(ROOT / "missing.gpkg")

    def test_registered_hash_matches_the_protocol(self):
        self.assertEqual(rq3.registered_hash(), rq3.sha256(rq3.PROTOCOL))

    def test_saved_design_holds_no_outcomes(self):
        design = json.loads((ROOT / "output/rq3_one_year_survival/design.json").read_text())
        for analysis in design["analyses"].values():
            self.assertFalse({key for key in analysis if key.startswith(("risk", "removals", "ci95", "p_"))})
        self.assertNotIn("inventory_2026", design["inputs_sha256"])


if __name__ == "__main__":
    unittest.main()
