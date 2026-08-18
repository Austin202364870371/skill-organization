import tempfile
import unittest
from pathlib import Path

from common.schemas import OrganizationView
from common.utils import write_jsonl
from retrieval.bridge import build_snapshots, load_snapshots
from runtime.agent import parse_code, parse_used_skills
from runtime.appworld_runtime import extract_scores
from runtime.official_agent import COMPLETION_RULE, skill_rules_for_view


class RuntimeRetrievalTests(unittest.TestCase):
    def test_completion_rule_distinguishes_action_and_answer_tasks(self):
        self.assertIn("complete_task()` without an answer", COMPLETION_RULE)
        self.assertIn("only when the task explicitly asks", COMPLETION_RULE)

    def test_skill_rules_distinguish_all_disclosure_modes(self):
        def view(condition, loader_enabled, exposed=()):
            return OrganizationView(condition, "context", tuple(exposed), tuple(exposed), loader_enabled, {}, "hash")

        no_skill = skill_rules_for_view(view("No-Skill", False))
        flat = skill_rules_for_view(view("Flat-NoPD", False, ("skill-a",)))
        pd = skill_rules_for_view(view("Flat-PD", True, ("skill-a",)))
        self.assertIn("No skills are available", no_skill)
        self.assertIn("full instructions", flat)
        self.assertIn("Do not emit LOAD_SKILL", flat)
        self.assertNotIn("No skills are available", flat)
        self.assertIn("LOAD_SKILL <skill_id>", pd)

    def test_agent_output_parsing(self):
        text = '```python\nprint("ok")\n```\nUSED_SKILLS: ["a", "outside"]'
        self.assertEqual(parse_code(text), 'print("ok")')
        self.assertEqual(parse_used_skills(text, {"a"}), ["a"])

    def test_pass_failure_fallback(self):
        tgc, requirement_completion, success = extract_scores({"passes": [1, 2], "failures": [3]})
        self.assertEqual(tgc, 0)
        self.assertAlmostEqual(requirement_completion, 2 / 3)
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
                    {"skill_id": "a", "reranker_score": 2.5},
                    {"skill_id": "b", "reranker_score": 2},
                ],
            }])
            report = build_snapshots(records, output, {"model": "frozen"}, top_k=2)
            snapshots = load_snapshots(output)
            self.assertEqual(snapshots["task"].skill_ids, ("a", "b"))
            self.assertEqual(report["duplicates_removed"], 1)


if __name__ == "__main__":
    unittest.main()
