import tempfile
import unittest
from pathlib import Path

from retrieval_bridge import create_freeze_manifest, verify_freeze_manifest
from skill_generation import leakage_findings
from utils import require_generation_split


class ProvenanceTests(unittest.TestCase):
    def test_test_split_is_forbidden(self):
        with self.assertRaises(ValueError):
            require_generation_split("test_normal")

    def test_leakage_patterns(self):
        self.assertIn("email", leakage_findings("write to person@example.com"))
        self.assertIn("date", leakage_findings("on 2026-08-15"))

    def test_freeze_detects_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "artifact.json"
            artifact.write_text("{}", encoding="utf-8")
            manifest = root / "freeze.json"
            create_freeze_manifest({"artifact": artifact}, {"model": "local"}, manifest)
            verify_freeze_manifest(manifest)
            artifact.write_text('{"changed":true}', encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_freeze_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
