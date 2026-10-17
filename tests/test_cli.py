from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from berlin_heat.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CommandLineTests(unittest.TestCase):
    def test_status_reports_declared_readiness(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(["--root", str(ROOT), "status"])
        text = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("00_foundation", text)
        self.assertIn("partial-ready", text)
        self.assertIn("01_cooling_loss", text)
        self.assertIn("preliminary-only", text)
        self.assertIn("blocked-planned", text)
        self.assertIn("10 core planned", text)
        self.assertIn("0 deferred extensions", text)

    def test_validate_current_repository(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(["--root", str(ROOT), "validate"])
        text = stdout.getvalue()
        self.assertEqual(result, 0, text)
        self.assertIn("Validation summary: 0 errors", text)
        self.assertIn("known_limitation", text)
        self.assertNotIn("economic_inputs", text)

    def test_invalid_root_has_controlled_error(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = main(["--root", directory, "status"])
        self.assertEqual(result, 2)
        self.assertIn("Could not locate", stderr.getvalue())

    def test_module_entrypoint(self):
        environment = os.environ.copy()
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            str(ROOT / "src")
            if not existing
            else str(ROOT / "src") + os.pathsep + existing
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "berlin_heat",
                "--root",
                str(ROOT),
                "status",
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Workstream readiness", completed.stdout)


if __name__ == "__main__":
    unittest.main()
