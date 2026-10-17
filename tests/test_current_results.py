import csv
from pathlib import Path
import sqlite3
import unittest

from berlin_heat.manifest import load_manifest
from berlin_heat.paths import resolve_project_path


ROOT = Path(__file__).resolve().parents[1]


def read_metric_table(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["metric"]: row["value"]
            for row in csv.DictReader(handle)
        }


def gpkg_connection(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


class CurrentResultParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(ROOT)

    def dataset_path(self, dataset_id: str) -> Path:
        spec = self.manifest.datasets[dataset_id]
        self.assertIsNotNone(spec.path)
        return resolve_project_path(ROOT, spec.path or "")

    def test_recorded_watering_snapshot_parity(self):
        path = self.dataset_path("recorded_watering_events")
        spec = self.manifest.datasets["recorded_watering_events"]
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=spec.delimiter)
            header = next(reader)
            rows = [tuple(row) for row in reader]

        id_index = header.index("id")
        self.assertEqual(len(rows), 58847)
        self.assertEqual(len(rows) - len(set(rows)), 111)
        self.assertEqual(len({row[id_index] for row in rows}), 11278)

    def test_lor_boundary_contract_parity(self):
        path = self.dataset_path("lor_boundaries_2021")
        with gpkg_connection(path) as connection:
            count = connection.execute(
                'SELECT COUNT(*) FROM "a_lor_plr_2021"'
            ).fetchone()[0]
            srs_id = connection.execute(
                "SELECT srs_id FROM gpkg_contents "
                "WHERE table_name = 'a_lor_plr_2021'"
            ).fetchone()[0]
        self.assertEqual(count, 542)
        self.assertEqual(srs_id, 25833)

    def test_tree_linkage_and_spatial_assignment_parity(self):
        matches = read_metric_table(
            ROOT / "output/exploratory/tables/tree_id_match_summary.csv"
        )
        assignment = read_metric_table(
            ROOT / "output/spatial/tables/spatial_join_audit.csv"
        )
        self.assertEqual(int(float(matches["Matched cadastre IDs"])), 11160)
        self.assertAlmostEqual(
            float(matches["Match rate"]), 0.989537151977301, places=12
        )
        self.assertEqual(
            int(float(assignment["Trees assigned to a Planungsraum"])),
            955434,
        )
        self.assertAlmostEqual(
            float(assignment["Assignment rate"]),
            0.9990453255983446,
            places=12,
        )

    def test_current_spatial_result_parity(self):
        moran = read_metric_table(
            ROOT / "output/spatial/tables/global_moran_watering_reach.csv"
        )
        self.assertAlmostEqual(
            float(moran["Moran's I"]), 0.4405453105454913, places=12
        )
        self.assertEqual(float(moran["Permutation p-value"]), 0.001)
        self.assertEqual(int(float(moran["Permutations"])), 999)

        path = self.dataset_path("lor_recorded_watering_metrics_current")
        with gpkg_connection(path) as connection:
            count = connection.execute(
                'SELECT COUNT(*) FROM "lor_watering_metrics"'
            ).fetchone()[0]
        self.assertEqual(count, 542)

    def test_optional_local_tree_inventory_parity(self):
        path = self.dataset_path("tree_inventory")
        if not path.is_file():
            self.skipTest("The ignored local tree inventory is not installed.")
        with gpkg_connection(path) as connection:
            count = connection.execute(
                'SELECT COUNT(*) FROM "Berlin_trees"'
            ).fetchone()[0]
            srs_id = connection.execute(
                "SELECT srs_id FROM gpkg_contents "
                "WHERE table_name = 'Berlin_trees'"
            ).fetchone()[0]
        self.assertEqual(count, 962545)
        self.assertEqual(srs_id, 4326)

    def test_optional_current_equity_result_parity(self):
        table = ROOT / "output/equity/tables/lor_watering_equity_metrics.csv"
        if not table.is_file():
            self.skipTest("The current-worktree equity result is not available.")
        with table.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 535)

        path = self.dataset_path("lor_recorded_watering_equity_current")
        with gpkg_connection(path) as connection:
            count = connection.execute(
                'SELECT COUNT(*) FROM "lor_watering_equity"'
            ).fetchone()[0]
        self.assertEqual(count, 542)


if __name__ == "__main__":
    unittest.main()
