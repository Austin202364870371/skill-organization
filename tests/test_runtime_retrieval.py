import tempfile
import unittest
from pathlib import Path

from agent import parse_code, parse_used_skills
from appworld_runtime import extract_scores
from retrieval_bridge import build_snapshots, load_snapshots
from utils import write_jsonl


class RuntimeRetrievalTests(unittest.TestCase):
    def test_agent_output_parsing(self):
        text = '```python\nprint("ok")\n```\nUSED_SKILLS: ["a", "outside"]'
        self.assertEqual(parse_code(text), 'print("ok")')
        self.assertEqual(parse_used_skills(text, {"a"}), ["a"])

    def test_pass_failure_fallback(self):
        tgc, sgc, success = extract_scores({"passes": [1, 2], "failures": [3]})
        self.assertAlmostEqual(tgc, 2 / 3)
        self.assertEqual(sgc, 0)
        self.assertFalse(success)

    def test_snapshot_hash_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = root / "records.jsonl"
            output = root / "snapshots.jsonl"
            write_jsonl(records, [{
                "query_id": "task", "query": "do it",
                "reranked_candidates": [
                    {"skill_id": "a", "reranker_score": 3},
                    {"skill_id": "b", "reranker_score": 2},
                ],
            }])
            build_snapshots(records, output, {"model": "frozen"}, top_k=2)
            snapshots = load_snapshots(output)
            self.assertEqual(snapshots["task"].skill_ids, ("a", "b"))


if __name__ == "__main__":
    unittest.main()

