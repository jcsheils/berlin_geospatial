import hashlib
import io
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from PIL import Image

from analysis import rq3_crown_health_extract as extract


def png(array: np.ndarray, mode: str = "RGB") -> bytes:
    buffer = io.BytesIO()
    image = Image.fromarray(array.astype(np.uint8), "RGB")
    (image.convert("P") if mode == "P" else image).save(buffer, format="PNG")
    return buffer.getvalue()


def trees(rows):
    """rows: (tree_id, x, y)."""
    return pd.DataFrame([(t, 2010, x, y) for t, x, y in rows], columns=["tree_id", "planting_year", "x", "y"])


class FakeClient:
    """Serves a constant colour-infrared image (near-infrared 200, red 50, green 80) of the requested size."""

    def __init__(self, bands=(200, 50, 80)):
        self.bands = bands
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        width, height = int(query["WIDTH"][0]), int(query["HEIGHT"][0])
        return png(np.broadcast_to(np.array(self.bands), (height, width, 3)))


def brute_force_count(window, x, y, radius):
    count = 0
    for r in range(window.height):
        for c in range(window.width):
            px = (window.ix0 + c + 0.5) * extract.PIXEL_M
            py = (window.iy1 - r - 0.5) * extract.PIXEL_M
            count += (px - x) ** 2 + (py - y) ** 2 <= radius ** 2 + extract.EDGE_M2
    return count


class WindowTests(unittest.TestCase):
    def test_windows_hold_every_circle_on_the_pixel_grid(self):
        rng = np.random.default_rng(1)
        frame = trees([(f"t{i}", 390000 + rng.uniform(0, 400), 5810000 + rng.uniform(0, 400)) for i in range(300)])
        cells, membership = extract.windows(frame)
        self.assertEqual(int(cells["trees"].sum()), len(frame))
        for tree, key in zip(frame.itertuples(), membership):
            cell = cells.loc[key]
            self.assertLessEqual(cell.ix0 * extract.PIXEL_M, tree.x - 3 + 1e-9)
            self.assertGreaterEqual(cell.ix1 * extract.PIXEL_M, tree.x + 3 - 1e-9)
            self.assertLessEqual(cell.iy0 * extract.PIXEL_M, tree.y - 3 + 1e-9)
            self.assertGreaterEqual(cell.iy1 * extract.PIXEL_M, tree.y + 3 - 1e-9)
        self.assertTrue((cells["width"] <= (extract.CELL_M + 6) / extract.PIXEL_M + 1).all())

    def test_shards_split_the_windows_once(self):
        frame = trees([(f"t{i}", 390000 + 60 * i, 5810000.0) for i in range(20)])
        cells, _ = extract.windows(frame)
        parts = [cells.iloc[s::6].index for s in range(6)]
        self.assertEqual(sorted(i for part in parts for i in part), sorted(cells.index))

    def test_request_url_snaps_to_the_grid(self):
        window = pd.DataFrame({"ix0": [1973093], "iy0": [29050000], "ix1": [1973124], "iy1": [29050031],
                               "width": [31], "height": [31]}).iloc[0]
        query = urllib.parse.parse_qs(urllib.parse.urlparse(extract.getmap_url("truedop_2025_sommer", "truedop_2025_sommer_cir", window)).query)
        self.assertEqual(query["BBOX"][0], "394618.6,5810000.0,394624.8,5810006.2")
        self.assertEqual((query["WIDTH"][0], query["HEIGHT"][0], query["FORMAT"][0]), ("31", "31", "image/png"))
        self.assertEqual(query["SRS"][0], "EPSG:25833")


class CircleTests(unittest.TestCase):
    def setUp(self):
        # "inside" sits on a pixel centre, so whole-pixel radii pass through pixel centres
        self.frame = trees([("inside", 390010.3, 5810010.7), ("edge", 390020.0, 5810010.0), ("off", 390004.37, 5810013.18)])
        cells, _ = extract.windows(self.frame, cell=100.0)
        self.window = next(cells.itertuples())
        bands = np.zeros((self.window.height, self.window.width, 3))
        bands[:, :, 0], bands[:, :, 1], bands[:, :, 2] = 200, 50, 80
        edge_col = int(round(390020.0 / extract.PIXEL_M)) - self.window.ix0
        bands[:, edge_col:, :] = 0  # east of the second tree lies outside the image
        self.bands = bands.astype(np.uint8)

    def test_counts_and_ndvi_inside_the_image(self):
        stats = extract.circle_stats(self.bands, self.window, self.frame, "ndvi").set_index("tree_id")
        for tree, x, y in (("inside", 390010.3, 5810010.7), ("off", 390004.37, 5810013.18)):
            for radius in extract.RADII_M:
                label = f"{radius:g}m"
                expected = brute_force_count(self.window, x, y, radius)
                self.assertEqual(stats.loc[tree, f"pixels_{label}"], expected)
                self.assertEqual(stats.loc[tree, f"in_image_{label}"], expected)
                self.assertAlmostEqual(stats.loc[tree, f"ndvi_{label}"], 150 / 250)
        self.assertAlmostEqual(stats.loc["inside", "pixels_2m"], np.pi * 100, delta=15)

    def test_pixels_outside_the_image_are_left_out(self):
        stats = extract.circle_stats(self.bands, self.window, self.frame, "ndvi").set_index("tree_id")
        self.assertLess(stats.loc["edge", "in_image_2m"], 0.6 * stats.loc["edge", "pixels_2m"])
        self.assertAlmostEqual(stats.loc["edge", "ndvi_2m"], 0.6)

    def test_green_share_for_colour_images(self):
        stats = extract.circle_stats(self.bands, self.window, self.frame, "gcc").set_index("tree_id")
        self.assertAlmostEqual(stats.loc["inside", "gcc_2m"], 50 / 330)


class DecodeTests(unittest.TestCase):
    def test_full_colour_png_of_the_requested_size(self):
        array = np.full((4, 5, 3), 7, dtype=np.uint8)
        self.assertEqual(extract.decode(png(array), 5, 4).shape, (4, 5, 3))

    def test_palette_or_wrong_size_is_refused(self):
        array = np.full((4, 5, 3), 7, dtype=np.uint8)
        with self.assertRaises(ValueError):
            extract.decode(png(array, mode="P"), 5, 4)
        with self.assertRaises(ValueError):
            extract.decode(png(array), 4, 5)


class FreezeTests(unittest.TestCase):
    def test_freeze_guard(self):
        protocol = b"plan text\n"
        good = f'[project.rq3_crown_health]\nprotocol_sha256 = "{hashlib.sha256(protocol).hexdigest()}"\n'
        self.assertTrue(extract.frozen(good, protocol))
        self.assertFalse(extract.frozen(good, protocol + b"changed"))
        self.assertFalse(extract.frozen("[project.rq3_crown_health]\n", protocol))

    def test_commands_refuse_to_read_images_before_the_freeze(self):
        with mock.patch.object(extract, "frozen", return_value=False), tempfile.TemporaryDirectory() as folder:
            client = FakeClient()
            with self.assertRaises(SystemExit):
                extract.run("2025", 0, 1, Path(folder), client=client, trees=trees([("a", 390010.0, 5810010.0)]))
            self.assertEqual(client.urls, [])


class PipelineTests(unittest.TestCase):
    def test_run_and_combine_with_a_fake_service(self):
        frame = trees([(f"t{i}", 390000 + 70 * i + 10, 5810010.0) for i in range(5)])
        with mock.patch.object(extract, "require_freeze"), tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for shard in range(2):
                extract.run("2020", shard, 2, folder / "shards", client=FakeClient(), trees=frame)
            summary = extract.combine("2020", folder / "shards", folder / "out")
            table = pd.read_csv(folder / "out/crown_circles_2020.csv.gz")
            log = pd.read_csv(folder / "out/crown_windows_2020.csv.gz", keep_default_na=False)
        self.assertEqual((summary["trees"], summary["windows"], summary["failed_windows"]), (5, 5, 0))
        self.assertEqual(sorted(table["tree_id"]), sorted(frame["tree_id"]))
        self.assertTrue(np.allclose(table["ndvi_2m"], 0.6))
        self.assertTrue((log["sha256"].str.len() == 64).all())
        self.assertFalse({"watered", "never", "litres"} & set(table.columns))

    def test_crosscheck_passes_when_layers_agree(self):
        class Layers(FakeClient):
            def get(self, url):
                self.bands = (50, 80, 60) if "_rgb" in url else (200, 50, 80)
                return super().get(url)
        frame = trees([(f"t{i}", 390000 + 70 * i + 10, 5810010.0) for i in range(3)])
        with mock.patch.object(extract, "require_freeze"), tempfile.TemporaryDirectory() as folder:
            result = extract.crosscheck("2020", Path(folder), client=Layers(), trees=frame)
        self.assertTrue(result["passes"])
        self.assertEqual((result["red_median_abs_diff"], result["green_median_abs_diff"]), (0.0, 0.0))


class WorkflowTests(unittest.TestCase):
    def test_workflow_shards_match_the_module(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        path = Path(extract.ROOT) / ".github/workflows/rq3-crown-health.yml"
        workflow = yaml.safe_load(path.read_text())
        job = workflow["jobs"]["extract"]
        self.assertEqual(job["strategy"]["matrix"]["shard"], list(range(extract.SHARDS)))
        self.assertIn(f"--shards {extract.SHARDS}", path.read_text())
        self.assertEqual(set(workflow[True]["workflow_dispatch"]["inputs"]["flight"]["options"]), set(extract.FLIGHTS))


class CohortTests(unittest.TestCase):
    def test_cohort_holds_positions_and_planting_years_only(self):
        cohort = extract.cohort()
        self.assertEqual(list(cohort.columns), ["tree_id", "planting_year", "x", "y"])
        self.assertTrue(cohort["tree_id"].str.startswith("strassenbaeume.").all())
        self.assertTrue(cohort["planting_year"].between(1980, 2019).all())
        self.assertFalse(cohort["tree_id"].duplicated().any())


if __name__ == "__main__":
    unittest.main()
