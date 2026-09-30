from __future__ import annotations

import unittest
from pathlib import Path

from fallbacklens.loaders import load_litellm_config, policy_from_data
from fallbacklens.simulate import load_scenarios, replay_scenario, replay_scenarios

ROOT = Path(__file__).resolve().parents[1]


class SimulationTests(unittest.TestCase):
    def test_demo_scenarios_match_expectations(self) -> None:
        result = replay_scenarios(
            load_litellm_config(ROOT / "examples" / "litellm-safe.yaml"),
            load_scenarios(ROOT / "examples" / "scenarios.json"),
        )
        self.assertEqual(2, result["summary"]["matched_expectation"])
        self.assertEqual("agent-local", result["results"][0]["terminal"])

    def test_cycle_replay_is_hard_bounded(self) -> None:
        policy = policy_from_data(
            {
                "model_list": [{"model_name": "a"}, {"model_name": "b"}],
                "router_settings": {"num_retries": 0, "fallbacks": [{"a": "b"}, {"b": "a"}]},
            }
        )
        scenario = {
            "name": "cycle",
            "entrypoint": "a",
            "outcomes": {"a": ["error"] * 10, "b": ["error"] * 10},
            "expected_status": "bounded_abort",
        }
        result = replay_scenario(policy, scenario, max_steps=5)
        self.assertEqual("bounded_abort", result["status"])
        self.assertEqual(5, result["attempts"])
        self.assertTrue(result["matched_expectation"])

    def test_content_policy_uses_specific_edge(self) -> None:
        policy = policy_from_data(
            {
                "model_list": [{"model_name": "a"}, {"model_name": "b"}, {"model_name": "c"}],
                "router_settings": {
                    "num_retries": 0,
                    "fallbacks": [{"a": "b"}],
                    "content_policy_fallbacks": [{"a": "c"}],
                },
            }
        )
        result = replay_scenario(
            policy,
            {"name": "policy", "entrypoint": "a", "outcomes": {"a": ["content_policy"], "c": ["success"]}, "expected_terminal": "c"},
            max_steps=5,
        )
        self.assertEqual("c", result["terminal"])


if __name__ == "__main__":
    unittest.main()
