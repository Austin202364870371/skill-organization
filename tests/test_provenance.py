import tempfile
import unittest
from pathlib import Path

from retrieval.bridge import create_freeze_manifest, verify_freeze_manifest


class ProvenanceTests(unittest.TestCase):
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
