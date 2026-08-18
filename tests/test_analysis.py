import tempfile
import unittest
from pathlib import Path

from common.utils import write_json
from reporting.analysis import analyze_runs


class AnalysisTests(unittest.TestCase):
    def test_paired_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for condition, tokens in (("Flat-NoPD", 20), ("Flat-PD", 10)):
                record = {
                    "split": "dev", "task_id": "task", "seed": 42, "condition": condition,
                    "success": True, "input_tokens": tokens,
                    "output_tokens": 0, "execution_steps": 2, "wall_clock_time": 1,
                    "exposed_skill_ids": ["a"], "used_skill_ids": ["a"], "skill_load_events": [],
                }
                write_json(root / condition / "record.json", record)
            result = analyze_runs(root, bootstrap_samples=100)
            comparison = result["comparisons"]["dev"][0]
            self.assertEqual(comparison["metrics"]["total_tokens"]["difference"], -10)


if __name__ == "__main__":
    unittest.main()
