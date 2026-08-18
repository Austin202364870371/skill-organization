import unittest

from evaluation.metrics import METRIC_NAMES, holm_adjust, run_metrics, summarize


class GraphMetricTests(unittest.TestCase):
    def test_nine_metrics(self):
        record = {
            "condition": "Flat-PD", "success": True,
            "evaluation": {"passes": [1, 2], "failures": [3]},
            "input_tokens": 10, "output_tokens": 4,
            "execution_steps": 2, "wall_clock_time": 3, "exposed_skill_ids": ["a", "b"],
            "used_skill_ids": ["a"], "skill_load_events": [{"skill_id": "a", "status": "loaded"}],
        }
        result = run_metrics(record)
        self.assertEqual(tuple(result), METRIC_NAMES)
        self.assertEqual(result["total_tokens"], 14)
        self.assertEqual(result["skill_utilization_rate"], 0.5)
        self.assertEqual(result["success_rate"], 1)
        self.assertAlmostEqual(result["requirement_completion_rate"], 2 / 3)
        self.assertEqual(result["tgc"], 1)

    def test_sgc_requires_complete_scenarios(self):
        records = []
        for family, outcomes in (("a", [True, True, True]), ("b", [True, False, True])):
            for variant, success in enumerate(outcomes, 1):
                records.append({
                    "task_id": f"{family}_{variant}", "split": "dev", "seed": 42,
                    "condition": "No-Skill", "success": success,
                })
        result = summarize(records)
        self.assertEqual(result["tgc"]["mean"], 5 / 6)
        self.assertEqual(result["sgc"]["mean"], 0.5)

    def test_non_applicable_skill_metrics_are_missing(self):
        result = run_metrics({"condition": "No-Skill", "success": False})
        self.assertIsNone(result["skill_utilization_rate"])
        self.assertIsNone(result["unique_skills_loaded"])

    def test_holm_adjustment(self):
        adjusted = holm_adjust([0.01, 0.04, 0.03])
        self.assertEqual(len(adjusted), 3)
        self.assertTrue(all(0 <= value <= 1 for value in adjusted))


if __name__ == "__main__":
    unittest.main()
