import tempfile
import unittest
from pathlib import Path

import pandas as pd

from tools import eye_check

SHEET = "chip,tree_id,on_tree\n000.png,strassenbaeume.a,\n001.png,strassenbaeume.b,\n002.png,strassenbaeume.c,\n"


class EyeCheckTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "eye_check.csv").write_text(SHEET)

    def test_rating_changes_only_on_tree_of_that_chip(self):
        result = eye_check.rate(self.folder, "001.png", " Yes ")
        self.assertEqual(result["answers"], ["", "yes", ""])
        text = (self.folder / "eye_check.csv").read_text()
        self.assertEqual(text, SHEET.replace("001.png,strassenbaeume.b,", "001.png,strassenbaeume.b,yes"))
        # the check stage reads the sheet this way
        sheet = pd.read_csv(self.folder / "eye_check.csv", dtype=str, keep_default_na=False)
        self.assertEqual(list(sheet["on_tree"]), ["", "yes", ""])
        self.assertEqual(list(sheet["tree_id"]), ["strassenbaeume.a", "strassenbaeume.b", "strassenbaeume.c"])

    def test_answers_can_be_changed_and_cleared(self):
        eye_check.rate(self.folder, "000.png", "no")
        eye_check.rate(self.folder, "000.png", "yes")
        self.assertEqual(eye_check.rate(self.folder, "002.png", "no")["answers"], ["yes", "", "no"])
        eye_check.rate(self.folder, "000.png", "")
        self.assertEqual((self.folder / "eye_check.csv").read_text(),
                         SHEET.replace("002.png,strassenbaeume.c,", "002.png,strassenbaeume.c,no"))

    def test_bad_answers_and_unknown_chips_leave_the_sheet_alone(self):
        with self.assertRaises(ValueError):
            eye_check.rate(self.folder, "000.png", "maybe")
        with self.assertRaises(ValueError):
            eye_check.rate(self.folder, "199.png", "yes")
        self.assertEqual((self.folder / "eye_check.csv").read_text(), SHEET)
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), ["eye_check.csv"])


if __name__ == "__main__":
    unittest.main()
