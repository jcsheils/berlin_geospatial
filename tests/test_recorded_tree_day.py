import csv
import json
import math
from pathlib import Path
import unittest

from berlin_heat.recorded_tree_day import AGE_BAND_ORDER, assign_age_band


ROOT = Path(__file__).resolve().parents[1]
TEMPORAL = ROOT / "data/processed/temporal"
TREE_DAY = TEMPORAL / "recorded_tree_day_watering_2020_2025.csv"
AGE = TEMPORAL / "recorded_watering_timing_by_age_band_2021_2025.csv"
GENUS = TEMPORAL / "recorded_watering_timing_by_genus_2021_2025.csv"
METADATA = TEMPORAL / "recorded_tree_day_watering_2020_2025.metadata.json"
FIGURE = (
    ROOT
    / "output/03_spatial_equity_vulnerability/figures"
    / "02_recorded_watering_timing_by_tree_age_genus.png"
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RecordedTreeDayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = (TREE_DAY, AGE, GENUS, METADATA, FIGURE)
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise AssertionError(
                "Recorded-tree-day artifacts are missing; run "
                "pipelines/05_build_recorded_tree_day.py. Missing: "
                + ", ".join(missing)
            )
        cls.tree_days = read_rows(TREE_DAY)
        cls.age = read_rows(AGE)
        cls.genus = read_rows(GENUS)
        cls.metadata = json.loads(METADATA.read_text(encoding="utf-8"))

    def test_age_bands_have_no_gap_and_reject_implausible_values(self):
        cases = {
            None: "unknown",
            -1: "unknown",
            0: "0-9",
            9.999: "0-9",
            10: "10-19",
            19.999: "10-19",
            20: "20-39",
            39.999: "20-39",
            40: "40-59",
            59.999: "40-59",
            60: "60+",
            250: "60+",
            251: "unknown",
            math.nan: "unknown",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(assign_age_band(value), expected)

    def test_tree_day_keys_and_exposure_totals_match_foundation(self):
        self.assertEqual(len(self.tree_days), 50259)
        keys = {(row["tree_id"], row["local_date"]) for row in self.tree_days}
        self.assertEqual(len(keys), len(self.tree_days))
        self.assertEqual(
            sum(int(row["recorded_watering_events"]) for row in self.tree_days),
            57786,
        )
        self.assertTrue(
            all(
                row["recorded_events_tree_day"]
                == row["recorded_watering_events"]
                and row["recorded_litres_tree_day"] == row["recorded_litres"]
                for row in self.tree_days
            )
        )
        self.assertAlmostEqual(
            sum(float(row["recorded_litres"]) for row in self.tree_days),
            2249502.0,
            places=6,
        )
        self.assertEqual(len({row["tree_id"] for row in self.tree_days}), 11127)
        self.assertEqual(
            sum(row["multiple_logs_tree_day"] == "True" for row in self.tree_days),
            5392,
        )
        dates = [row["local_date"] for row in self.tree_days]
        self.assertEqual(min(dates), "2020-05-18")
        self.assertEqual(max(dates), "2025-12-22")

    def test_complete_year_profiles_are_balanced(self):
        self.assertEqual(len(self.age), len(AGE_BAND_ORDER) * 12)
        age_counts = {
            age_band: sum(row["age_band"] == age_band for row in self.age)
            for age_band in AGE_BAND_ORDER
        }
        self.assertEqual(set(age_counts.values()), {12})
        self.assertEqual(
            {row["observed_complete_years"] for row in self.age}, {"5"}
        )

        genera = {row["genus"] for row in self.genus}
        self.assertEqual(len(self.genus), len(genera) * 12)
        self.assertTrue(genera)
        self.assertEqual(
            {row["observed_complete_years"] for row in self.genus}, {"5"}
        )

        for group_field, rows in (("age_band", self.age), ("genus", self.genus)):
            groups = {row[group_field] for row in rows}
            for group in groups:
                with self.subTest(group_field=group_field, group=group):
                    share = sum(
                        float(row["within_group_recorded_watering_day_share"])
                        for row in rows
                        if row[group_field] == group
                    )
                    self.assertAlmostEqual(share, 1.0, places=10)

    def test_metadata_preserves_timestamp_and_claim_limits(self):
        audit = self.metadata["audit"]
        self.assertEqual(audit["tree_day_rows"], 50259)
        self.assertEqual(audit["tree_days_with_multiple_source_events"], 5392)
        precision = {
            row["year"]: row for row in audit["timestamp_precision_by_local_year"]
        }
        self.assertEqual(precision[2025]["share_at_exact_utc_midnight"], 1.0)
        self.assertIn("municipal", self.metadata["semantics"]["recorded_zero"])
        self.assertIn("do not estimate", self.metadata["semantics"]["claim_boundary"])
        self.assertGreater(FIGURE.stat().st_size, 50_000)


if __name__ == "__main__":
    unittest.main()
