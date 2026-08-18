import tempfile
import unittest
from pathlib import Path

from organization.graph_evidence import analyze_solution, extract_train_graph_evidence
from organization.library import parse_skill_frontmatter


class LibraryStructureTests(unittest.TestCase):
    def test_frontmatter_rejects_generic_and_nested_metadata(self):
        with self.assertRaises(ValueError):
            parse_skill_frontmatter(
                "---\nname: SKILL.md\ndescription: generic\n---\nBody"
            )
        with self.assertRaises(ValueError):
            parse_skill_frontmatter(
                "---\nname: Valid\ndescription: first\n---\n"
                "---\nname: Hidden\ndescription: second\n---\nBody"
            )

    def test_frontmatter_accepts_one_valid_block_and_body_rule(self):
        name, description = parse_skill_frontmatter(
            "---\nname: Aggregate Results\n\ndescription: Reuse results.\n---\n"
            "Body\n---\nMore body"
        )
        self.assertEqual((name, description), ("Aggregate Results", "Reuse results."))


class GroundTruthEvidenceTests(unittest.TestCase):
    def test_ast_tracks_collection_alias_into_later_api_argument(self):
        source = '''\
def _solution(main_user, apis, requester, public_data):
    items = apis.alpha.list_items()
    item_ids = set()
    for item in items:
        item_ids.add(item.id)
    for item_id in item_ids:
        apis.beta.use_item(item_id=item_id)
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "solution.py"
            path.write_text(source, encoding="utf-8")
            result = analyze_solution(path)
        apis = {item["id"]: item["api"] for item in result["occurrences"]}
        self.assertIn(
            ("alpha.list_items", "beta.use_item", "item_id"),
            {
                (
                    apis[item["source_occurrence"]],
                    apis[item["target_occurrence"]],
                    item["argument"],
                )
                for item in result["dependencies"]
            },
        )

    def test_non_train_task_list_is_rejected_before_task_files_are_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = root / "skills"
            skill_root.mkdir()
            datasets = root / "appworld" / "data" / "datasets"
            datasets.mkdir(parents=True)
            (datasets / "train.txt").write_text("trainfam_1\n", encoding="utf-8")
            dev = datasets / "dev.txt"
            dev.write_text("devfam_1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                extract_train_graph_evidence(
                    skill_root,
                    root / "appworld",
                    split_file=dev,
                )


if __name__ == "__main__":
    unittest.main()
