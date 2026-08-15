import unittest

from graph import build_candidate_graph, validate_graph
from metrics import METRIC_NAMES, holm_adjust, run_metrics
from schemas import Contract


class GraphMetricTests(unittest.TestCase):
    def test_dependency_from_contract_terms(self):
        first = Contract("a", "find", "mail", outputs=("message id",))
        second = Contract("b", "reply", "mail", inputs=("message id",))
        graph = build_candidate_graph([first, second])
        validate_graph(graph)
        self.assertEqual(graph["edges"][0]["relation"], "dependency")

    def test_eight_metrics(self):
        record = {
            "tgc": 0.5, "sgc": 1, "success": True, "input_tokens": 10, "output_tokens": 4,
            "execution_steps": 2, "wall_clock_time": 3, "exposed_skill_ids": ["a", "b"],
            "used_skill_ids": ["a"], "skill_load_events": [{"skill_id": "a", "status": "loaded"}],
        }
        result = run_metrics(record)
        self.assertEqual(tuple(result), METRIC_NAMES)
        self.assertEqual(result["total_tokens"], 14)
        self.assertEqual(result["skill_utilization_rate"], 0.5)

    def test_holm_adjustment(self):
        adjusted = holm_adjust([0.01, 0.04, 0.03])
        self.assertEqual(len(adjusted), 3)
        self.assertTrue(all(0 <= value <= 1 for value in adjusted))


if __name__ == "__main__":
    unittest.main()

