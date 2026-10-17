from pathlib import Path
import unicodedata
import unittest

from berlin_heat.manifest import load_manifest
from berlin_heat.paths import resolve_project_path


ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(ROOT)

    def test_declares_all_workstreams(self):
        self.assertEqual(
            set(self.manifest.pillars),
            {
                "00_foundation",
                "01_cooling_loss",
                "02_civic_heat_response",
                "03_allocation_comparison",
                "99_synthesis",
            },
        )

    def test_readiness_is_honest(self):
        statuses = {
            pillar_id: pillar.status
            for pillar_id, pillar in self.manifest.pillars.items()
        }
        self.assertEqual(statuses["00_foundation"], "partial-ready")
        self.assertEqual(
            statuses["01_cooling_loss"],
            "preliminary-only",
        )
        self.assertEqual(
            statuses["02_civic_heat_response"],
            "preliminary-only",
        )
        self.assertEqual(
            statuses["03_allocation_comparison"], "blocked-planned"
        )
        self.assertEqual(statuses["99_synthesis"], "blocked-planned")

    def test_scope_matches_october_seminar_proposal(self):
        self.assertEqual(self.manifest.project["scope_version"], "october-2026-seminar-proposal")
        self.assertEqual(self.manifest.project["core_study"], "02_civic_heat_response")
        self.assertTrue((ROOT / self.manifest.project["proposal"]).is_file())

    def test_old_cooling_gate_is_not_active(self):
        self.assertNotIn("part_ii_gate", self.manifest.project)
        triggers = self.manifest.project["schedule_triggers"]
        self.assertEqual(triggers["satellite_watering_effect"], "not-attempted-in-october-scope")
        self.assertEqual(triggers["part_iii_checkpoint"], "end-month-4")
        self.assertIn("Descriptive", triggers["part_iii_fallback"])

    def test_all_pillar_dependencies_are_declared(self):
        declared = set(self.manifest.datasets)
        for pillar in self.manifest.pillars.values():
            with self.subTest(pillar=pillar.pillar_id):
                self.assertTrue(set(pillar.datasets).issubset(declared))

    def test_current_manifest_paths_are_relative_and_contained(self):
        for spec in self.manifest.datasets.values():
            if not spec.path:
                continue
            with self.subTest(dataset=spec.dataset_id):
                self.assertFalse(Path(spec.path).is_absolute())
                resolved = resolve_project_path(self.manifest.root, spec.path)
                resolved.relative_to(self.manifest.root)

    def test_new_platform_terminology_is_explicit(self):
        recorded = self.manifest.datasets["recorded_watering_events"]
        self.assertEqual(recorded.grain, "recorded_watering_event")
        self.assertTrue(unicodedata.is_normalized("NFC", recorded.path or ""))
        self.assertIn(
            "recorded_watering",
            self.manifest.datasets[
                "lor_recorded_watering_metrics_current"
            ].dataset_id,
        )


if __name__ == "__main__":
    unittest.main()
