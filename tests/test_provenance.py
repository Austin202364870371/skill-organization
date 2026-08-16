import tempfile
import unittest
from pathlib import Path

from retrieval_bridge import create_freeze_manifest, verify_freeze_manifest
from corpus import _sanitize_path, build_family_split
from skill_generation import leakage_findings
from utils import require_generation_split


class ProvenanceTests(unittest.TestCase):
    def test_test_split_is_forbidden(self):
        with self.assertRaises(ValueError):
            require_generation_split("test_normal")

    def test_leakage_patterns(self):
        self.assertIn("email", leakage_findings("write to person@example.com"))
        self.assertIn("date", leakage_findings("on 2026-08-15"))

    def test_family_split_is_stable_and_complete(self):
        task_ids = [f"family_{family}_{variant}" for family in range(30) for variant in (1, 2, 3)]
        split = build_family_split(list(reversed(task_ids)))
        self.assertEqual(len(split["families"]), 30)
        self.assertEqual(split["families"][0]["generation_task"], "family_0_1")
        self.assertEqual(split["families"][0]["refinement_task"], "family_0_2")
        self.assertEqual(split["families"][0]["acceptance_task"], "family_0_3")
        self.assertEqual(split, build_family_split(list(reversed(task_ids))))

    def test_reference_paths_hide_dynamic_ids(self):
        self.assertEqual(
            _sanitize_path("/venmo/transactions/8230/likes?debug=true"),
            "/venmo/transactions/{id}/likes",
        )
        self.assertEqual(
            _sanitize_path("/items/550e8400-e29b-41d4-a716-446655440000"),
            "/items/{uuid}",
        )

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
