import tempfile
import unittest
from pathlib import Path

from agent import parse_code, parse_used_skills
from appworld_runtime import extract_scores
from official_agent import COMPLETION_RULE
from retrieval_bridge import build_snapshots, load_snapshots
from utils import write_jsonl


class RuntimeRetrievalTests(unittest.TestCase):
    def test_completion_rule_distinguishes_action_and_answer_tasks(self):
        self.assertIn("complete_task()` without an answer", COMPLETION_RULE)
        self.assertIn("only when the task explicitly asks", COMPLETION_RULE)

    def test_agent_output_parsing(self):
        text = '```python\nprint("ok")\n```\nUSED_SKILLS: ["a", "outside"]'
        self.assertEqual(parse_code(text), 'print("ok")')
        self.assertEqual(parse_used_skills(text, {"a"}), ["a"])

    def test_fenced_skill_markdown(self):
        from skill_generation import parse_skill_markdown
        text = "```markdown\n---\nname: Search Songs\ndescription: Find songs generically.\n---\n\n## When to Use\nUse for song search.\n```"
        skill = parse_skill_markdown("search-songs", text)
        self.assertEqual(skill.name, "Search Songs")
        self.assertTrue(skill.body.startswith("---"))

    def test_title_frontmatter_is_normalized(self):
        from skill_generation import parse_skill_markdown
        text = "---\ntitle: Search Songs\n---\n\n## When to Use\n\nFind songs by an artist.\n\n## Preconditions\n\nAPI access.\n"
        skill = parse_skill_markdown("search-songs", text)
        self.assertEqual(skill.name, "Search Songs")
        self.assertEqual(skill.description, "Find songs by an artist.")
        self.assertIn("description: Find songs by an artist.", skill.body)

    def test_markdown_title_and_description_are_normalized(self):
        from skill_generation import parse_skill_markdown
        text = "# Search Songs\n\n## Description\nFind songs generically.\n\n## When to Use\nUse for song search.\n"
        skill = parse_skill_markdown("search-songs", text)
        self.assertEqual(skill.name, "Search Songs")
        self.assertEqual(skill.description, "Find songs generically.")
        self.assertTrue(skill.body.startswith("---\nname: Search Songs\n"))

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
                    {"skill_id": "b", "reranker_score": 2},
                ],
            }])
            build_snapshots(records, output, {"model": "frozen"}, top_k=2)
            snapshots = load_snapshots(output)
            self.assertEqual(snapshots["task"].skill_ids, ("a", "b"))


if __name__ == "__main__":
    unittest.main()
