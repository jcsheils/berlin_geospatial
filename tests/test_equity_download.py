from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis import download_equity_data


class FakeFrame:
    def __init__(self, payload: str, fail: bool = False):
        self.payload = payload
        self.fail = fail

    def __len__(self):
        return 542

    def to_file(self, path, layer, driver):
        if self.fail:
            raise RuntimeError("simulated write failure")
        output = Path(path)
        prior = output.read_text() if output.exists() else ""
        output.write_text(prior + f"{layer}:{self.payload}\n")


class EquityDownloadReplacementTests(unittest.TestCase):
    def test_complete_staged_file_replaces_existing_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "equity.gpkg"
            output.write_text("old artifact")
            sources = {
                "first": ("endpoint", "feature-a"),
                "second": ("endpoint", "feature-b"),
            }
            frames = [FakeFrame("a"), FakeFrame("b")]

            with (
                patch.object(download_equity_data, "OUTPUT", output),
                patch.object(download_equity_data, "SOURCES", sources),
                patch.object(
                    download_equity_data,
                    "download_layer",
                    side_effect=frames,
                ),
            ):
                with redirect_stdout(io.StringIO()):
                    download_equity_data.main()

            self.assertEqual(output.read_text(), "first:a\nsecond:b\n")
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_failed_staging_preserves_existing_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "equity.gpkg"
            output.write_text("old artifact")
            sources = {
                "first": ("endpoint", "feature-a"),
                "second": ("endpoint", "feature-b"),
            }
            frames = [FakeFrame("a"), FakeFrame("b", fail=True)]

            with (
                patch.object(download_equity_data, "OUTPUT", output),
                patch.object(download_equity_data, "SOURCES", sources),
                patch.object(
                    download_equity_data,
                    "download_layer",
                    side_effect=frames,
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "write failure"):
                    with redirect_stdout(io.StringIO()):
                        download_equity_data.main()

            self.assertEqual(output.read_text(), "old artifact")
            self.assertEqual(list(Path(directory).iterdir()), [output])


if __name__ == "__main__":
    unittest.main()
