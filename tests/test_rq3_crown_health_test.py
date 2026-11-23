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

EFFECT = 0.05  # true gain in crown greenness at sustained care, 2020 to 2025; linear in the level of care
AGE_SLOPE = 0.02  # greenness gained per year of age in 2020


def synthetic_world(seed: int = 7):
    """Trees, logs and image tables for 40 planning areas; care adds EFFECT * level / 3 to the 2020-2025 change."""
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
    level = np.select([draw < 0.08, draw < 0.15, draw < 0.20], [1, 2, 3], 0)
    early = (draw >= 0.20) & (draw < 0.25)
    pit = trees["pitid"]
    logs = [(t, dt.date(2022, 6, 1), 40.0) for t in pit[level >= 1]]
    logs += [(t, dt.date(2022, 6, day), 200.0) for t in pit[level == 2] for day in (2, 3)]  # three log days, 440 L
    logs += [(t, dt.date(year, 7, 1), 40.0) for t in pit[level == 3] for year in (2021, 2024)]  # three seasons
    logs += [(t, dt.date(2020, 6, 1), 40.0) for t in pit[early]]
    logs = pd.DataFrame(logs, columns=["tree_id", "date", "recorded_litres"])
    logs["year"] = [d.year for d in logs["date"]]
    logs["calendar_month"] = [d.month for d in logs["date"]]
    age = 2020 - trees["planting_year"]
    n = len(trees)
    level_2020 = 0.3 + AGE_SLOPE * age.clip(upper=15) + trees["area_effect"] + rng.normal(0, 0.03, n)
    gain = np.where(age <= 15, EFFECT * level / 3, 0.0)
    green = {"2015": level_2020 - 0.1 + rng.normal(0, 0.03, n), "2020": level_2020,
             "2025": level_2020 + 0.1 + gain + rng.normal(0, 0.03, n)}
    gcc = {"2020rgb": 0.4 + rng.normal(0, 0.01, n), "2023": 0.41 + rng.normal(0, 0.01, n)}
    change = green["2025"] - green["2020"]
    removed = pd.Series((change < np.quantile(change, 0.04)).to_numpy(), index=trees["tree_id"].to_numpy())  # falling greenness goes with removal
    return trees.drop(columns="area_effect"), logs, green, gcc, removed


def write_tables(folder: Path, trees: pd.DataFrame, green: dict, gcc: dict) -> None:
    rng = np.random.default_rng(11)
    windows = "w" + (trees.index // 40).astype(str)
    for flight, values in {**green, **gcc}.items():
        index = extract.FLIGHTS[flight]["index"]
        table = pd.DataFrame({"tree_id": trees["tree_id"], "window": windows})
        for region, pixels in (("1m", 81), ("2m", 317), ("3m", 709), ("ring", 1256)):
            table[f"pixels_{region}"] = pixels
            table[f"in_image_{region}"] = pixels
            table[f"shadow_frac_{region}"] = 0.1
            if index == "ndvi":
                table[f"veg_ndvi_{region}"] = values if region != "ring" else 0.5 + rng.normal(0, 0.02, len(trees))
                table[f"veg_frac_{region}"] = 0.6 + rng.normal(0, 0.02, len(trees))
                table[f"ndvi_{region}"] = 0.6 * values
            else:
                table[f"gcc_{region}"] = values
        table.to_csv(folder / f"crown_circles_{flight}.csv.gz", index=False)
        log = pd.DataFrame({"window": sorted(set(windows)), "sha256": "0" * 64, "bytes": 1, "error": ""})
        log["stable_ndvi"] = rng.normal(0.02, 0.01, len(log)) if index == "ndvi" else np.nan
        log.to_csv(folder / f"crown_windows_{flight}.csv.gz", index=False)
        vegetation = 0.25 if index == "ndvi" else None
        (folder / f"crown_circles_{flight}.json").write_text(json.dumps({"thresholds": {"vegetation": vegetation, "shadow": 40.0}}))
    for flight in stages.INFRARED:
        (folder / f"{flight}_crosscheck.json").write_text(json.dumps({"passes": True, "red_median_abs_diff": 0.0, "green_median_abs_diff": 0.0}))
    pd.DataFrame({"chip": [f"{i:03d}.png" for i in range(200)], "tree_id": "x", "on_tree": "yes"}).to_csv(folder / "eye_check.csv", index=False)


def write_one_year(path: Path) -> None:
    path.write_text(json.dumps({"analyses": {"primary_any_log_2020_2024_age_0_15": {"risk_treated_pct": 1.02, "risk_matched_control_pct": 1.23}}}))


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
        self.assertEqual(stages.interpret([0.01, 0.03], 0.028, 0.05), "More care went with greener crowns, by less than Δ at sustained care")
        self.assertEqual(stages.interpret([0.01, 0.09], 0.08, 0.05), "More care went with greener crowns; whether by Δ or more at sustained care stays open")
        self.assertEqual(stages.interpret([-0.01, 0.03], 0.02, 0.05), "No gain detected; a gain of Δ or more at sustained care is ruled out")
        self.assertEqual(stages.interpret([-0.01, 0.09], 0.08, 0.05), "Inconclusive; report the largest gain the interval does not exclude")
        self.assertTrue(stages.interpret([-0.09, -0.01], -0.02, 0.05).startswith("More care went with less green crowns"))

    def test_selection_rule_follows_the_primary_direction(self):
        self.assertTrue(stages.same_direction([0.01, 0.04], 0.03))
        self.assertFalse(stages.same_direction([0.01, 0.04], -0.03))
        self.assertFalse(stages.same_direction([-0.01, 0.04], 0.03))
        self.assertTrue(stages.same_direction([-0.04, -0.01], -0.03))

    def test_auc(self):
        self.assertAlmostEqual(stages.auc(np.array([3.0, 2.0, 1.0, 0.0]), np.array([True, True, False, False])), 1.0)
        self.assertAlmostEqual(stages.auc(np.array([1.0, 1.0, 1.0, 1.0]), np.array([True, False, True, False])), 0.5)


class StageTests(unittest.TestCase):
    def setUp(self):
        self.trees, self.logs, green, gcc, self.removed = synthetic_world()
        self.folder = tempfile.TemporaryDirectory()
        root = Path(self.folder.name)
        self.data, self.out = root / "data", root / "out"
        self.data.mkdir()
        self.one_year = root / "corrected.json"
        write_one_year(self.one_year)
        write_tables(self.data, self.trees, green, gcc)
        self.patches = [mock.patch.object(extract, "require_freeze"),
                        mock.patch.object(stages.four_year, "load_trees", return_value=self.trees),
                        mock.patch.object(stages.one_year, "load_raw_logs", return_value=self.logs)]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.folder.cleanup()

    def removed_of(self, ids):
        return ids.map(self.removed).to_numpy(bool)

    def test_all_three_stages(self):
        checked = stages.check(self.data, self.out)
        self.assertTrue(checked["passes"], checked["checks"])
        self.assertEqual(set(checked["flight_consistency"]), {"2015_2020", "2020_2025"})
        planned = stages.design(self.data, self.out, removed_of=self.removed_of)
        self.assertTrue(planned["validity"]["passes"], planned["validity"])
        self.assertAlmostEqual(planned["smallest_effect"]["delta"], AGE_SLOPE / 2, delta=0.002)
        levels = planned["analyses"]["primary"]["by_level"]
        self.assertTrue(all(levels[name] > 100 for name in stages.LEVELS), levels)
        self.assertIsNotNone(planned["noise_floor_residual_sd_never_watered_16_40"])
        for analysis in planned["analyses"].values():  # the design stage holds no comparison by watering
            self.assertFalse({k for k in analysis if k == "difference" or k.startswith("ci")})
        result = stages.outcome(self.data, self.out, reps=200, one_year_result=self.one_year)
        self.assertEqual(result["outcome_reading"], "crown condition")
        primary = result["primary"]
        self.assertLess(primary["ci95_bootstrap"][0], EFFECT)
        self.assertGreater(primary["ci95_bootstrap"][1], EFFECT)
        self.assertTrue(primary["test_a_gain"])
        secondary = result["secondary"]
        self.assertAlmostEqual(secondary["older_16_40"]["difference"], 0.0, delta=0.02)
        self.assertAlmostEqual(secondary["placebo_2015_2020"]["difference"], 0.0, delta=0.02)
        self.assertAlmostEqual(secondary["s3_sustained"]["difference"], EFFECT, delta=0.02)
        self.assertAlmostEqual(secondary["s3_occasional"]["difference"], EFFECT / 3, delta=0.02)
        self.assertAlmostEqual(secondary["s12_minus_background_ring"]["difference"], EFFECT, delta=0.02)
        self.assertAlmostEqual(secondary["s13_stable_surface_covariate"]["difference"], EFFECT, delta=0.02)
        self.assertAlmostEqual(secondary["s10_canopy_fraction"]["difference"], 0.0, delta=0.02)
        self.assertTrue(secondary["s16_2020_2023_green_share"]["treated"] > 0)
        bounds = result["s17_survivor_bounds"]
        self.assertEqual(len(bounds["grid"]), 6)
        self.assertLessEqual(bounds["widest_ci95"][0], primary["ci95_bootstrap"][0] + 1e-3)
        self.assertEqual(result["s18_without_survivor_selection"][:6], "awaits")

    def test_validity_failure_changes_the_reading(self):
        stages.check(self.data, self.out)
        rng = np.random.default_rng(5)
        planned = stages.design(self.data, self.out, removed_of=lambda ids: rng.random(len(ids)) < 0.04)
        self.assertFalse(planned["validity"]["passes"])
        result = stages.outcome(self.data, self.out, reps=50, one_year_result=self.one_year)
        self.assertTrue(result["outcome_reading"].startswith("crown greenness only"))

    def test_validity_ignores_watering(self):
        trees = stages.tree_table(self.data)
        shuffled = trees.copy()
        care = ["dose", "watered", "never", "watered_before_baseline", "occasional", "repeated", "sustained", "dry_2022", "high_dose"]
        shuffled[care] = shuffled[care].sample(frac=1.0, random_state=1).to_numpy()
        self.assertEqual(stages.validity(trees, self.removed_of), stages.validity(shuffled, self.removed_of))

    def test_eye_check_failure_stops_the_design(self):
        eye = pd.read_csv(self.data / "eye_check.csv")
        eye.loc[:30, "on_tree"] = "no"
        eye.to_csv(self.data / "eye_check.csv", index=False)
        self.assertFalse(stages.check(self.data, self.out)["passes"])
        with self.assertRaises(SystemExit):
            stages.design(self.data, self.out, removed_of=self.removed_of)

    def test_outcome_refuses_a_sample_that_differs_from_the_design(self):
        stages.check(self.data, self.out)
        stages.design(self.data, self.out, removed_of=self.removed_of)
        planned = json.loads((self.out / "design.json").read_text())
        planned["analyses"]["primary"]["by_level"]["sustained"] += 1
        (self.out / "design.json").write_text(json.dumps(planned))
        with self.assertRaises(SystemExit):
            stages.outcome(self.data, self.out, reps=20, one_year_result=self.one_year)

    def test_missing_inventory_stops_the_design(self):
        stages.check(self.data, self.out)
        with self.assertRaises(SystemExit):
            stages.design(self.data, self.out, inventory=Path(self.folder.name) / "absent.gpkg")


if __name__ == "__main__":
    unittest.main()
