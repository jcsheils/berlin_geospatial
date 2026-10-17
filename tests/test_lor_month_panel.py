import csv
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "data/processed/foundation"
PANEL = FOUNDATION / "lor_month_recorded_watering_2020_2025.csv"
CROSSWALK = FOUNDATION / "recorded_tree_lor_crosswalk_2020_2025.csv"
METADATA = FOUNDATION / "lor_month_recorded_watering_2020_2025.metadata.json"


class LorMonthPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PANEL.is_file() or not CROSSWALK.is_file() or not METADATA.is_file():
            raise AssertionError(
                "Foundation artifacts are missing; run "
                "pipelines/03_build_lor_month_panel.py first."
            )
        with PANEL.open("r", encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        with CROSSWALK.open("r", encoding="utf-8", newline="") as handle:
            cls.crosswalk = list(csv.DictReader(handle))
        cls.metadata = json.loads(METADATA.read_text(encoding="utf-8"))

    def test_panel_is_balanced(self):
        self.assertEqual(len(self.rows), 542 * 68)
        months = sorted({row["month"] for row in self.rows})
        self.assertEqual(len(months), 68)
        self.assertEqual(months[0], "2020-05-01")
        self.assertEqual(months[-1], "2025-12-01")
        for month in months:
            with self.subTest(month=month):
                self.assertEqual(
                    sum(row["month"] == month for row in self.rows),
                    542,
                )

    def test_panel_matches_current_spatial_totals(self):
        events = sum(int(row["recorded_watering_events"]) for row in self.rows)
        litres = sum(float(row["recorded_litres"]) for row in self.rows)
        self.assertEqual(events, 57786)
        self.assertAlmostEqual(litres, 2249502.0, places=6)
        first_month = [
            row for row in self.rows if row["month"] == "2020-05-01"
        ]
        self.assertEqual(
            sum(int(row["current_inventory_trees"]) for row in first_month),
            955434,
        )
        self.assertEqual(
            self.metadata["audit"]["deduplicated_events_in_window"],
            58474,
        )

    def test_crosswalk_is_unique_and_matches_complete_window(self):
        tree_ids = [row["tree_id"] for row in self.crosswalk]
        self.assertEqual(len(tree_ids), 11127)
        self.assertEqual(len(set(tree_ids)), 11127)
        self.assertTrue(all(row["plr_id"] for row in self.crosswalk))

    def test_partial_start_and_zero_semantics_are_explicit(self):
        may = [row for row in self.rows if row["month"] == "2020-05-01"]
        self.assertEqual({row["platform_live_days"] for row in may}, {"14"})
        self.assertEqual(
            {row["platform_month_status"] for row in may},
            {"partial_platform_start"},
        )
        semantics = self.metadata["semantics"]
        self.assertIn("municipal", semantics["recorded_zero"])
        self.assertIn("current tree inventory", semantics["denominator_caveat"])
        self.assertIn("does not estimate", semantics["claim_boundary"])

    def test_new_exposure_fields_use_recorded_terminology(self):
        fields = set(self.rows[0])
        exposure_fields = {
            field
            for field in fields
            if field.endswith("events")
            or field.endswith("litres")
            or "watered_trees" in field
            or "reach" in field
        }
        self.assertTrue(exposure_fields)
        self.assertTrue(all(field.startswith("recorded_") for field in exposure_fields))


if __name__ == "__main__":
    unittest.main()
