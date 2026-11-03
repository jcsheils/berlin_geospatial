"""Portable checks for the canonical examination artifacts, not local drafts."""
import hashlib
import json
from pathlib import Path
import unittest
from berlin_heat.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[1]

class ProposalArtifactTests(unittest.TestCase):
    def test_current_proposal_and_slides_are_frozen_pdfs(self):
        manifest = json.loads((ROOT / "examination/release_manifest.json").read_text())
        entries = {e["path"]: e for e in manifest["files"]}
        for name in ("Proposal_October_2026.pdf", "Seminar_Slides_October_2026.pdf"):
            rel = "examination/proposal/" + name
            path = ROOT / rel
            self.assertTrue(path.read_bytes().startswith(b"%PDF-"))
            with path.open("rb") as handle:
                self.assertEqual(hashlib.file_digest(handle, "sha256").hexdigest(), entries[rel]["sha256"])

    def test_frozen_examination_proposal_is_distinct_from_active_design(self):
        project = load_manifest(ROOT).project
        self.assertEqual(project["examination_proposal"], "examination/proposal/Proposal_October_2026.pdf")
        self.assertTrue((ROOT / project["examination_proposal_notes"]).is_file())
        self.assertNotEqual(project["active_proposal"], project["examination_proposal"])

    def test_active_proposal_matches_declared_hash(self):
        project = load_manifest(ROOT).project
        path = ROOT / project["active_proposal"]
        self.assertTrue(path.read_bytes().startswith(b"%PDF-"))
        with path.open("rb") as handle:
            self.assertEqual(hashlib.file_digest(handle, "sha256").hexdigest(), project["active_proposal_sha256"])

if __name__ == "__main__":
    unittest.main()
