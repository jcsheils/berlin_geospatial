import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import crown_tables


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CrownTablesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "repo"
        self.release = base / "release"
        self.release.mkdir()
        self.files = {"crown_circles_2025.csv.gz": b"circles", "crown_windows_2025.csv.gz": b"windows"}
        for name, data in self.files.items():
            (self.release / name).write_bytes(data)
        outcome = self.root / crown_tables.OUTCOME
        outcome.parent.mkdir(parents=True)
        outcome.write_text(json.dumps({"inputs_sha256": {n: sha(d) for n, d in self.files.items()}}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_verify_accepts_matching_tables(self):
        self.assertEqual(set(crown_tables.verify(self.release, self.root)), set(self.files))

    def test_verify_names_missing_and_changed_tables(self):
        (self.release / "crown_circles_2025.csv.gz").write_bytes(b"other")
        (self.release / "crown_windows_2025.csv.gz").unlink()
        with self.assertRaisesRegex(ValueError, "changed crown_circles_2025.*missing crown_windows_2025"):
            crown_tables.verify(self.release, self.root)

    def test_sums_cover_every_file_but_themselves(self):
        (self.release / "notes.json").write_bytes(b"{}")
        crown_tables.write_sums(self.release)
        lines = crown_tables.write_sums(self.release).read_text().splitlines()
        self.assertEqual([line.split("  ")[1] for line in lines],
                         ["crown_circles_2025.csv.gz", "crown_windows_2025.csv.gz", "notes.json"])
        self.assertEqual(lines[0].split("  ")[0], sha(b"circles"))

    def test_fetch_downloads_and_checks(self):
        fetched = crown_tables.fetch(self.root, self.release.as_uri())
        self.assertEqual(len(fetched), 2)
        self.assertEqual((self.root / crown_tables.TABLES / "crown_windows_2025.csv.gz").read_bytes(), b"windows")
        self.assertEqual(crown_tables.fetch(self.root, self.release.as_uri()), [])

    def test_fetch_keeps_nothing_on_mismatch(self):
        (self.release / "crown_windows_2025.csv.gz").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "crown_windows_2025"):
            crown_tables.fetch(self.root, self.release.as_uri())
        left = sorted(p.name for p in (self.root / crown_tables.TABLES).iterdir())
        self.assertEqual(left, ["crown_circles_2025.csv.gz"])

    def test_fetch_refuses_a_differing_local_table(self):
        target = self.root / crown_tables.TABLES
        target.mkdir(parents=True)
        (target / "crown_circles_2025.csv.gz").write_bytes(b"local edit")
        with self.assertRaisesRegex(ValueError, "move it aside"):
            crown_tables.fetch(self.root, self.release.as_uri())
        self.assertEqual((target / "crown_circles_2025.csv.gz").read_bytes(), b"local edit")


if __name__ == "__main__":
    unittest.main()
