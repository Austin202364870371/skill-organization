import json
import tempfile
import unittest
from pathlib import Path

from common.schemas import Candidate, Skill, Snapshot
from organization.graph_builder import build_global_graph, validate_global_graph
from organization.graph_runtime import build_task_dag
from organization.hierarchy import build_hierarchy
from organization.organizers import assert_fair_views, build_view


def make_skill(root, skill_id, metadata=None, api_patterns=None, valid_md=True):
    directory = root / skill_id
    (directory / "references").mkdir(parents=True)
    body = (
        f"---\nname: {skill_id}-name\ndescription: test\n---\nBody {skill_id}"
        if valid_md
        else f"Body {skill_id}"
    )
    (directory / "SKILL.md").write_text(body, encoding="utf-8")
    if metadata == "malformed":
        (directory / "metadata.json").write_text("{", encoding="utf-8")
    elif metadata is not None:
        (directory / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )
    if api_patterns is not None:
        (directory / "references" / "api_patterns.json").write_text(
            json.dumps(api_patterns), encoding="utf-8"
        )


class HierarchyTests(unittest.TestCase):
    def test_type_apps_fallback_and_supervisor_exclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(root, "core", {
                "required_apps": ["supervisor", "", "zeta", "amazon"],
            })
            make_skill(root, "shared", {
                "candidate_type": "reusable_subskill",
                "supporting_apis": ["supervisor.complete_task", "spotify.search"],
            })
            result = build_hierarchy(["shared", "core", "shared"], root)
            self.assertEqual(result["retrieved_skill_ids"], ["shared", "core"])
            self.assertEqual(result["hierarchy"]["Core"]["amazon"], ["core"])
            self.assertEqual(result["hierarchy"]["Shared"]["spotify"], ["shared"])

    def test_malformed_metadata_and_name_fallback_do_not_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(root, "broken", "malformed", valid_md=False)
            result = build_hierarchy(["broken", "unknown"], root)
            self.assertEqual(result["hierarchy"]["Core"]["General"], ["broken"])
            self.assertEqual(result["names"]["broken"], "broken")
            self.assertIn("unknown skill_id: unknown", result["warnings"])


class GraphBuildTests(unittest.TestCase):
    def test_global_graph_validation_allows_cycles(self):
        validate_global_graph({
            "nodes": [{"id": "a"}, {"id": "b"}],
            "edges": [
                {"source": "a", "target": "b", "type": "PRECEDES", "confidence": 1, "support": 2},
                {"source": "b", "target": "a", "type": "DATA_DEP", "confidence": 1, "support": 1},
            ],
        })

    def test_support_is_shared_to_core_and_requires_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(
                root,
                "core",
                {"family_id": "family-1"},
                {"required_apis": ["spotify.search", "spotify.add"]},
            )
            make_skill(root, "unrelated", {"family_id": "family-2"})
            make_skill(root, "shared", {
                "candidate_type": "reusable_subskill",
                "supporting_family_ids": ["family-1"],
                "supporting_apis": ["spotify.search"],
            })
            graph = build_global_graph(root)
            validate_global_graph(graph)
            edges = graph["edges"]
            self.assertEqual(len(edges), 1)
            self.assertEqual(
                (edges[0]["source"], edges[0]["target"], edges[0]["type"]),
                ("shared", "core", "SUPPORTS"),
            )

    def test_support_accepts_shared_source_task_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(
                root,
                "core",
                {"generation_task": "train-task"},
                {"required_apis": ["spotify.search"]},
            )
            make_skill(root, "shared", {
                "candidate_type": "reusable_subskill",
                "generation_task": "train-task",
                "supporting_apis": ["spotify.search"],
            })
            graph = build_global_graph(root)
            self.assertEqual(
                [(edge["source"], edge["target"]) for edge in graph["edges"]],
                [("shared", "core")],
            )

    def test_support_accepts_explicit_api_subsequence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(
                root,
                "core",
                {},
                {"api_sequences": [["a.start", "a.middle", "a.finish"]]},
            )
            make_skill(
                root,
                "shared",
                {"candidate_type": "reusable_subskill"},
                {"api_sequences": [["a.start", "a.finish"]]},
            )
            graph = build_global_graph(root)
            self.assertEqual(
                [(edge["source"], edge["target"], edge["type"]) for edge in graph["edges"]],
                [("shared", "core", "SUPPORTS")],
            )

    def test_data_dependency_requires_explicit_producer_consumer_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(root, "producer", {
                "data_dependencies": [{
                    "producer_skill_id": "producer",
                    "consumer_skill_id": "consumer",
                    "output": "contact_id",
                    "input": "recipient_id",
                    "support": 2,
                }],
            })
            make_skill(root, "consumer", {})
            make_skill(root, "same-app-only", {"required_apps": ["phone"]})
            graph = build_global_graph(root)
            data_edges = [edge for edge in graph["edges"] if edge["type"] == "DATA_DEP"]
            self.assertEqual(
                [(edge["source"], edge["target"], edge["support"]) for edge in data_edges],
                [("producer", "consumer", 2)],
            )

    def test_precedes_uses_train_threshold_and_rejects_non_train(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(root, "a", {})
            make_skill(root, "b", {})
            graph = build_global_graph(
                root,
                trajectory_orders=[
                    {"split": "train", "successful": True, "skill_ids": ["a", "b"]},
                    {"split": "train", "successful": True, "skill_ids": ["a", "b"]},
                ],
            )
            edge = next(edge for edge in graph["edges"] if edge["type"] == "PRECEDES")
            self.assertEqual((edge["source"], edge["target"], edge["support"]), ("a", "b", 2))
            with self.assertRaises(ValueError):
                build_global_graph(
                    root,
                    trajectory_orders=[{"split": "dev", "skill_ids": ["a", "b"]}],
                )
            with self.assertRaises(ValueError):
                build_global_graph(
                    root,
                    trajectory_orders=[{"split": "train", "skill_ids": ["a", "b"]}],
                )

    def test_non_train_skill_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(root, "leaked", {"source_split": "test_normal"})
            with self.assertRaises(ValueError):
                build_global_graph(root)

    def test_malformed_metadata_does_not_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_skill(root, "broken", "malformed")
            graph = build_global_graph(root)
            self.assertEqual([node["id"] for node in graph["nodes"]], ["broken"])
            self.assertTrue(graph["warnings"])


class GraphRuntimeTests(unittest.TestCase):
    def test_induced_graph_cycle_resolution_and_isolated_node(self):
        graph = {
            "edges": [
                {"source": "a", "target": "b", "type": "PRECEDES", "confidence": 1, "support": 5},
                {"source": "b", "target": "c", "type": "SUPPORTS", "confidence": 1, "support": 2},
                {"source": "c", "target": "a", "type": "DATA_DEP", "confidence": 1, "support": 1},
                {"source": "a", "target": "outside", "type": "DATA_DEP", "confidence": 1, "support": 9},
                {"source": "d", "target": "d", "type": "PRECEDES", "confidence": 1, "support": 1},
            ]
        }
        first = build_task_dag(["a", "b", "c", "d", "a"], graph)
        second = build_task_dag(["a", "b", "c", "d", "a"], graph)
        self.assertEqual(first, second)
        self.assertEqual(first["nodes"], ["a", "b", "c", "d"])
        self.assertTrue(all(edge["target"] != "outside" for edge in first["edges"]))
        self.assertFalse(any(edge["source"] == "d" for edge in first["edges"]))
        self.assertEqual(
            {(edge["source"], edge["target"]) for edge in first["edges"]},
            {("b", "c"), ("c", "a")},
        )
        self.assertEqual(
            {(edge["source"], edge["target"], edge["reason"]) for edge in first["dropped_edges"]},
            {("a", "b", "cycle"), ("d", "d", "self_loop")},
        )

    def test_empty_edges_preserve_every_node(self):
        dag = build_task_dag(["a", "b", "c"], {"edges": []})
        self.assertEqual(dag["nodes"], ["a", "b", "c"])
        self.assertEqual(dag["edges"], [])
        self.assertEqual(dag["topological_layers"], [["a", "b", "c"]])

    def test_same_type_cycle_prefers_confidence_then_support(self):
        graph = {"edges": [
            {"source": "a", "target": "b", "type": "PRECEDES", "confidence": 0.9, "support": 2},
            {"source": "b", "target": "c", "type": "PRECEDES", "confidence": 0.8, "support": 9},
            {"source": "c", "target": "a", "type": "PRECEDES", "confidence": 0.7, "support": 20},
        ]}
        dag = build_task_dag(["a", "b", "c"], graph)
        self.assertEqual(
            [(edge["source"], edge["target"]) for edge in dag["edges"]],
            [("a", "b"), ("b", "c")],
        )
        self.assertEqual(
            [(edge["source"], edge["target"], edge["reason"]) for edge in dag["dropped_edges"]],
            [("c", "a", "cycle")],
        )

    def test_graph_condition_never_adds_a_skill(self):
        library = {
            skill_id: Skill(skill_id, skill_id.upper(), "desc", f"Body {skill_id}")
            for skill_id in ("a", "b")
        }
        snapshot = Snapshot(
            "task",
            "query",
            (Candidate("a", 1, 1.0), Candidate("b", 2, 0.9)),
        )
        graph = {
            "edges": [
                {"source": "a", "target": "b", "type": "SUPPORTS", "confidence": 1, "support": 1},
                {"source": "outside", "target": "a", "type": "DATA_DEP", "confidence": 1, "support": 1},
            ]
        }
        hierarchy = {
            "hierarchy": {"Core": {"General": ["a", "b"]}, "Shared": {}},
            "names": {},
        }
        views = [
            build_view(condition, snapshot, library, hierarchy, graph)
            for condition in ("Flat-NoPD", "Flat-PD", "Hierarchy-PD", "Graph-PD")
        ]
        assert_fair_views(views)
        self.assertTrue(all(view.allowed_skill_ids == ("a", "b") for view in views))
        self.assertEqual(views[-1].structure["retrieved_skill_ids"], ["a", "b"])
        self.assertNotIn("outside", views[-1].initial_context)

    def test_unknown_retrieved_skill_warns_without_crashing(self):
        library = {"a": Skill("a", "A", "desc", "Body a")}
        snapshot = Snapshot(
            "task",
            "query",
            (Candidate("a", 1, 1.0), Candidate("unknown", 2, 0.5)),
        )
        view = build_view(
            "Graph-PD",
            snapshot,
            library,
            graph={"nodes": [{"id": "a"}], "edges": []},
        )
        self.assertEqual(view.allowed_skill_ids, ("a", "unknown"))
        self.assertTrue(any("unknown" in warning for warning in view.structure["warnings"]))


if __name__ == "__main__":
    unittest.main()
