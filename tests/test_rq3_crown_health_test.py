import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from analysis import rq3_crown_health_extract as extract
from analysis import rq3_crown_health_test as stages

EFFECT = 0.05  # true gain of watered young crowns, 2020 to 2025
AGE_SLOPE = 0.02  # NDVI gained per year of age in 2020


def synthetic_world(seed: int = 7):
    """Trees, logs and circle tables for 40 planning areas; watering adds EFFECT to the 2020-2025 change."""
    rng = np.random.default_rng(seed)
    rows = []
    for area in range(40):
        for i in range(80):
            young = i < 60
            planting = int(rng.integers(2005, 2020)) if young else int(rng.integers(1985, 2005))
            rows.append({"tree_id": f"strassenbaeume.{area:03d}_{i:03d}", "planting_year": planting,
                         "genus_group": "TILIA" if i % 2 else "ACER", "plr_id": f"P{area:03d}", "area_effect": rng.normal(0, 0.05)})
    trees = pd.DataFrame(rows)
    trees["pitid"] = trees["tree_id"].str.removeprefix("strassenbaeume.")
    trees["bzr_id"] = "B1"
    draw = rng.random(len(trees))
    watered = draw < 0.2
    early = (draw >= 0.2) & (draw < 0.25)
    logs = [(t, dt.date(2022, 6, 1), 40.0) for t in trees.loc[watered, "pitid"]]
    heavy = trees.loc[watered, "pitid"].iloc[::3]  # three log days, 600 L and a second season
    logs += [(t, dt.date(2022, 6, day), 200.0) for t in heavy for day in (2, 3)]
    logs += [(t, dt.date(2024, 7, 1), 40.0) for t in heavy]
    logs += [(t, dt.date(2020, 6, 1), 40.0) for t in trees.loc[early, "pitid"]]
    logs = pd.DataFrame(logs, columns=["tree_id", "date", "recorded_litres"])
    logs["year"] = [d.year for d in logs["date"]]
    logs["calendar_month"] = [d.month for d in logs["date"]]
    age = 2020 - trees["planting_year"]
    level_2020 = 0.3 + AGE_SLOPE * age.clip(upper=15) + trees["area_effect"] + rng.normal(0, 0.03, len(trees))
    gain = np.where(watered & (age <= 15), EFFECT, 0.0)
    ndvi = {"2015": level_2020 - 0.1 + rng.normal(0, 0.03, len(trees)),
            "2020": level_2020,
            "2025": level_2020 + 0.1 + gain + rng.normal(0, 0.03, len(trees))}
    gcc = {"2020rgb": 0.4 + rng.normal(0, 0.01, len(trees)), "2023": 0.41 + rng.normal(0, 0.01, len(trees))}
    return trees.drop(columns="area_effect"), logs, ndvi, gcc


def write_tables(folder: Path, trees: pd.DataFrame, ndvi: dict, gcc: dict) -> None:
    for flight, values in {**ndvi, **gcc}.items():
        index = extract.FLIGHTS[flight]["index"]
        table = pd.DataFrame({"tree_id": trees["tree_id"], "window": "w"})
        for radius, pixels in (("1m", 81), ("2m", 317), ("3m", 709)):
            table[f"pixels_{radius}"] = pixels
            table[f"in_image_{radius}"] = pixels
            table[f"{index}_{radius}"] = values
        table.to_csv(folder / f"crown_circles_{flight}.csv.gz", index=False)
        pd.DataFrame({"window": ["w"], "sha256": ["0" * 64], "bytes": [1], "error": [""]}).to_csv(folder / f"crown_windows_{flight}.csv.gz", index=False)
    for flight in stages.INFRARED:
        (folder / f"{flight}_crosscheck.json").write_text(json.dumps({"passes": True, "red_median_abs_diff": 0.0, "green_median_abs_diff": 0.0}))
    pd.DataFrame({"chip": [f"{i:03d}.png" for i in range(200)], "tree_id": "x", "on_tree": "yes"}).to_csv(folder / "eye_check.csv", index=False)


class EstimatorTests(unittest.TestCase):
    def test_fixed_effects_fit_recovers_the_effect(self):
        rng = np.random.default_rng(3)
        n = 4000
        a, b = rng.integers(0, 50, n), rng.integers(0, 12, n)
        t = rng.random(n) < 0.1 + 0.3 * (a % 3 == 0)
        y = rng.normal(0, 1, 50)[a] + rng.normal(0, 1, 12)[b] + 0.4 * t + rng.normal(0, 0.1, n)
        beta, residual, rx = stages.fe_fit(y, t[:, None].astype(float), [a, b])
        self.assertAlmostEqual(beta[0], 0.4, delta=0.02)
        self.assertLess(stages.cluster_se(rx, residual, a), 0.05)

    def test_exact_matching_by_hand(self):
        y = np.array([1.0, 3.0, 2.0, 10.0, 0.0, 5.0])
        t = np.array([True, False, False, True, False, True])
        stratum = np.array([0, 0, 0, 1, 1, 2])  # stratum 2 has no control and drops out
        self.assertAlmostEqual(stages.exact_att(y, t, stratum), ((1 - 2.5) + (10 - 0)) / 2)

    def test_interpretation_table(self):
        self.assertEqual(stages.interpret([0.01, 0.03], 0.028, 0.05), "Watered crowns became greener, by less than Δ")
        self.assertEqual(stages.interpret([0.01, 0.09], 0.08, 0.05), "Watered crowns became greener; whether by Δ or more stays open")
        self.assertEqual(stages.interpret([-0.01, 0.03], 0.02, 0.05), "No gain detected; a gain of Δ or more is ruled out")
        self.assertEqual(stages.interpret([-0.01, 0.09], 0.08, 0.05), "Inconclusive; report the largest gain the interval does not exclude")
        self.assertTrue(stages.interpret([-0.09, -0.01], -0.02, 0.05).startswith("Watered crowns lost greenness"))

    def test_selection_rule_follows_the_primary_direction(self):
        self.assertTrue(stages.same_direction([0.01, 0.04], 0.03))
        self.assertFalse(stages.same_direction([0.01, 0.04], -0.03))
        self.assertFalse(stages.same_direction([-0.01, 0.04], 0.03))
        self.assertTrue(stages.same_direction([-0.04, -0.01], -0.03))


class StageTests(unittest.TestCase):
    def setUp(self):
        self.trees, self.logs, ndvi, gcc = synthetic_world()
        self.folder = tempfile.TemporaryDirectory()
        self.data = Path(self.folder.name) / "data"
        self.out = Path(self.folder.name) / "out"
        self.data.mkdir()
        write_tables(self.data, self.trees, ndvi, gcc)
        self.patches = [mock.patch.object(extract, "require_freeze"),
                        mock.patch.object(stages.four_year, "load_trees", return_value=self.trees),
                        mock.patch.object(stages.one_year, "load_raw_logs", return_value=self.logs)]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.folder.cleanup()

    def test_all_three_stages(self):
        checked = stages.check(self.data, self.out)
        self.assertTrue(checked["passes"], checked["checks"])
        planned = stages.design(self.data, self.out)
        self.assertAlmostEqual(planned["smallest_effect"]["delta"], AGE_SLOPE / 2, delta=0.002)
        self.assertGreater(planned["analyses"]["primary"]["treated"], 300)
        for analysis in planned["analyses"].values():  # the design stage holds no comparison by watering
            self.assertFalse({k for k in analysis if k == "difference" or k.startswith("ci")})
        result = stages.outcome(self.data, self.out, reps=200)
        primary = result["primary"]
        self.assertLess(primary["ci95_bootstrap"][0], EFFECT)
        self.assertGreater(primary["ci95_bootstrap"][1], EFFECT)
        self.assertTrue(primary["test_a_gain"])
        self.assertAlmostEqual(result["secondary"]["older_16_40"]["difference"], 0.0, delta=0.02)
        self.assertAlmostEqual(result["secondary"]["placebo_2015_2020"]["difference"], 0.0, delta=0.02)
        self.assertAlmostEqual(result["secondary"]["s5_exact_matching"]["difference"], EFFECT, delta=0.02)
        self.assertEqual(result["s8_without_survivor_selection"][:6], "awaits")

    def test_eye_check_failure_stops_the_design(self):
        eye = pd.read_csv(self.data / "eye_check.csv")
        eye.loc[:30, "on_tree"] = "no"
        eye.to_csv(self.data / "eye_check.csv", index=False)
        self.assertFalse(stages.check(self.data, self.out)["passes"])
        with self.assertRaises(SystemExit):
            stages.design(self.data, self.out)

    def test_outcome_refuses_a_sample_that_differs_from_the_design(self):
        stages.check(self.data, self.out)
        stages.design(self.data, self.out)
        planned = json.loads((self.out / "design.json").read_text())
        planned["analyses"]["primary"]["treated"] += 1
        (self.out / "design.json").write_text(json.dumps(planned))
        with self.assertRaises(SystemExit):
            stages.outcome(self.data, self.out, reps=20)


if __name__ == "__main__":
    unittest.main()
