import unittest

from organizers import assert_fair_views, build_view
from schemas import Candidate, Skill, Snapshot
from skill_loader import SkillLoader


class OrganizationTests(unittest.TestCase):
    def setUp(self):
        self.library = {
            "a": Skill("a", "A", "first", "Do A"),
            "b": Skill("b", "B", "second", "Do B"),
        }
        self.snapshot = Snapshot("task", "query", (Candidate("a", 1, 2.0), Candidate("b", 2, 1.0)))
        self.hierarchy = {"paths": {"a": ["D", "App", "CapA"], "b": ["D", "App", "CapB"]}}
        self.graph = {"nodes": ["a", "b"], "edges": [{
            "source": "a", "target": "b", "relation": "dependency", "evidence": "a output feeds b",
            "confidence": 1.0, "method": "test",
        }]}

    def test_all_skill_views_preserve_order_and_hash(self):
        views = [
            build_view(condition, self.snapshot, self.library, self.hierarchy, self.graph)
            for condition in ("Flat-NoPD", "Flat-PD", "Hierarchy-PD", "Graph-PD")
        ]
        assert_fair_views(views)
        self.assertTrue(all(view.allowed_skill_ids == ("a", "b") for view in views))

    def test_no_skill_isolated(self):
        view = build_view("No-Skill", self.snapshot, self.library)
        self.assertEqual(view.initial_context, "")
        self.assertEqual(view.allowed_skill_ids, ())

    def test_loader_is_bounded_and_idempotent(self):
        view = build_view("Flat-PD", self.snapshot, self.library)
        loader = SkillLoader(view, self.library)
        self.assertIn("Do A", loader.load("a", 1))
        self.assertIn("already loaded", loader.load("a", 2))
        self.assertIn("unavailable", loader.load("outside", 3))
        self.assertEqual(loader.loaded, {"a"})


if __name__ == "__main__":
    unittest.main()

