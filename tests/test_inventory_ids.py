import hashlib
import json
from pathlib import Path
import unittest

import pandas as pd

from analysis import build_feedback_benchmarks as benchmarks
from tools import extract_tree_inventory_2025 as extract


ROOT = Path(__file__).resolve().parents[1]
HEADER = "occurrenceID\tmunicipality\tgenus\tverbatimLatitude\tverbatimLongitude\tdynamicProperties\n"


def frame(rows):
    return pd.DataFrame(rows, columns=["tree_id", "genus", "planting_year", "x", "y"])


class ArchiveExtractTests(unittest.TestCase):
    def test_one_sorted_row_per_tree_and_none_is_missing(self):
        lines = [
            HEADER,
            'strassenbaeume.b\tMitte\tTILIA\t5820000.126\t390000.5\t{"age":None, "height":None, "planting year":2015}\n',
            "strassenbaeume.b.planted\tMitte\tTILIA\t5820000.126\t390000.5\t\n",
            'anlagenbaeume.a\tPankow\tACER\t5820001\t390001\t{"age":None, "planting year":None}\n',
        ]
        self.assertEqual(extract.tree_rows(lines), [
            ["anlagenbaeume.a", "Pankow", "ACER", "", "390001.00", "5820001.00"],
            ["strassenbaeume.b", "Mitte", "TILIA", "2015", "390000.50", "5820000.13"],
        ])

    def test_frozen_extract_matches_its_snapshot(self):
        snapshot = json.loads((ROOT / "data/raw/tree_inventory/snapshot_2025.json").read_text())
        with (ROOT / snapshot["file"]).open("rb") as handle:
            self.assertEqual(hashlib.file_digest(handle, "sha256").hexdigest(), snapshot["file_sha256"])
        self.assertEqual(snapshot["rows"], snapshot["street_trees"] + snapshot["green_space_trees"])


class IdentifierComparisonTests(unittest.TestCase):
    def test_separates_removed_rekeyed_and_replanted_trees(self):
        before = frame([
            ["kept", "TILIA", 2012, 0.0, 0.0],
            ["rekeyed", "ACER", 2010, 10.0, 0.0],
            ["replanted", "ACER", 2011, 20.0, 0.0],
            ["removed", "ACER", 2013, 30.0, 0.0],
        ])
        after = frame([
            ["kept", "Tilia", 2012, 0.0, 0.0],
            ["new-1", "Acer", 2010, 10.3, 0.0],
            ["new-2", "Quercus", 2025, 20.2, 0.0],
            ["new-3", "Acer", 2013, 45.0, 0.0],
        ])
        result = benchmarks.compare_identifiers(before, after).set_index("tree_id")
        self.assertEqual(result["gone"].to_dict(), {"kept": False, "rekeyed": True, "replanted": True, "removed": True})
        self.assertEqual(result.index[result["rekeyed"]].tolist(), ["rekeyed"])
        self.assertEqual(result.index[result["replanted"]].tolist(), ["replanted"])

    def test_nothing_gone_leaves_flags_false(self):
        trees = frame([["kept", "TILIA", 2012, 0.0, 0.0]])
        result = benchmarks.compare_identifiers(trees, trees)
        self.assertFalse(result[["gone", "rekeyed", "replanted"]].to_numpy().any())


class DetectabilityTests(unittest.TestCase):
    def test_smaller_effects_and_rarer_removals_need_more_trees(self):
        self.assertGreater(benchmarks.treated_needed(0.015, 0.25), benchmarks.treated_needed(0.015, 0.5))
        self.assertGreater(benchmarks.treated_needed(0.015, 0.5), benchmarks.treated_needed(0.05, 0.5))

    def test_saved_benchmarks_never_split_removals_by_watering(self):
        saved = json.loads((ROOT / "output/feedback_benchmarks/benchmarks.json").read_text())
        section = saved["design_feasibility"]["inventory_ids_2025_to_2026"]
        self.assertEqual(section["trees_2025"], 927914)
        self.assertEqual(set(section["one_year_survival_2025_season"]), {
            "young_street_trees_with_logged_watering", "expected_removals_at_overall_rate",
            "mde_pp_design_effect_1_and_2", "treated_trees_needed_to_detect_halving"})


if __name__ == "__main__":
    unittest.main()
